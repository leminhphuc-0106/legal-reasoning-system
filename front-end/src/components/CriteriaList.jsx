// CriteriaList.jsx
// Hiển thị danh sách tiêu chí đã đối chiếu, kèm bộ lọc theo trạng thái
// (đạt / chưa đạt / chưa đủ dữ liệu) và chi tiết lý do, minh chứng, căn cứ.
import Icon from "./Icon.jsx";

export default function CriteriaList({ results, visibleResults, counts, filter, setFilter }) {
  // Cấu hình các tab lọc và nhãn hiển thị tương ứng.

  const tabs = [["all", `Tất cả (${results.length})`], 
              ["pass", `Đạt (${counts.pass})`], 
              ["fail", `Chưa đạt (${counts.fail})`], 
              ["pending", `Chưa rõ (${counts.pending})`]];

  return <>
    {/* Tiêu đề và các tab lọc trạng thái tiêu chí */}
    <div className="criteria-heading">
      <div>
        <h3><Icon>☷</Icon> Chi tiết tiêu chí</h3>
        {/* <p>Đối chiếu từng điều kiện và minh chứng liên quan</p> */}
      </div>

      <div className="filter-tabs">{tabs.map(([value, label]) => 
        <button key={value} 
                className={`filter-tab ${filter === value ? "active" : ""} ${value}`} 
                onClick={() => setFilter(value)}>{label}
          </button>)}
      </div>
    </div>



    {/* Danh sách thẻ tiêu chí sau khi lọc */}
    <div className="criteria-list">
      {visibleResults.map((item, index) => 
      // 1 thẻ tiêu chí sẽ có cấu trúc như sau
      <article className={`criterion-card ${item.status}`} key={item.id}>

        <div className="criterion-top">
          <div className="criterion-title">
            <span className="criterion-number">{index + 1}</span>
            <h4>{item.name}</h4>
          </div>

          {/* Nhãn trạng thái tiêu chí */}
          <span className={`status-badge ${item.status}`}>
            {item.status === "pass" ? "✓ ĐẠT" : 
            item.status === "fail" ? "× CHƯA ĐẠT" : "◷ CHƯA ĐỦ DỮ LIỆU"}
          </span>
        </div>


        {/* Mô tả tiêu chí và lý do đối chiếu */}
        <p className="criterion-description">{item.description}</p><p className="criterion-reason">{item.reason}</p>
        {/* Minh chứng và căn cứ pháp lý liên quan */}
        <div className="criterion-footer"><span><Icon>▧</Icon> Minh chứng: {item.evidence}</span>{item.legalBasis && <span className="legal-basis">Căn cứ: {item.legalBasis}</span>}</div>
      </article>)}
      {/* Trạng thái rỗng khi không có tiêu chí phù hợp bộ lọc */}
      {visibleResults.length === 0 && <div className="empty-state">Không có tiêu chí nào thuộc trạng thái đang chọn.</div>}
    </div>
  </>;
}
