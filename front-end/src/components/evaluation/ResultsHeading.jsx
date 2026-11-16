// ResultsHeading.jsx
// Tiêu đề khu vực kết quả đối chiếu hồ sơ và nút xuất báo cáo.
import Icon from "../common/Icon.jsx";

export default function ResultsHeading() {
  // Xử lí xuất báo cáo bằng hộp thoại in của trình duyệt.
  const handleExport = () => window.print();

  return <div className="results-heading">
    <div className="title-results-heading">
      <h2>Kết quả đối chiếu hồ sơ</h2>
    </div>
    <button className="button button-secondary export-button" onClick={handleExport}>
      <Icon>⇩</Icon> Xuất báo cáo
    </button>
  </div>;
}
