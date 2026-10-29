import json
from pathlib import Path


# 1. Đọc dữ liệu JSON từ thư mục
def load_data(dataset_path):
    dataset_path = Path(dataset_path)
    dataset = []

    if not dataset_path.is_dir():
        raise FileNotFoundError(
            f"Không tìm thấy thư mục dữ liệu: {dataset_path}"
        )

    for file_path in sorted(dataset_path.glob("*.json")):
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list):
            raise ValueError(
                f"Dữ liệu trong {file_path} phải là một danh sách JSON."
            )

        dataset.extend(data)

    return dataset


# 2. Chuẩn hóa cấu trúc dữ liệu và loại bỏ mẫu không có relation
def preprocess_data(data):
    clean_data = []

    for item in data:
        relations = item.get("relations", [])

        # Bỏ qua mẫu không có quan hệ
        if not relations:
            continue

        clean_item = {
            "tokenized_text": item["tokenized_text"],
            "ner": item.get("ner", []),
            "relations": relations,
        }

        clean_data.append(clean_item)

    return clean_data


# 3. Lọc các mẫu có relation sai định dạng
def filter_valid_relations(data):
    clean_data = []

    for sample in data:
        relations = sample.get("relations", [])

        # Bỏ qua mẫu không có relation
        if not relations:
            continue

        # Mỗi relation phải là list/tuple gồm đúng 3 phần tử
        is_valid = all(
            isinstance(rel, (list, tuple)) and len(rel) == 3
            for rel in relations
        )

        if is_valid:
            clean_data.append(sample)

    return clean_data

# 4. Thực hiện toàn bộ quy trình xử lý cho một tập dữ liệu
def prepare_dataset(dataset_path):
    data = load_data(dataset_path)
    data = preprocess_data(data)
    data = filter_valid_relations(data)

    return data

# 5. Đọc và xử lý cả tập train và eval
def prepare_train_eval(train_path, eval_path):
    clean_data = prepare_dataset(train_path)
    clean_data_eval = prepare_dataset(eval_path)

    return clean_data, clean_data_eval