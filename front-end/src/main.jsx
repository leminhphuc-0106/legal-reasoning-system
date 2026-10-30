// main.jsx
// Điểm khởi tạo ứng dụng React: gắn component App vào phần tử #root trong index.html.
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

// Render ứng dụng trong StrictMode để phát hiện các vấn đề tiềm ẩn khi phát triển.
createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
