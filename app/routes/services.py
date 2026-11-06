import asyncio
import json

from fastapi import FastAPI, File, HTTPException, UploadFile, APIRouter
from app.pipe_line import read_data
from app.pipe_line.read_data import read_data
from app.pipe_line.evaluate_profile import evaluate
router = APIRouter()

@router.post("/api/evaluate")
async def evaluate_api(
    criteria_file: UploadFile = File(...),
    candidate_files: list[UploadFile] = File(...)
):
    #Kiểm tra file đầu vào
    if not candidate_files:
        raise HTTPException(
            status_code=400,
            detail="Không có danh sách ứng viên, vui lòng nhập"
        )

    if criteria_file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="File tiêu chí phải là PDF"
        )

    #Đọc nội dung file tiêu chí và danh sách file ứng viên
    criteria_bytes = await criteria_file.read()
    candidate_files_data = [
        (await file.read()).decode("utf-8")
        for file in candidate_files
    ]

    # Đọc và xử lý file luật trước
    result = await read_data(
        criteria_file=criteria_bytes
    )
    print("Chờ trong khi xây dựng đồ thị...")

    # Import hàm xây dựng Knowledge Graph
    from app.pipe_line.build_graph import build_graph_from_json

    # Xây dựng đồ thị
    status_graph = await build_graph_from_json(result)
    candidates = []

    for idx, candidate in enumerate(candidate_files_data, start=1):
        # Chạy pipeline đánh giá hồ sơ
        mapped_results, criteria, data_candidate, coverage = evaluate(candidate)
        # Tạo ID cho hồ sơ
        candidate_id = f"HS{idx:02d}"
        # Tên đối tượng xét thưởng
        candidate_name = (
            data_candidate.get("DOI_TUONG", f"Hồ sơ {candidate_id}")
        )
        # Ghép toàn bộ dữ liệu vào một hồ sơ
        candidate_result = {
            "id": candidate_id,
            "name": candidate_name,

            # Thông tin đã trích xuất từ hồ sơ
            "data": data_candidate,

            # Kết quả mapping với Knowledge Graph
            "mapped_results": mapped_results,

            # Các tiêu chí pháp lý tìm được
            "criteria": criteria,
            "coverage": coverage
        }

        candidates.append(candidate_result)

    # Cấu trúc kết quả tổng hợp
    output = {
        "candidates": candidates
    }

    # Lưu kết quả JSON
    with open(
        "app/result/predict_profile/predicted_profile.json",
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(output, f, ensure_ascii=False, indent=4)

    print("Đã lưu kết quả đánh giá hồ sơ.")

    return {
        "message": "Files received successfully",
        "candidate_files_count": len(candidates),
        "status_graph": status_graph,
        "candidates": candidates
    }
