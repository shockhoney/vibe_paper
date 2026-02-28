"""WebSocket 实时推送 Agent 执行进度。"""

import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.database.redis_client import get_redis_client

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/{project_id}")
async def agent_ws(websocket: WebSocket, project_id: int):
    """WebSocket 端点：订阅指定项目的 Agent 事件流。"""
    await websocket.accept()
    redis = get_redis_client()
    stream_key = f"agent:stream:{project_id}"

    # 从最新消息开始读取
    last_id = "$"

    try:
        while True:
            # 阻塞读取 Redis Stream（最长等 5 秒）
            messages = await redis.xread({stream_key: last_id}, block=5000, count=10)

            if messages:
                for stream, entries in messages:
                    for msg_id, data in entries:
                        last_id = msg_id
                        await websocket.send_json({
                            "id": msg_id,
                            "agent": data.get("agent", ""),
                            "data": data.get("data", ""),
                        })
            else:
                # 无新消息，发送心跳
                await websocket.send_json({"type": "heartbeat"})

    except WebSocketDisconnect:
        pass
    except Exception:
        await websocket.close()
