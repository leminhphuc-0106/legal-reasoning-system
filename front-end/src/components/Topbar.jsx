// Topbar.jsx
// Thanh tiêu đề trên cùng: tên hệ thống, trạng thái giao diện và nút đặt lại dữ liệu.
import Icon from "./Icon.jsx";

export default function Topbar({ onReset }) {
  return <header className="topbar">
    {/* Thương hiệu và tên chức năng */}
    <div className="brand">
      
      <div className="brand-mark"><Icon>⚖</Icon></div>
      <div>
        <h1>Hệ thống hỗ trợ ra quyết định khen thưởng hành chính</h1>
        <p>Trợ lý tra cứu pháp luật và đối chiếu hồ sơ ứng viên</p>
      </div>
      <span className="version">v1.0</span>

    </div>
    {/* Trạng thái hệ thống và nút khôi phục dữ liệu ban đầu */}
    <div className="top-actions">
      <span className="system-status"><span className="status-dot" />Giao diện sẵn sàng</span>
      <button className="button button-secondary" onClick={onReset}>↻ Đặt lại</button>
    </div>
  </header>;
}
