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

# Cache model để tránh nạp lại nhiều lần trong cùng tiến trình.
_MODEL_CACHE = {}


# # ---------------------------------------------------------------------------
# # ORCHESTRATOR
# # ---------------------------------------------------------------------------

def _save_output(payload: dict, output_file: Path = OUTPUT_FILE) -> None:
    """Ghi kết quả pipeline ra file JSON."""
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
    print(f"Đã lưu kết quả lọc bằng fasttext vào: {output_file}")

# ---------------------------------------------------------------------------
# 1. NHẬN FILE TỪ API
# ---------------------------------------------------------------------------

def _to_bytes(source: Any) -> bytes:
    """Chuyển nguồn đầu vào (bytes, file object, đường dẫn) về bytes."""
    if source is None:
        return b""

    if isinstance(source, (bytes, bytearray)):
        return bytes(source)

    if isinstance(source, (str, os.PathLike)):
        with open(source, "rb") as file:
            return file.read()

    if hasattr(source, "read"):
        # file object đồng bộ (BytesIO, file đã mở, ...)
        data = source.read()
        if isinstance(data, str):
            return data.encode("utf-8")
        return data

    raise TypeError(f"Không hỗ trợ kiểu dữ liệu đầu vào: {type(source)!r}")


async def _read_upload(file: Any) -> bytes:
    """Đọc nội dung UploadFile của FastAPI (read() là async)."""
    if file is None:
        return b""

    if isinstance(file, (bytes, bytearray)):
        return bytes(file)

    if isinstance(file, (str, os.PathLike)):
        with open(file, "rb") as handle:
            return handle.read()

    if hasattr(file, "read"):
        data = file.read()
        if hasattr(data, "__await__"):
            data = await data
        if isinstance(data, str):
            return data.encode("utf-8")
        return data

    raise TypeError(f"Không hỗ trợ kiểu dữ liệu đầu vào: {type(file)!r}")


def extract_text_from_pdf(pdf_source: Any) -> str:
    """OCR toàn bộ file PDF và trả về văn bản thô."""
    from pdf2image import convert_from_bytes
    from pdf2image.pdf2image import pdfinfo_from_bytes

    pdf_bytes = _to_bytes(pdf_source)

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


def extract_text(source: Any, filename: Optional[str] = None) -> str:
    """
    Trích xuất văn bản từ file người dùng tải lên.
    Hỗ trợ PDF (OCR), DOCX, TXT và JSON.
    """
    data = _to_bytes(source)

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


# # ---------------------------------------------------------------------------
# # 2. CHUNKING THEO CẤU TRÚC ĐIỀU - KHOẢN - ĐIỂM
# # ---------------------------------------------------------------------------

def chunk_text(text: str) -> list[dict]:
    """Chia văn bản pháp luật thành các chunk theo Điều / Khoản / Điểm."""
    from preprocessing import build_structure, structure_base_chunk

    articles = structure_base_chunk(text)

    # Văn bản không có cấu trúc "Điều": giữ nguyên toàn bộ làm một chunk.
    if not articles:
        cleaned = (text or "").strip()
        return [{
            "text": cleaned,
            "article_id": None,
            "section_id": None,
            "point_label": None,
        }] if cleaned else []

    all_chunks = []

    for raw_article in articles:
        article = build_structure(raw_article)
        if not article:
            continue

        article_id = article["article_id"]
        article_text = f"Điều {article_id}: {article['content_art']}"

        if not article["sections"]:
            all_chunks.append({
                "text": article_text,
                "article_id": article_id,
                "section_id": None,
                "point_label": None,
            })
            continue

        for section in article["sections"]:
            section_id = section["section_id"]
            section_text = (
                f"{article_text}\n"
                f"Khoản {section_id}: {section['title_sec']}"
            )

            if not section["points"]:
                all_chunks.append({
                    "text": section_text,
                    "article_id": article_id,
                    "section_id": section_id,
                    "point_label": None,
                })
                continue

            for point in section["points"]:
                chunk_text_value = (
                    f"{section_text}\n"
                    f"Điểm {point['label']}) {point['text']}"
                )
                all_chunks.append({
                    "text": chunk_text_value,
                    "article_id": article_id,
                    "section_id": section_id,
                    "point_label": point["label"],
                })

    print(f"Tổng số chunks: {len(all_chunks)}")
    return all_chunks

# # ---------------------------------------------------------------------------
# # 3. TÁCH CÂU ĐƠN (Vi-T5)
# # ---------------------------------------------------------------------------

def _get_simplify_model(model_path: str = SIMPLIFY_MODEL_PATH):
    """Nạp (và cache) mô hình tách câu đơn."""
    if "simplify" not in _MODEL_CACHE:
        from load_model_simplify import load_model

        _MODEL_CACHE["simplify"] = load_model(model_path)

    return _MODEL_CACHE["simplify"]


