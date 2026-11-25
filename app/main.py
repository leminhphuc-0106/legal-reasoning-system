from fastapi import FastAPI
from app.routes import routes
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="He Thong Ho Tro Xet KHen Thuong Hanh Chinh",
    version="1.0.0"
)
# Cấu hình CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router=routes.router)
