# def load_data():
#     import json
#     data_path = "Result/T5-Tach-Cau/results.json"
#     with open(data_path, "r", encoding="utf-8") as f:
#         data = json.load(f)
#     return data

def filter(data):
    import fasttext

    model = fasttext.load_model("./models/Fast_text_model/fast_text_model.bin")

    result_after_filter = []
    for sample in data:
        chunk = sample["text"]
        sentences = chunk.split(".")
        for sentence in sentences:
            if isinstance(sentence, str):
                labels, probs = model.predict(sentence)
                if labels[0] == '__label__KEEP':
                    sample_ = sample.copy()
                    sample_["text"] = sentence
                    result_after_filter.append(sample_)
    print(f"So luong mau sau khi loc: {len(result_after_filter)}")
    return result_after_filter



if __name__ == "__main__":
    import json
    data=[{
        "text": "Tôi là một sinh viên. Tôi đang học lập trình. Tôi thích học Python."
    }]
    # with open(data_path, "r", encoding="utf-8") as f:
    #     data = json.load(f)

    filtered_data = filter(data)

    print(json.dumps(filtered_data, ensure_ascii=False, indent=4))