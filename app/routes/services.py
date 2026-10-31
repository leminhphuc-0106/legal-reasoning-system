from fastapi import FastAPI, UploadFile, File
from app.pipe_line import read_data

app = FastAPI()

@app.post("/api/evaluate")
async def evaluate(
    criteria_file: UploadFile = File(...),
    candidate_files: list[UploadFile] = File(...)
):
    

    return result