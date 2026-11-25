// chatService.js
// Lớp dịch vụ gọi API chat để nhận câu trả lời từ mô hình Qwen-Viet ở backend.
import { API_BASE_URL } from "./apiConfig.js";

// Gửi câu hỏi kèm lịch sử hội thoại và ngữ cảnh hồ sơ tới trợ lý.
export async function askAssistant(question, { history = [], candidates = [] } = {}) {
  const response = await fetch(`${API_BASE_URL}/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      message: question,
      history,
      candidates,
    }),
  });

  const result = await response.json().catch(() => ({}));

  if (!response.ok) {
    const detail = typeof result.detail === "string"
      ? result.detail
      : "Trợ lý đang gặp sự cố, vui lòng thử lại.";
    throw new Error(detail);
  }

  return result.answer;
}