def _split_model_output(output: str) -> list[str]:
    """
    Tách kết quả của mô hình thành từng câu đơn.
    Mô hình huấn luyện trả về các câu cách nhau bởi xuống dòng.
    """
    output = (output or "").strip()
    if not output:
        return []

    sentences = [part.strip() for part in re.split(r"[\r\n]+", output) if part.strip()]

    # Trường hợp mô hình trả về nhiều câu trên cùng một dòng.
    if len(sentences) == 1:
        sentences = [
            part.strip(" -")
            for part in re.split(r"(?<=[.!?])\s+", sentences[0])
            if part.strip(" -")
        ]

    return sentences


def split_simple_sentences(
    chunks: Iterable[dict],
    model_path: str = SIMPLIFY_MODEL_PATH,
) -> list[dict]:
    """Dùng mô hình tách câu để biến mỗi chunk thành các câu đơn."""
    from load_model_simplify import simplify

    model, tokenizer = _get_simplify_model(model_path)

    results = []
    for chunk in chunks:
        print("CHUNKING........")
        output = simplify(chunk["text"], tokenizer, model)

        for sentence in _split_model_output(output):
            sample = dict(chunk)
            sample["text"] = sentence
            results.append(sample)

    print(f"Tổng số câu đơn: {len(results)}")
    return results


# # ---------------------------------------------------------------------------
# # 4. LỌC CÂU (FastText)
# # ---------------------------------------------------------------------------

def _get_fasttext_model(model_path: str = FASTTEXT_MODEL_PATH):
    """Nạp (và cache) mô hình FastText phân loại câu giữ/bỏ."""
    if "fasttext" not in _MODEL_CACHE:
        import fasttext

        _MODEL_CACHE["fasttext"] = fasttext.load_model(model_path)

    return _MODEL_CACHE["fasttext"]


def filter_sentences(
    samples: Iterable[dict],
    model_path: str = FASTTEXT_MODEL_PATH,
    keep_label: str = "__label__KEEP",
    min_chars: int = 10,
) -> list[dict]:
    """Giữ lại các câu được mô hình FastText dự đoán là cần giữ."""
    model = _get_fasttext_model(model_path)

    results = []
    for sample in samples:
        text = re.sub(r"\s+", " ", sample.get("text", "")).strip()

        # Bỏ câu rỗng hoặc quá ngắn, đồng thời tránh lỗi FastText với xuống dòng.
        if len(text) < min_chars:
            continue

        labels, probs = model.predict(text)
        if labels and labels[0] == keep_label:
            kept = dict(sample)
            kept["text"] = text
            kept["label"] = labels[0]
            kept["label_score"] = float(probs[0])
            results.append(kept)

    print(f"Số câu sau khi lọc: {len(results)}")
    return results

# # ---------------------------------------------------------------------------
# # 5. TRÍCH XUẤT THỰC THỂ & QUAN HỆ (GLiNER)
# # ---------------------------------------------------------------------------

def _get_gliner_model(model_path: str = GLINER_MODEL_PATH):
    """Nạp (và cache) mô hình GLiNER."""
    if "gliner" not in _MODEL_CACHE:
        from ner_rel_extractrion import load_gliner

        _MODEL_CACHE["gliner"] = load_gliner(model_path)

    return _MODEL_CACHE["gliner"]


def _split_kg_output(result: Any) -> tuple[list, list]:
    """Chuẩn hóa đầu ra của GLiNER về cặp (entities, relations)."""
    if isinstance(result, dict):
        entities = result.get("entities") or result.get("ner") or []
        relations = result.get("relations") or result.get("relation") or []
        return list(entities), list(relations)

    if isinstance(result, (tuple, list)) and len(result) >= 2:
        return list(result[0] or []), list(result[1] or [])

    return [], []


def extract_entities_relations(
    samples: Iterable[dict],
    model_path: str = GLINER_MODEL_PATH,
    entity_threshold: float = 0.5,
    relation_threshold: float = 0.5,
    drop_empty: bool = True,
) -> list[dict]:
    """Trích xuất thực thể và quan hệ cho từng câu đã lọc."""
    from ner_rel_extractrion import predict_kg

    model = _get_gliner_model(model_path)
    from tqdm.auto import tqdm
    results = []
    for sample in tqdm(samples, desc="Dự đoán thực thể và quan hệ: "):
        raw = predict_kg(
            model,
            sample["text"],
            entity_threshold=entity_threshold,
            relation_threshold=relation_threshold,
        )
        entities, relations = _split_kg_output(raw)

        # Bỏ các câu không trích xuất được thực thể hoặc quan hệ.
        if drop_empty and (not entities or not relations):
            continue

        results.append({
            "Origin": sample["text"],
            "article_id": sample.get("article_id"),
            "section_id": sample.get("section_id"),
            "point_label": sample.get("point_label"),
            "entities": entities,
            "relations": relations,
        })

    print(f"Số câu có thực thể và quan hệ: {len(results)}")
    return results


