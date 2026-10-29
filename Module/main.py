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

# from pdf2image import convert_from_path
# import pytesseract
# from pdf2image.pdf2image import pdfinfo_from_path


# pdf_path = path_list[0]
# info = pdfinfo_from_path(pdf_path)
# total_pages = info["Pages"]

# print(f"PDF có {total_pages} trang")

# text = ""

# for page_num in range(1, total_pages + 1):
#     print(f"OCR trang {page_num}/{total_pages}...")
#     image = convert_from_path(
#         pdf_path,
#         first_page=page_num,
#         last_page=page_num
#     )[0]

#     page_text = pytesseract.image_to_string(
#         image,
#         lang="vie"
#     )
#     text += f"\n===== TRANG {page_num} =====\n"
#     text += page_text

# print(text)





# model_path = "Models/Vi-T5-Base-Tach-Cau"

# if os.path.exists(model_path):
#     print("Đường dẫn tồn tại")
# else:
#     print("Đường dẫn không tồn tại")
