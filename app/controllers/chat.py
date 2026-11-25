from typing import Any

from fastapi import HTTPException
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = Field(default_factory=list)
    candidates: list[dict[str, Any]] = Field(default_factory=list)


# Xử lí yêu cầu chat và trả về câu trả lời do Qwen-Viet sinh ra.
def chat_controller(payload: ChatRequest):
    from app.services.chat_service import generate_chat_answer

    message = payload.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Nội dung câu hỏi không được để trống.")

    history = [item.model_dump() for item in payload.history]

    try:
        answer = generate_chat_answer(
            message=message,
            history=history,
            candidates=payload.candidates,
        )
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Không thể sinh câu trả lời: {error}",
        )

    if not answer:
        raise HTTPException(status_code=500, detail="Mô hình không trả về nội dung.")

    return {"answer": answer}
