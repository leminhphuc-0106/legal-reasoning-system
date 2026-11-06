
// SummaryCard.jsx

// Chuyển tiếng Việt có dấu thành chữ IN HOA KHÔNG DẤU
const removeVietnameseAccents = (str = "") => {
  return str
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/đ/g, "d")
    .replace(/Đ/g, "D")
    .toUpperCase();
};

export default function SummaryCard({ candidate }) {
  // Lấy dữ liệu coverage từ candidate
  const coverage = candidate?.coverage || {};

  const total = coverage.total_criteria || 0;
  const achieved = coverage.achieved_criteria || 0;
  const notAchieved = coverage.not_achieved_criteria || 0;

  // Tỷ lệ đạt tiêu chí
  const percentage = total > 0
    ? Math.round((achieved / total) * 100)
    : 0;

  // Nội dung hiển thị
  const summary = candidate?.summary
    || `HO SO ${candidate?.name || ""} DA DAT ${achieved}/${total} TIEU CHI.`;

  return (
    <article className="summary-card">

      {/* Header */}
      <div className="summary-header">
        <div>
          <p className="eyebrow">
            {removeVietnameseAccents("Tổng quan đánh giá")}
          </p>

          <h3>
            {removeVietnameseAccents("Mức độ đáp ứng tiêu chí")}
          </h3>
        </div>

        <div className="score">
          <strong>{percentage}%</strong>
          <span>
            {removeVietnameseAccents("Đạt tiêu chí")}
          </span>
        </div>
      </div>

      {/* Progress bar */}
      <div className="progress-track">
        <div
          className="progress-fill"
          style={{ width: `${percentage}%` }}
        />
      </div>

      {/* Statistics */}
      <div className="summary-stats">

        <div className="stat-item">
          <span className="stat-dot pass-dot" />
          <div>
            <strong>{achieved}</strong>
            <span>
              {removeVietnameseAccents("Đạt")}
            </span>
          </div>
        </div>

        <div className="stat-item">
          <span className="stat-dot fail-dot" />
          <div>
            <strong>{notAchieved}</strong>
            <span>
              {removeVietnameseAccents("Chưa đạt")}
            </span>
          </div>
        </div>

      </div>

      {/* Summary */}
      <p className="summary-note">
        {removeVietnameseAccents(summary)}
      </p>

    </article>
  );
}
