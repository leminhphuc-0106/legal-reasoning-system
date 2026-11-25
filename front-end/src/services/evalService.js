// evalService.js
// Lớp dịch vụ gọi các API xét hồ sơ và sinh báo cáo từ backend.
import { API_BASE_URL } from "./apiConfig.js";

// Gửi file tiêu chí và hồ sơ ứng viên lên API đánh giá bằng Knowledge Graph.
export async function evaluateCandidates(formData) {
  const response = await fetch(`${API_BASE_URL}/evaluate`, {
    method: "POST",
    body: formData,
  });

  const result = await response.json();
  if (!response.ok) {
    throw new Error(JSON.stringify(result.detail));
  }

  return result;
}

// Gửi kết quả đánh giá sang API để Qwen sinh báo cáo tổng hợp.
export async function generateReport(candidates) {
  const response = await fetch(`${API_BASE_URL}/generate-report`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(candidates),
  });

  const result = await response.json();
  if (!response.ok) {
    throw new Error(JSON.stringify(result.detail));
  }

  return result;
}
