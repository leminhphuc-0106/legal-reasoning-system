import json
import os

#Load file json
def load_json_data(path: str):
    """Load JSON dataset."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


#Load dữ liệu từ thư mục
def load_from_direct(path:str):
    data_train = []
    for file_name in os.listdir(path):
        if file_name.endswith('.json'):
            file_path = os.path.join(path, file_name)
            data_file = load_json_data(file_path)
            data_train.extend(data_file)
    return data_train

#format trước khi huấn luyện
def format_item(data):
    if data is isinstance(dict):
        formated_data = {
          "tokenized_text": data["tokenized_text"],
          "ner": data.get("ner", [])
        }
        return formated_data
    return None


def format_dataset(dataset):
    formated_dataset = []
    for item in dataset:
        if item is None:
            continue
        clean_data = format_item(item)
        formated_dataset.append(clean_data)

    return formated_dataset