import os
from pathlib import Path
from typing import Any

from app.modules.document_processing import simplify_chunk, filter_sentence
from app.modules.ner_rel_extraction import excute_extraction

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

import asyncio
async def extract_text_from_pdf_async(pdf_bytes: bytes) -> str:
    from app.modules.document_processing import extract_text_from_pdf
    return await asyncio.to_thread(
        extract_text_from_pdf,
        pdf_bytes
    )
    

async def chunk_document(criteria_file: Any):
    #Đọc dữ liệu vào từ API gửi
    text = await extract_text_from_pdf_async(criteria_file)

    #Chunking theo cấu trúc Điều - Khoản - Điểm
    from app.modules.document_processing import structure_base_chunk, build_structure, context_inheritance
    articles = structure_base_chunk(text)
    results_chunking = []
    for (_, article) in enumerate(articles):
        article = build_structure(article)
        results_chunking.append(article)

    #Kế thừa ngữ nghĩa
    text_chunks, article_ids = context_inheritance(results_chunking)
    output_path = "./app/result/chunking/results_chunking.json"
    # _save_output(payload=text_chunks, output_file=output_path)
    return text_chunks, article_ids



