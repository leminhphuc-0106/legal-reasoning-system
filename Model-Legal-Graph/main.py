import os
data_path = "Data"


if os.path.exists(data_path):
    path_list = [
        os.path.join(data_path, f)
        for f in os.listdir(data_path)
        if f.lower().endswith(".pdf")
    ]
    for path in path_list:
        print(path)
else:
    print("Đường dẫn không tồn tại")

import fasttext
model = fasttext.load_model("Models/Fast_text_model/fast_text_model.bin")

all_sentences = []

if os.path.exists("output.txt"):
    with open("output.txt", "r", encoding="utf-8") as f:
        all_sentences = [
            line.strip()
            for line in f
            if line.strip()
        ]


all_sentences_after_filter = []
print(f"So luong cau truoc khi loc: {len(all_sentences)}")
for sentence in all_sentences:
    if isinstance(sentence, str):
        labels, probs = model.predict(sentence)
        if labels[0] == '__label__KEEP':
            all_sentences_after_filter.append(sentence)
print(f"So luong cau sau khi loc: {len(all_sentences_after_filter)}")


for sentence in all_sentences_after_filter:
    print("="*10)
    print(sentence)
    print("="*10)
    print()
