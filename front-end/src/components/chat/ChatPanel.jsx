// ChatPanel.jsx
// Khung trò chuyện với trợ lý: phần giới thiệu, danh sách tin nhắn,
// thông báo trạng thái và ô nhập câu hỏi kèm nút gửi.
import Icon from "../common/Icon.jsx";

export default function ChatPanel({ messages, notice, query, setQuery, onSend }) {
  // Xử lí gửi câu hỏi khi nhấn Enter, Shift+Enter để xuống dòng.
  function handleKeyDown(event) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      event.currentTarget.form.requestSubmit();
    }
  }

  return <section className="chat-panel">
    {/* Phần giới thiệu đầu khung chat */}

    <div className="chat-intro">
      <div className="intro-symbol">✳</div>
      <p className="eyebrow">TRỢ LÝ HÀNH CHÍNH SỐ</p>
      <h2>Xin chào, tôi có thể giúp gì?</h2>
    </div>


    {/* Lịch sử hội thoại: tin nhắn của trợ lý và người dùng */}
    <div className="conversation">
      {messages.map((message, index) =>
        <div
          key={`${message.role}-${index}`}
          className={`message-row ${message.role === "user" ? "message-user" : ""}`}
        >
          {/* Hiển thị avatar của AI */}
          {message.role === "assistant" && <div className="avatar avatar-ai">AI</div>}

          <div
            className={`message-bubble ${message.role}`}
            style={{ whiteSpace: "pre-wrap" }}
          >
            {message.content}
          </div>
          
        </div>)}

      {/* Thông báo trạng thái (nạp dữ liệu, lỗi, ...) nếu có */}
      {notice && <div className="notice"><Icon>ℹ</Icon>{notice}</div>}

    </div>


    {/* Ô nhập câu hỏi; Enter để gửi, Shift+Enter để xuống dòng */}
    <div className="chat-composer"><form onSubmit={onSend}>
      <textarea value={query} onChange={e => setQuery(e.target.value)} 

        placeholder="Nhập câu hỏi về quy định hoặc hồ sơ ứng viên..." rows={2} 
        aria-label="Nhập câu hỏi"
        onKeyDown={handleKeyDown}
      />

      <div className="composer-bottom">
        <span className="composer-hint">Enter để gửi · Shift + Enter xuống dòng</span>
        <button type="submit" 
                className="send-button" 
                disabled={!query.trim()} aria-label="Gửi câu hỏi">↑
        </button>
      </div>
    </form></div>
  </section>;
}
