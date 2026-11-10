from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from app.core.dependencies import require_roles
from app.core.rate_limit import limiter
from app.schemas.api import ChatRequest, ChatResponse, ErrorResponse
from app.services.gemini_service import GeminiChatService

router = APIRouter(tags=["Chat"])


@router.post(
    "/chat",
    response_model=ChatResponse,
    responses={
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
        503: {"model": ErrorResponse, "description": "Gemini unavailable"},
    },
    summary="Ask the fraud operations assistant",
)
@limiter.limit("20/minute")
async def chat(
    request: Request,
    payload: ChatRequest,
    _user=Depends(require_roles("admin", "analyst")),
) -> ChatResponse:
    service = GeminiChatService(request.app.state.settings)
    message = await service.reply(payload)
    return ChatResponse(message=message, model=request.app.state.settings.gemini_model)