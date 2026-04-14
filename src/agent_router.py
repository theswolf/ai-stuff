from fastapi import APIRouter
from pydantic import BaseModel
from .agent_service import AgentService

router = APIRouter(prefix="/agent", tags=["Agent"])
agent = AgentService()


class AgentRequest(BaseModel):
    message: str


@router.post("/run")
async def run_agent(request: AgentRequest):
    return agent.run(request.message)