if __name__ == "__main__":
    # pdf_path = "./data/2024-10-2024-QĐ-UBND-TPCT.pdf"
    # text = extract_text(source=pdf_path)
    # all_chunks = chunk_text(text=text)

    # splited_results = split_simple_sentences(chunks=all_chunks, model_path=SIMPLIFY_MODEL_PATH)
    #     # Lưu kết quả vào file JSON
    # output_path = "./app/result/chunking/splited_results.json"
    # os.makedirs(os.path.dirname(output_path), exist_ok=True)
    # with open(output_path, "w", encoding="utf-8") as f:
    #     json.dump(splited_results, f, ensure_ascii=False, indent=4)

    # print(f"Đã lưu kết quả chunking vào: {output_path}")
    input_path = "./app/result/chunking/splited_results.json"
    os.makedirs(os.path.dirname(input_path), exist_ok=True)
    with open(input_path, "r", encoding="utf-8") as f:
        splited_results = json.load(f)

    filtered_chunk = filter_sentences(samples=splited_results)
    output_path = "./app/result/filter_sentences/splited_results.json"
    _save_output(payload=filtered_chunk, output_file=output_path)

    results_ner_rel = extract_entities_relations(samples=filtered_chunk, model_path=GLINER_MODEL_PATH)
    output_path = "./app/result/ner_rel/gliner_predict.json"
    _save_output(payload=results_ner_rel, output_file=output_path)






# def run_pipeline_sync(
#     criteria_source: Any,
#     filename: Optional[str] = None,
#     candidate_files: Optional[Iterable[Any]] = None,
#     output_file: Optional[Path] = OUTPUT_FILE,
#     simplify_model_path: str = SIMPLIFY_MODEL_PATH,
#     fasttext_model_path: str = FASTTEXT_MODEL_PATH,
#     gliner_model_path: str = GLINER_MODEL_PATH,
# ) -> dict:
#     """
#     Phiên bản đồng bộ của pipeline, dùng cho test hoặc gọi từ luồng xử lý nền.

#     Tham số:
#         criteria_source: file pháp luật (bytes / file object / đường dẫn).
#         filename: tên file để xác định định dạng (pdf, docx, txt, ...).
#         candidate_files: danh sách hồ sơ ứng viên (chưa xử lý ở pipeline này).
#     """
#     # Bước 1: nhận và trích xuất văn bản.
#     text = extract_text(criteria_source, filename=filename)
#     print(f"Độ dài văn bản: {len(text)} ký tự")

#     # Bước 2: chunking theo cấu trúc.
#     chunks = chunk_text(text)

#     # Bước 3: tách câu đơn.
#     sentences = split_simple_sentences(chunks, model_path=simplify_model_path)

#     # Bước 4: lọc câu.
#     filtered = filter_sentences(sentences, model_path=fasttext_model_path)

#     # Bước 5: trích xuất thực thể, quan hệ.
#     knowledge = extract_entities_relations(filtered, model_path=gliner_model_path)

#     result = {
#         "filename": filename,
#         "num_chunks": len(chunks),
#         "num_sentences": len(sentences),
#         "num_filtered": len(filtered),
#         "num_knowledge": len(knowledge),
#         "chunks": chunks,
#         "sentences": sentences,
#         "filtered_sentences": filtered,
#         "knowledge": knowledge,
#         "candidate_files": [
#             getattr(file, "filename", str(file)) for file in (candidate_files or [])
#         ],
#     }

#     if output_file is not None:
#         _save_output(result, Path(output_file))
#         print(f"Đã lưu kết quả tại: {output_file}")

#     return result


# async def run_pipeline(
#     criteria_file: Any,
#     candidate_files: Optional[Iterable[Any]] = None,
#     filename: Optional[str] = None,
#     output_file: Optional[Path] = OUTPUT_FILE,
#     simplify_model_path: str = SIMPLIFY_MODEL_PATH,
#     fasttext_model_path: str = FASTTEXT_MODEL_PATH,
#     gliner_model_path: str = GLINER_MODEL_PATH,
# ) -> dict:
#     """
#     Entry point dùng trong route FastAPI.
#     Nhận UploadFile, đọc nội dung rồi chạy toàn bộ pipeline.
#     """
#     criteria_bytes = await _read_upload(criteria_file)
#     resolved_name = filename or getattr(criteria_file, "filename", None)

#     return run_pipeline_sync(
#         criteria_bytes,
#         filename=resolved_name,
#         candidate_files=candidate_files,
#         output_file=output_file,
#         simplify_model_path=simplify_model_path,
#         fasttext_model_path=fasttext_model_path,
#         gliner_model_path=gliner_model_path,
#     )


# # Alias để route có thể gọi tên ngắn gọn.
# evaluate = run_pipeline


# if __name__ == "__main__":
#     # Chạy thử với một file PDF/TXT trong thư mục data.
#     import sys

#     if len(sys.argv) < 2:
#         print("Cách dùng: python -m app.pipe_line.full_pipeline <đường_dẫn_file>")
#         raise SystemExit(1)

#     input_path = sys.argv[1]
#     run_pipeline_sync(input_path, filename=os.path.basename(input_path))
