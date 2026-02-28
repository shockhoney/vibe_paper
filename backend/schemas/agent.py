from pydantic import BaseModel
from datetime import datetime


class AgentTaskOut(BaseModel):
    id: int
    project_id: int
    agent_type: str
    status: str
    input_data: str
    output_data: str
    created_at: datetime
    model_config = {"from_attributes": True}


class AgentStartRequest(BaseModel):
    """启动 Agent 写作流程的请求。"""
    project_id: int
    instruction: str = ""  # 用户附加指令


class AgentFeedback(BaseModel):
    """用户向 Agent 发送的人工反馈。"""
    project_id: int
    feedback: str
    target_section_id: int | None = None
