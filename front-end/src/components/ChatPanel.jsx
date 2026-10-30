// ChatPanel.jsx
// Khung trò chuyện với trợ lý: phần giới thiệu, danh sách tin nhắn,
// thông báo trạng thái và ô nhập câu hỏi kèm nút gửi.
import Icon from "./Icon.jsx";

export default function ChatPanel({ messages, notice, query, setQuery, onSend }) {
  return <section className="chat-panel">
    {/* Phần giới thiệu đầu khung chat */}

    <div className="chat-intro">
      <div className="intro-symbol">✳</div>
      <p className="eyebrow">TRỢ LÝ HÀNH CHÍNH SỐ</p>
      <h2>Xin chào, tôi có thể giúp gì?</h2>
      {/* <p className="intro-description">
        Tra cứu quy định khen thưởng, 
        kiểm tra điều kiện và tổng hợp thông tin hồ sơ ứng viên trên cùng một giao diện.
      </p> */}
    </div>


    {/* Lịch sử hội thoại: tin nhắn của trợ lý và người dùng */}
    <div className="conversation">
      {messages.map((message, index) => 

      <div className={`message-row 
        // Phân biệt user và AI role
        ${message.role === "user" ? "message-user" : ""}`
      } 
        // Nhận diện từng phần tử trong tin nhắn
        key={`${message.role}-${index}`}>
        
        {/* Hiển thị avatar của AI */}
        {message.role === "assistant" && <div className="avatar avatar-ai">AI</div>}

        <div className={`message-bubble ${message.role}`}>{message.content}</div>

        {/* {message.role === "user" && <div className="avatar avatar-user">Bạn</div>} */}

      </div>)}

      {/* Thông báo trạng thái (nạp dữ liệu, lỗi, ...) nếu có */}
      {notice && <div className="notice"><Icon>ℹ</Icon>{notice}</div>}

    </div>


    {/* Ô nhập câu hỏi; Enter để gửi, Shift+Enter để xuống dòng */}
    <div className="chat-composer"><form onSubmit={onSend}>
      <textarea value={query} onChange={e => setQuery(e.target.value)} 

        placeholder="Nhập câu hỏi về quy định hoặc hồ sơ ứng viên..." rows={2} 
        aria-label="Nhập câu hỏi"
        onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) 

        { e.preventDefault(); e.currentTarget.form.requestSubmit(); } }} 
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
