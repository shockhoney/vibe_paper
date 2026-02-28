"""Agent 控制路由：启动写作流程、查询状态、发送反馈。"""

import asyncio
import json
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.postgres import get_db
from backend.database.models import AgentTask, Project
from backend.database.redis_client import get_redis_client
from backend.schemas.agent import AgentStartRequest, AgentFeedback, AgentTaskOut
from backend.agents.graph import get_compiled_graph
from backend.agents.state import PaperState

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/agents", tags=["agents"])


@router.post("/start")
async def start_writing(body: AgentStartRequest, db: AsyncSession = Depends(get_db)):
    """启动多智能体写作流程（异步后台执行）。"""
    project = await db.get(Project, body.project_id)
    if not project:
        raise HTTPException(404, "项目不存在")

    # 检查是否已有运行中的任务
    redis = get_redis_client()
    lock_key = f"agent:lock:{body.project_id}"
    if await redis.exists(lock_key):
        raise HTTPException(409, "该项目已有正在运行的 Agent 任务")

    # 设置锁
    await redis.set(lock_key, "running", ex=3600)

    # 创建任务记录
    task = AgentTask(
        project_id=body.project_id,
        agent_type="workflow",
        status="running",
        input_data=json.dumps({"instruction": body.instruction}, ensure_ascii=False),
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)

    # 异步启动 LangGraph 流程
    asyncio.create_task(_run_graph(body.project_id, body.instruction, task.id))

    return {"task_id": task.id, "status": "started"}


async def _run_graph(project_id: int, instruction: str, task_id: int):
    """后台运行 LangGraph 图。"""
    redis = get_redis_client()
    state_key = f"agent:state:{project_id}"
    lock_key = f"agent:lock:{project_id}"

    try:
        # 恢复或初始化状态
        saved = await redis.get(state_key)
        if saved:
            initial_state = json.loads(saved)
            initial_state["user_instruction"] = instruction
        else:
            initial_state = {
                "project_id": project_id,
                "current_agent": "",
                "messages": [],
                "outline": {},
                "sections": {},
                "references": [],
                "review_feedback": [],
                "format_issues": [],
                "iteration": 0,
                "status": "init",
                "user_instruction": instruction,
            }

        graph = get_compiled_graph()

        # 流式执行，保存中间状态到 Redis
        final_state = None
        for event in graph.stream(initial_state):
            for node_name, node_output in event.items():
                # 将进度推送到 Redis Stream
                await redis.xadd(
                    f"agent:stream:{project_id}",
                    {"agent": node_name, "data": json.dumps(node_output, ensure_ascii=False, default=str)},
                )
            final_state = event

        # 保存最终状态
        if final_state:
            # 序列化状态（排除不可序列化的 messages）
            save_state = dict(initial_state)
            save_state.update({
                "status": "done",
                "current_agent": "",
            })
            # messages 不保存到 Redis（太大）
            save_state.pop("messages", None)
            await redis.set(state_key, json.dumps(save_state, ensure_ascii=False, default=str))

    except Exception as e:
        logger.error("Graph execution failed: %s", e)
        await redis.xadd(
            f"agent:stream:{project_id}",
            {"agent": "error", "data": str(e)},
        )
    finally:
        await redis.delete(lock_key)


@router.get("/status/{project_id}")
async def get_agent_status(project_id: int):
    """获取 Agent 执行状态。"""
    redis = get_redis_client()

    lock_key = f"agent:lock:{project_id}"
    is_running = await redis.exists(lock_key)

    state_key = f"agent:state:{project_id}"
    state_raw = await redis.get(state_key)
    state = json.loads(state_raw) if state_raw else {}

    # 读取最近的 Stream 消息
    stream_key = f"agent:stream:{project_id}"
    recent = await redis.xrevrange(stream_key, count=10)
    events = []
    for msg_id, data in recent:
        events.append({"id": msg_id, **data})

    return {
        "running": bool(is_running),
        "state": state,
        "recent_events": events,
    }


@router.post("/feedback")
async def send_feedback(body: AgentFeedback):
    """用户发送反馈（存入 Redis，供 Agent 下次读取）。"""
    redis = get_redis_client()
    state_key = f"agent:state:{body.project_id}"

    state_raw = await redis.get(state_key)
    if state_raw:
        state = json.loads(state_raw)
        feedback = state.get("review_feedback", [])
        feedback.append({
            "section": str(body.target_section_id) if body.target_section_id else "",
            "comment": body.feedback,
            "source": "user",
        })
        state["review_feedback"] = feedback
        await redis.set(state_key, json.dumps(state, ensure_ascii=False))

    return {"ok": True}


@router.post("/stop/{project_id}")
async def stop_agent(project_id: int):
    """强制停止 Agent 执行。"""
    redis = get_redis_client()
    await redis.delete(f"agent:lock:{project_id}")
    return {"ok": True}
