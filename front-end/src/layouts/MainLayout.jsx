// MainLayout.jsx
// Bố cục chính của ứng dụng: thanh tiêu đề phía trên, bên dưới chia hai cột
// (khung chat bên trái và vùng kết quả đánh giá bên phải).
import Topbar from "../components/Topbar.jsx";
import ChatPanel from "../components/ChatPanel.jsx";

export default function MainLayout({ onReset, chatProps, children }) {
  return <div className="app-shell">

    {/* Thanh tiêu đề chung */}
    <Topbar onReset={onReset} />

    <main className="workspace">
      {/* Gồm 2 phần Chat và phần hiển thị kết quả */}

      {/* Cột trái: khung trò chuyện với trợ lý */}

      <ChatPanel {...chatProps} />

      {/* Cột phải: nội dung kết quả đánh giá được truyền qua children */}
      <section className="results-panel">{children}</section>

    </main>
    
  </div>;
}
