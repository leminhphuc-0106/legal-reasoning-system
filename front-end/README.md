# Xét Khen Thưởng - Front-end

Giao diện React + Vite cho hệ thống hỗ trợ xét khen thưởng hành chính.

## Cấu trúc thư mục

```
src/
├── assets/                 # Hình ảnh và tài nguyên tĩnh
├── components/
│   ├── chat/               # Khung trò chuyện với trợ lý
│   ├── common/             # Thành phần dùng chung (Icon, ...)
│   ├── evaluation/         # Hiển thị kết quả đối chiếu hồ sơ
│   └── upload/             # Nạp văn bản luật và hồ sơ ứng viên
├── data/                   # Dữ liệu mẫu
├── layouts/                # Bố cục chung (MainLayout, Topbar)
├── services/               # Gọi API backend (chat, đánh giá, sinh báo cáo)
├── styles/                 # CSS toàn cục (App.css, index.css)
├── utils/                  # Hàm tiện ích (chuẩn hóa dữ liệu)
├── App.jsx                 # Quản lý trạng thái và điều phối giao diện
└── main.jsx                # Điểm khởi tạo ứng dụng
```

## Lệnh

```bash
npm install
npm run dev
npm run build
npm run lint
```
