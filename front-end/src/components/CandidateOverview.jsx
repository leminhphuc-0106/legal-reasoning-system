// CandidateOverview.jsx
// Thẻ tóm tắt thông tin nhận diện của hồ sơ ứng viên: họ tên, mã, chức vụ,
// đơn vị, ngày nộp, hình thức khen thưởng và tệp nguồn (nếu có).
import Icon from "./Icon.jsx";

export default function CandidateOverview({ candidate }) {
  // Tạo chữ viết tắt từ hai từ cuối của họ tên để hiển thị trong avatar.
  const initials = candidate.name.split(" ").slice(-2).map(part => part[0]).join("").toUpperCase();
  return <article className="overview-card">


    {/* Avatar chữ viết tắt của ứng viên */}
    <div className="candidate-avatar">{initials}</div>
    
    <div className="candidate-main">

      {/* Họ tên và mã hồ sơ */}
      <div className="candidate-name-row">
        <h3>{candidate.name}</h3>
        <span className="candidate-id">{candidate.id}</span>
      </div>

      {/* Ngày nộp hồ sơ */}
      <div className="candidate-meta">        
        <span>
          <Icon>◷</Icon> Ngày nộp: {candidate.submittedAt}
        </span>
      </div>
      
    </div>


  </article>;
}
