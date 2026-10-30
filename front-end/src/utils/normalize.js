// normalize.js
// Các hàm chuẩn hóa dữ liệu đầu vào: chuyển trạng thái, tiêu chí và hồ sơ
// từ nhiều cách đặt tên trường khác nhau (tiếng Anh/tiếng Việt) về một dạng thống nhất.
export function normalizeStatus(status) {
  // Chuẩn hóa trạng thái về một trong ba giá trị: pass / fail / pending.
  const value = String(status ?? "").trim().toLowerCase();
  if (["pass", "passed", "đạt", "đạt tiêu chí", "true", "yes"].includes(value)) return "pass";
  if (["fail", "failed", "chưa đạt", "không đạt", "false", "no"].includes(value)) return "fail";
  return "pending";
}

// Chuẩn hóa danh sách tiêu chí từ file JSON; hỗ trợ nhiều tên trường khác nhau.
export function normalizeCriteria(data) {
  const items = Array.isArray(data) ? data : data?.criteria ?? data?.criterias ?? data?.tieu_chi;
  if (!Array.isArray(items)) throw new Error("Không tìm thấy mảng criteria trong file JSON.");
  return items.map((item, index) => ({
    id: String(item.id ?? item.code ?? `TC${index + 1}`),
    name: item.name ?? item.ten_tieu_chi ?? item.title ?? `Tiêu chí ${index + 1}`,
    description: item.description ?? item.mo_ta ?? item.requirement ?? "Chưa có mô tả.",
    legalBasis: item.legalBasis ?? item.can_cu_phap_ly ?? item.legal_basis ?? "",
    required: item.required ?? item.bat_buoc ?? true,
  }));
}

// Chuẩn hóa một hồ sơ ứng viên: ánh xạ các trường và kết quả tiêu chí về cấu trúc chung.
export function normalizeCandidate(item, index) {
  const raw = item.criteriaResults ?? item.criteria_results ?? item.results ?? item.ket_qua_tieu_chi ?? [];
  const results = Array.isArray(raw) ? raw : Object.entries(raw).map(([criterionId, value]) => ({
    criterionId, ...(typeof value === "object" ? value : { status: value }),
  }));
  return {
    id: String(item.id ?? item.ma_ho_so ?? item.candidateId ?? `HS${index + 1}`),
    name: item.name ?? item.ho_ten ?? item.full_name ?? `Ứng viên ${index + 1}`,
    position: item.position ?? item.vi_tri ?? item.chuc_vu ?? "Chưa cập nhật",
    department: item.department ?? item.don_vi ?? item.phong_ban ?? "Chưa cập nhật",
    submittedAt: item.submittedAt ?? item.ngay_nop ?? item.submitted_at ?? "Chưa cập nhật",
    awardType: item.awardType ?? item.hinh_thuc_khen_thuong ?? "Chưa xác định",
    summary: item.summary ?? item.tom_tat ?? item.nhan_xet ?? "Chưa có nhận xét.",
    criteriaResults: results.map(result => ({
      criterionId: String(result.criterionId ?? result.criterion_id ?? result.id ?? result.ma_tieu_chi ?? ""),
      status: normalizeStatus(result.status ?? result.trang_thai ?? result.result),
      reason: result.reason ?? result.ly_do ?? result.explanation ?? "",
      evidence: result.evidence ?? result.minh_chung ?? "",
    })),
  };
}

// Đọc nội dung file JSON, loại bỏ ký tự BOM (nếu có) trước khi phân tích.
export async function readJsonFile(file) {
  return JSON.parse((await file.text()).replace(/^\uFEFF/, ""));
}
