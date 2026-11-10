def parse_text_to_dict(text):
    field_mapping = {
        "Cá nhân": "DOI_TUONG",
        "Tập thể": "DOI_TUONG",
        "Loại xét": "LOAI_XET",
        "Thời điểm xét": "THOI_DIEM_XET",
        "Danh hiệu thi đua": "DANH_HIEU_THI_DUA",
        "Kết quả đánh giá": "KET_QUA_DANH_GIA",
        "Hình thức khen thưởng": "HINH_THUC_KHEN_THUONG",
        "Sáng kiến NCKH": "SANG_KIEN_NCKH"
    }

    result = {}
    lines = text.splitlines()

    # Lấy dòng đầu tiên không rỗng
    first_line = next((line.strip() for line in lines if line.strip()), "")

    if first_line.startswith("Cá nhân:"):
        result["LOAI_DOI_TUONG"] = "CA_NHAN"

    elif first_line.startswith("Tập thể:"):
        result["LOAI_DOI_TUONG"] = "TAP_THE"

    # Trích xuất dữ liệu
    for line in lines:
        line = line.strip()

        if not line or ":" not in line:
            continue

        key, value = line.split(":", 1)

        key = key.strip()
        value = value.strip()

        if key in field_mapping:
            result[field_mapping[key]] = value

    return result