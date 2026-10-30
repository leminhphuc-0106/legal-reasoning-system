// initialData.js
// Dữ liệu minh họa mặc định cho ứng dụng: danh sách tiêu chí đánh giá và
// hai hồ sơ ứng viên mẫu dùng khi chưa nạp dữ liệu từ file.
export const initialCriteria = [
  { id: "TC01", name: "Đối tượng và điều kiện xét khen thưởng", description: "Kiểm tra đối tượng có thuộc phạm vi áp dụng của quy định hay không.", legalBasis: "Căn cứ văn bản pháp luật đã tải lên" },
  { id: "TC02", name: "Thành tích công tác", description: "Đánh giá thành tích và kết quả thực hiện nhiệm vụ.", legalBasis: "Căn cứ tiêu chuẩn xét khen thưởng" },
  { id: "TC03", name: "Chấp hành chủ trương, quy định", description: "Kiểm tra việc chấp hành quy định trong quá trình công tác.", legalBasis: "Căn cứ quy định liên quan" },
  { id: "TC04", name: "Minh chứng và hồ sơ hợp lệ", description: "Kiểm tra tính đầy đủ, hợp lệ của các tài liệu minh chứng.", legalBasis: "Căn cứ thành phần hồ sơ" },
];

// Hồ sơ ứng viên mẫu; criteriaResults chứa kết quả đối chiếu theo từng tiêu chí.
export const initialCandidates = [
  {
    id: "HS001", name: "Nguyễn Văn An", position: "Chuyên viên công nghệ thông tin",
    department: "Phòng Công nghệ thông tin", submittedAt: "29/10/2026",
    awardType: "Đề nghị xét khen thưởng",
    summary: "Hồ sơ có thông tin thành tích công tác. Cần đối chiếu các minh chứng với tiêu chuẩn áp dụng trước khi kết luận.",
    criteriaResults: [
      { criterionId: "TC01", status: "pass", reason: "Thông tin đối tượng đã được cung cấp.", evidence: "Thông tin trong hồ sơ ứng viên" },
      { criterionId: "TC02", status: "pass", reason: "Hồ sơ có thông tin về thành tích công tác.", evidence: "Bản kê khai thành tích" },
      { criterionId: "TC03", status: "pending", reason: "Chưa có đủ tài liệu để xác minh.", evidence: "Chưa có minh chứng" },
      { criterionId: "TC04", status: "fail", reason: "Cần bổ sung tài liệu minh chứng còn thiếu.", evidence: "Chưa cung cấp đầy đủ" },
    ],
  },
  // Hồ sơ thứ hai chưa có kết quả đối chiếu (mảng rỗng).
  {
    id: "HS002", name: "Trần Thị Bình", position: "Chuyên viên hành chính",
    department: "Phòng Tổ chức - Hành chính", submittedAt: "28/10/2026",
    awardType: "Đề nghị xét khen thưởng",
    summary: "Hồ sơ cần được đối chiếu với các tiêu chuẩn và tài liệu minh chứng.",
    criteriaResults: [],
  },
];
