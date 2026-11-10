# full_pipeline.py
# Pipeline xử lý văn bản pháp luật từ API tới đồ thị tri thức:
#   1. Nhận file từ API (UploadFile / bytes / đường dẫn)
#   2. OCR + chunking theo cấu trúc Điều - Khoản - Điểm
#   3. Tách câu đơn bằng mô hình Vi-T5 đã fine-tune
#   4. Lọc câu bằng mô hình FastText
#   5. Trích xuất thực thể và quan hệ bằng mô hình GLiNER
#
# Có thể dùng trực tiếp trong route FastAPI:
#   result = await run_pipeline(criteria_file, candidate_files)

import io
import json
import os
import re
from pathlib import Path
from typing import Any, Iterable, Optional

# Thư mục gốc của project (app/pipe_line -> app -> project root)
BASE_DIR = Path(__file__).resolve().parents[2]

# Đường dẫn model, có thể ghi đè bằng biến môi trường khi triển khai.
SIMPLIFY_MODEL_PATH = os.getenv(
    "SIMPLIFY_MODEL_PATH",
    str(BASE_DIR / "models" / "Vi-T5-Base-Tach-Cau"),
)
FASTTEXT_MODEL_PATH = os.getenv(
    "FASTTEXT_MODEL_PATH",
    str(BASE_DIR / "models" / "Fast_text_model" / "fast_text_model.bin"),
)
GLINER_MODEL_PATH = os.getenv(
    "GLINER_MODEL_PATH",
    str(BASE_DIR / "models" / "GLiNER-Model"),
)

# Nơi lưu kết quả của pipeline.
OUTPUT_DIR = BASE_DIR / "app" / "result" / "full_pipeline"
OUTPUT_FILE = OUTPUT_DIR / "output.json"

POPPLER_PATH = "D:/ProgramFile86/poppler-26.09.0/Library/bin"

# # ---------------------------------------------------------------------------
# # ORCHESTRATOR
# # ---------------------------------------------------------------------------
def _save_output(payload: dict, output_file: Path = OUTPUT_FILE) -> None:
    """Ghi kết quả pipeline ra file JSON."""
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)

    print(f"Đã ghi kết quả vào: {output_file}")

def extract_text_from_pdf(pdf_bytes: Any) -> str:
    """OCR toàn bộ file PDF và trả về văn bản thô."""
    from pdf2image import convert_from_bytes
    from pdf2image.pdf2image import pdfinfo_from_bytes

    # pdf_bytes = _to_bytes(pdf_source)

    info = pdfinfo_from_bytes(pdf_bytes,
        poppler_path=POPPLER_PATH)
    total_pages = info["Pages"]

    print(f"PDF có {total_pages} trang")

    text = ""
    for page_num in range(1, total_pages + 1):
        print(f"OCR trang {page_num}/{total_pages}...")

        image = convert_from_bytes(
            pdf_bytes,
            first_page=page_num,
            last_page=page_num,
            poppler_path=POPPLER_PATH,
        )[0]
        import pytesseract
        pytesseract.pytesseract.tesseract_cmd = (
            r"D:\ProgramFile86\Tesseract\tesseract.exe"
        )

        page_text = pytesseract.image_to_string(image, lang="vie")

        text += f"\n===== TRANG {page_num} =====\n"
        text += page_text

    return text

import asyncio
async def extract_text_from_pdf_async(pdf_bytes: bytes) -> str:
    return await asyncio.to_thread(
        extract_text_from_pdf,
        pdf_bytes
    )


def extract_text(source: Any, filename: Optional[str] = None) -> str:
    """
    Trích xuất văn bản từ file người dùng tải lên.
    Hỗ trợ PDF (OCR), DOCX, TXT và JSON.
    """
    data = source.read() if not isinstance(source, bytes) else source

    # Ưu tiên phần mở rộng của tên file, sau đó tới tên file trên UploadFile.
    suffix = Path(filename or getattr(source, "filename", "") or "").suffix.lower()

    if suffix == ".pdf":
        return extract_text_from_pdf(data)

    if suffix == ".docx":
        from docx import Document

        document = Document(io.BytesIO(data))
        return "\n".join(paragraph.text for paragraph in document.paragraphs)

    if suffix in (".txt", ".json"):
        return data.decode("utf-8", errors="ignore")

    # Không xác định được định dạng: thử đọc UTF-8, nếu lỗi thì coi là PDF.
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return extract_text_from_pdf(data)
    

async def extract_ner_rel(criteria_file: Any):
    #Đọc dữ liệu vào từ API gửi
    text = await extract_text_from_pdf_async(criteria_file)

    #Chunking theo cấu trúc Điều - Khoản - Điểm
    from app.pipe_line.preprocessing import structure_base_chunk, build_structure, context_inheritance
    articles = structure_base_chunk(text)
    results_chunking = []
    for (_, article) in enumerate(articles):
        article = build_structure(article)
        results_chunking.append(article)

    #Kế thừa ngữ nghĩa
    text_chunks, article_ids = context_inheritance(results_chunking)
    output_path = "./app/result/chunking/results_chunking.json"
    _save_output(payload=text_chunks, output_file=output_path)


    #Tách câu đơn bằng mô hình Vi-T5 đã fine-tune
    from app.pipe_line.load_model_simplify import load_model, simplify
    model, tokenizer = load_model()
    splited_results = []
    count = 0
    for chunk in text_chunks:
        answer = simplify(chunk["text"], tokenizer, model)
        answer = {
            "text": answer,
            "article_id": chunk["article_id"],
            "section_id": chunk["section_id"],
            "point_label": chunk["point_label"]
        }
        splited_results.append(answer)
        if count <= 5:
            count += 1
            print(answer)


    #Lọc câu bằng mô hình FastText
    from app.pipe_line.filter_sentences import filter
    filtered_chunk = filter(data=splited_results)
    output_path = "./app/result/filter_sentences/splited_results.json"
    _save_output(payload=filtered_chunk, output_file=output_path)


    #trích xuất thực thể và quan hệ bằng mô hình GLiNER
    from app.pipe_line.ner_rel_extractrion import excute_predict
    results_ner_rel = excute_predict(filtered_chunk)
    output_path = "./app/result/ner_rel/gliner_predict.json"
    _save_output(payload=results_ner_rel, output_file=output_path)


    #Trả về kết quả trích xuất thực thể và quan hệ
    return results_ner_rel, article_ids




