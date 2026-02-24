from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .models import PersonFindRequest, PersonFindResponse, ErrorResponse
from .search.service import run_person_search


app = FastAPI(title="PersonFinderTool")

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
async def find_person(payload: PersonFindRequest):
    return run_person_search(payload)

