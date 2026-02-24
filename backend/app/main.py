from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .models import ErrorResponse, PersonFindRequest, PersonFindResponse
from .agent.langchain_agent import run_with_agent
from .search.service import run_person_search


settings = get_settings()
app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check() -> dict:
    return {"status": "ok"}


@app.post("/api/find-person", response_model=PersonFindResponse | ErrorResponse)
def find_person(payload: PersonFindRequest):
    if settings.enable_langchain_agent:
        return run_with_agent(payload)
    return run_person_search(payload)

