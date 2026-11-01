import asyncio

from fastapi import FastAPI, File, HTTPException, UploadFile, APIRouter
from app.pipe_line import read_data
from app.pipe_line.read_data import read_data

router = APIRouter()

@router.post("/api/evaluate")
async def evaluate(
    criteria_file: UploadFile = File(...),
    candidate_files: list[UploadFile] = File(...)
):
    # print(criteria_file.filename)
    # print(candidate_files[0].filename)
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

    criteria_bytes = await criteria_file.read()
    candidate_files_data = [await file.read() for file in candidate_files]

    # Đọc và xử lý các file
    result = await read_data(
        criteria_file=criteria_bytes,
        candidate_files=candidate_files_data
    )

    print("Chờ trong khi xây dựng đồ thị Neo4j...")

    # Import hàm xây dựng Knowledge Graph
    from app.pipe_line.build_graph import build_graph_from_json

    # Xây dựng đồ thị
    status_graph = await build_graph_from_json(result)
    # print("Graph building status:", status_graph)
    await asyncio.sleep(4)
    return {
            "message": "Files received successfully", 
            "criteria_file_size": len(criteria_bytes), 
            "candidate_files_count": len(candidate_files_data),
            **status_graph
        }