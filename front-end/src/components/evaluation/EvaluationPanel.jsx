// EvaluationPanel.jsx
// Khu vực chọn hồ sơ đang xem và hiển thị chi tiết kết quả đối chiếu tiêu chí.
import CandidateOverview from "./CandidateOverview.jsx";
import SummaryCard from "./SummaryCard.jsx";
import CriteriaList from "./CriteriaList.jsx";
import Icon from "../common/Icon.jsx";

export default function EvaluationPanel({
  candidates,
  selectedId,
  onSelectCandidate,
  filter,
  setFilter,
}) {
  // Xác định hồ sơ đang xem, nếu không tìm thấy thì dùng hồ sơ đầu tiên.
  const selectedCandidate = candidates.find(item => item.id === selectedId) ?? candidates[0];

  // Xử lí đổi hồ sơ đang xem và đưa bộ lọc về trạng thái tất cả.
  function handleSelectCandidate(event) {
    onSelectCandidate(event.target.value);
    setFilter("all");
  }

  return <>
    {/* Thanh chọn hồ sơ đang xem */}
    <div className="candidate-toolbar">
      <label htmlFor="candidate-select"><Icon>♙</Icon> Hồ sơ đang xem</label>
      <select
        id="candidate-select"
        value={selectedCandidate?.id ?? ""}
        onChange={handleSelectCandidate}
      >
        {candidates.map(candidate =>
          <option key={candidate.id} value={candidate.id}>{candidate.name} — {candidate.id}</option>)}
      </select>
      <span className="candidate-count">{candidates.length} hồ sơ</span>
    </div>

    {/* Nội dung chi tiết khi đã có hồ sơ được chọn */}
    {selectedCandidate ?
      <>
        <CandidateOverview candidate={selectedCandidate} />
        <SummaryCard candidate={selectedCandidate} />
        <CriteriaList
          candidate={selectedCandidate}
          filter={filter}
          setFilter={setFilter}
        />
        <div className="disclaimer">
          <Icon>ⓘ</Icon><p><strong>Lưu ý: </strong>
            Tỷ lệ đạt chỉ là thống kê tiêu chí, không tự động thay thế kết luận pháp lý hoặc quyết định của người có thẩm quyền.</p>
        </div>
      </> :
      <div className="empty-state">Chưa có hồ sơ. Hãy tải lên file JSON ứng viên để bắt đầu.</div>}
  </>;
}
