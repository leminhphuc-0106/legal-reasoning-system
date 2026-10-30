// Icon.jsx
// Component hiển thị biểu tượng dạng ký tự; aria-hidden để trình đọc màn hình bỏ qua.
export default function Icon({ children }) {
  return <span className="icon" aria-hidden="true">{children}</span>;
}
