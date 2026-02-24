from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .models import PersonFindRequest, PersonFindResponse, ErrorResponse


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
    # Temporary dummy implementation – will be replaced with real pipeline.
    example_person = PersonFindResponse(
        first_name="Mark",
        last_name="Zuckerberg",
        title="Chief Executive Officer",
        company=payload.company,
        source_url="https://about.facebook.com/company-info/",
        source_label="Example static source",
        confidence=0.1,
        raw_candidates=[],
        agent_notes="Dummy response for initial wiring.",
    )
    return example_person

