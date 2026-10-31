
import re
import json


def parse_period_items(text):
    """
    Tách các thông tin có cấu trúc:
    Tên nội dung năm học
    """
    results = []

    # Tìm các cụm có dạng: Nội dung + năm học
    pattern = r"([^;]+?)\s+(\d{4}\s*-\s*\d{4})"

    matches = re.findall(pattern, text)

    for content, year in matches:
        results.append({
            "nam": year.strip(),
            "noi_dung": content.strip()
        })

    return results


def txt_to_json(input_path, output_path):

    with open(input_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    data = {}

    # Ánh xạ tên trường TXT sang JSON
    field_mapping = {
        "Đơn vị": "don_vi",
        "Loại xét": "loai_xet",
        "Thời điểm xét": "thoi_diem_xet",
        "Danh hiệu thi đua": "danh_hieu_thi_dua",
        "Kết quả đánh giá, xếp loại": "ket_qua_danh_gia",
        "Hình thức khen thưởng": "hinh_thuc_khen_thuong"
    }

    for line in lines:

        line = line.strip()

        if not line or ":" not in line:
            continue

        key, value = line.split(":", 1)

        key = key.strip()
        value = value.strip()

        if key not in field_mapping:
            continue

        json_key = field_mapping[key]

        # Các trường chứa danh sách theo năm học
        if key in [
            "Danh hiệu thi đua",
            "Kết quả đánh giá, xếp loại",
            "Hình thức khen thưởng"
        ]:

            items = parse_period_items(value)

            # Đổi tên trường noi_dung theo từng loại dữ liệu
            content_key = {
                "Danh hiệu thi đua": "danh_hieu",
                "Kết quả đánh giá, xếp loại": "ket_qua",
                "Hình thức khen thưởng": "hinh_thuc"
            }[key]

            data[json_key] = [
                {
                    "nam": item["nam"],
                    content_key: item["noi_dung"]
                }
                for item in items
            ]

        else:
            data[json_key] = value

    # Ghi file JSON
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    print(f"Đã chuyển đổi thành công: {output_path}")


# if __name__ == "__main__":

#     txt_to_json(
#         input_path="./data_test/2024-canhan-xetBangkhenUBND.txt",
#         output_path="./back-end/result/predict_profile/predicted_profile.json"
#     )
