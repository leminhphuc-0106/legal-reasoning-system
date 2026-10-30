// SummaryCard.jsx
// Thẻ tổng quan kết quả: tỷ lệ đạt tiêu chí, thanh tiến trình và số lượng
// tiêu chí theo từng trạng thái, kèm nhận xét tóm tắt của hồ sơ.
export default function SummaryCard({ candidate, percentage, counts }) {
  return <article className="summary-card">

    {/* Điểm tỷ lệ đạt và tiêu đề tổng quan */}
    <div className="summary-header">
      <div>
        <p className="eyebrow">TỔNG QUAN ĐÁNH GIÁ</p>
        <h3>Mức độ đáp ứng tiêu chí</h3>
      </div>
      <div className="score">
        <strong>{percentage}%</strong>
        <span>Đạt tiêu chí</span>
      </div>
    </div>
    {/* Thanh tiến trình thể hiện trực quan tỷ lệ đạt */}


    <div className="progress-track"><div className="progress-fill" style={{ width: `${percentage}%` }} /></div>
    {/* Số lượng tiêu chí đạt / chưa đạt / chưa đủ dữ liệu */}
    <div className="summary-stats">
      <div className="stat-item"><span className="stat-dot pass-dot"/>
        <div>
          <strong>{counts.pass}</strong>
          <span>Đạt</span>
        </div>  
      </div>


      <div className="stat-item">
        <span className="stat-dot fail-dot" />
        <div>
          <strong>{counts.fail}</strong>
          <span>Chưa đạt</span>
        </div>
      </div>


      <div className="stat-item">
        <span className="stat-dot pending-dot" />
        <div>
          <strong>{counts.pending}</strong>
          <span>Chưa đủ dữ liệu</span>
        </div>
      </div>
    </div>
    
    {/* Nhận xét tóm tắt của hồ sơ */}
    <p className="summary-note">{candidate.summary}</p>
  </article>;
}
