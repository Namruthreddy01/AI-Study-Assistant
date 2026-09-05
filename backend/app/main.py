from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import analytics, documents, study
from app.core.config import get_settings
from app.core.errors import StudyAssistantError


settings = get_settings()
app = FastAPI(
    title="AI Study Assistant API",
    version="0.1.0",
    description="Grounded study tools for uploaded PDF material.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(StudyAssistantError)
async def study_error_handler(
    request: Request, error: StudyAssistantError
) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": str(error)})


app.include_router(documents.router)
app.include_router(study.router)
app.include_router(analytics.router)


@app.get("/health", tags=["Health"])
def health() -> dict[str, str]:
    return {"status": "ok"}
