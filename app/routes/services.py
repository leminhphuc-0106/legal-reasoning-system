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
    print("Chờ trong khi xây dựng đồ thị Neo4j...")

    # Import hàm xây dựng Knowledge Graph
    from app.pipe_line.build_graph import build_graph_from_json

    # Xây dựng đồ thị
    status_graph = await build_graph_from_json(result)

    results_eval = []
    for candidate in candidate_files_data:
        result = evaluate(candidate)
        results_eval.append(result)
    return {
            "message": "Files received successfully", 
            "candidate_files_count": len(candidate_files_data),
            "status_graph": status_graph,
            "result_eval": results_eval
        }