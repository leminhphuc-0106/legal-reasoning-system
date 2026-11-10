from fastapi import File, UploadFile, APIRouter
from typing import Any
from app.controllers.evaluate import evaluate_controller
from app.controllers.generate_report import generate_controller

router = APIRouter(
    prefix="/api"
)

@router.post("evaluate")
async def evaluate(
    criteria_file: UploadFile = File(...),
    candidate_files: list[UploadFile] = File(...)
):
    result = await evaluate_controller(criteria_file=criteria_file, candidate_files=candidate_files)
    return result


@router.post("/generate-report")
def generate_report(candidates: list[dict[str, Any]]):
    result = generate_controller(candidates=candidates)
    return result