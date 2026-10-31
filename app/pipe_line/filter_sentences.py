def load_data():
    import json
    data_path = "Result/T5-Tach-Cau/results.json"
    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data

def filter(data):
    import fasttext

    model = fasttext.load_model("./models/Fast_text_model/fast_text_model.bin")

    result_after_filer = []
    for sample in data:
        chunk = sample["text"]
        sentences = chunk.split(".")
        for sentence in sentences:
            if isinstance(sentence, str):
                labels, probs = model.predict(sentence)
                if labels[0] == '__label__KEEP':
                    sample_ = sample.copy()
                    sample_["text"] = sentence
                    result_after_filer.append(sample_)
    print(f"So luong mau sau khi loc: {len(result_after_filer)}")