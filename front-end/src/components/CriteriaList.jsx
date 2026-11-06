
import Icon from "./Icon.jsx";

// Chuyển tiếng Việt có dấu thành chữ IN HOA KHÔNG DẤU
// const removeVietnameseAccents = (str = "") => {
//   return String(str)
//     .normalize("NFD")
//     .replace(/[\u0300-\u036f]/g, "")
//     .replace(/đ/g, "d")
//     .replace(/Đ/g, "D")
//     .toUpperCase();
// };

export default function CriteriaList({
  candidate,
  filter,
  setFilter
}) {
  // Lấy dữ liệu đối chiếu
  const coverage = candidate?.coverage || {};

  const total = coverage.total_criteria || 0;
  const pass = coverage.achieved_criteria || 0;
  const fail = coverage.not_achieved_criteria || 0;
  const percentage = coverage.coverage_percentage || 0;

  // Chuyển matched_criteria và unmatched_criteria
  // thành cấu trúc thống nhất
  const results = [
    ...(coverage.matched_criteria || []).map((item, index) => ({
      ...item,
      id: `pass-${index}`,
      status: "pass"
    })),

    ...(coverage.unmatched_criteria || []).map((item, index) => ({
      ...item,
      id: `fail-${index}`,
      status: "fail"
    }))
  ];

  // Thống kê số lượng
  const counts = {
    pass,
    fail,
    pending: 0
  };

  // Lọc tiêu chí
  const visibleResults = results.filter(item =>
    filter === "all" || item.status === filter
  );

  // Chuyển path thành nội dung dễ đọc

  const relationText = {
    AP_DUNG_CHO: "áp dụng cho",
    DAT_DANH_HIEU: "đạt danh hiệu",
    PHAI_DAT_DANH_HIEU: "phải đạt danh hiệu",
    DAT_TIEU_CHUAN: "đạt tiêu chuẩn",
    DAP_UNG_DIEU_KIEN: "đáp ứng điều kiện",
    CO_THANH_TICH: "có thành tích",
    CO_SANG_KIEN: "có sáng kiến",
    CO_CONG_TRINH_KHOA_HOC: "có công trình khoa học",
    CO_THAM_QUYEN_QUYET_DINH: "có thẩm quyền quyết định",
    DUOC_CONG_NHAN_BOI: "được công nhận bởi",
    CAN_CU_XET_TANG: "là căn cứ để xét tặng",
    DUOC_QUY_DINH_TAI: "được quy định tại",
    BAN_HANH_BOI: "được ban hành bởi",
    KE_THUA_TU: "kế thừa từ",
    DUOC_XET_TRONG_THOI_GIAN: "được xét trong thời gian",
    DUOC_BINH_XET_THONG_QUA: "được bình xét thông qua",
    THAM_GIA_QUY_TRINH: "tham gia quy trình"
  };

  const formatPath = (path = []) => {
    if (!path.length) return [];

    const relations = [];
    let current = path[0];

    // Khởi tạo câu bằng thực thể đầu tiên
    let sentence = current.head;

    // Duyệt các quan hệ
    for (let i = 0; i < path.length; i++) {
      const relation = path[i];

      // Kiểm tra tính liên kết giữa các quan hệ
      if (i > 0 && current.tail !== relation.head) {
        relations.push(sentence);
        sentence = relation.head;
      }

      // Lấy cụm từ tiếng Việt tương ứng với quan hệ
      const predicate =
        relationText[relation.relation] || relation.relation;

      // Ghép thành câu
      sentence += ` ${predicate} ${relation.tail}`;

      current = relation;
    }

    // Thêm câu cuối cùng
    relations.push(sentence);

    // Chuẩn hóa chữ cái đầu và dấu câu
    return relations.map(text => {
      text = text.trim();

      return (
        text.charAt(0).toLocaleUpperCase("vi-VN") +
        text.slice(1).replace(/[.!?]*$/, "") +
        "."
      );
    });
  };


  // Hiển thị căn cứ pháp lý
  const formatLegalBasis = (item) => {
    const { article_id, section_id, point_label } = item;

    return(
      `Điều ${article_id}, khoản ${section_id}, điểm ${point_label}`
    );
  };

  // Các tab lọc
  const tabs = [
    ["all", `TẤT CẢ (${total})`],
    ["pass", `ĐẠT (${counts.pass})`],
    ["fail", `CHƯA ĐẠT (${counts.fail})`],
    ["pending", `CHƯA RÕ (${counts.pending})`]
  ];

  return (
    <>
      {/* Tổng quan mức độ đáp ứng */}
      <div className="coverage-summary">
        <div className="coverage-header">
          <h3>

            {"Mức độ đáp ứng tiêu chí"}
          </h3>

          <strong>{percentage.toFixed(1)}%</strong>
        </div>

        <div className="coverage-progress">
          <div
            className="coverage-progress-bar"
            style={{ width: `${percentage}%` }}
          />
        </div>

        <div className="coverage-stats">
          <span>
            {"Tổng"}: {total}{" "}
            {"tiêu chí"}
          </span>

          <span>
            {"Đạt"}: {pass}
          </span>

          <span>
            {"Chưa đạt"}: {fail}
          </span>
        </div>
      </div>

      {/* Tiêu đề và bộ lọc */}
      <div className="criteria-heading">
        <div>
          <h3>
            <Icon>☷</Icon>{" "}
            {"Chi tiết tiêu chí"}
          </h3>
        </div>

        <div className="filter-tabs">
          {tabs.map(([value, label]) => (
            <button
              key={value}
              className={`filter-tab ${
                filter === value ? "active" : ""
              } ${value}`}
              onClick={() => setFilter(value)}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Danh sách tiêu chí */}
      <div className="criteria-list">
        {visibleResults.map((item, index) => (
          <article
            className={`criterion-card ${item.status}`}
            key={item.id}
          >
            <div className="criterion-top">
              <div className="criterion-title">
                <span className="criterion-number">
                  {index + 1}
                </span>

                <h4>
                  {"Tiêu chí tại"}{" "}
                  {formatLegalBasis(item)}
                </h4>
              </div>

              <span className={`status-badge ${item.status}`}>
                {item.status === "pass"
                  ? "✓ DAT"
                  : "× CHUA DAT"}
              </span>
            </div>

            {/* Nội dung tiêu chí */}
            <div className="criterion-description">
              <strong>
                {"Nội dung tiêu chí"}:
              </strong>

              {formatPath(item.path).map((text, i) => (
                <p key={i}>{text}</p>
              ))}
            </div>

            {/* Chi tiết quan hệ */}
            {/* <div className="criterion-reason">
              <strong>
                {"Thông tin đối chiếu"}:
              </strong>

              {formatPath(item.path).map((text, i) => (
                <p key={i}>{text}</p>
              ))}
            </div> */}

            {/* Căn cứ pháp lý */}
            <div className="criterion-footer">
              <span>
                <Icon>▧</Icon>{" "}
                {("Căn cứ")}:{" "}
                {formatLegalBasis(item)}
              </span>
            </div>
          </article>
        ))}

        {visibleResults.length === 0 && (
          <div className="empty-state">
            {
              "Không có tiêu chí nào thuộc trạng thái đang chọn."
            }
          </div>
        )}
      </div>
    </>
  );
}
