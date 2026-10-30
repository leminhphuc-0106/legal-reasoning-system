// chatService.js
// Lớp dịch vụ giao tiếp với trợ lý. Hiện là mock trả về câu trả lời mẫu;
// khi backend sẵn sàng, thay phần thân bằng fetch() tới API thực tế.
// Mock service: thay phần này bằng fetch() đến backend khi API đã sẵn sàng.
export async function askAssistant(question) {
  return `Giao diện đã nhận câu hỏi: “${question}”. Để trả lời dựa trên văn bản pháp luật và phân tích hồ sơ thực tế, hãy kết nối hàm askAssistant() với API backend.`;
}
