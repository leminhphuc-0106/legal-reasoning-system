# Ghi nhận thời gian chạy của các mô hình (ViT5, GLiNER, Qwen) theo từng lượt xét hồ sơ.
# Mỗi lượt chạy tương ứng một file CSV đặt tên theo ngày giờ bắt đầu chạy.
import csv
import time
from datetime import datetime
from pathlib import Path
from threading import Lock

TIMING_DIR = Path(__file__).resolve().parents[1] / "result" / "timings"

CSV_HEADERS = [
    "thoi_gian_chay",
    "ma_ho_so",
    "ten_ho_so",
    "vit5_giay",
    "gliner_giay",
    "qwen_giay",
    "tong_giay",
]

_COMPONENTS = ("vit5", "gliner", "qwen")

_runs: dict[str, "RunTimer"] = {}
_registry_lock = Lock()


class _Measure:
    """Đo thời gian một khối lệnh và cộng dồn vào timer."""

    def __init__(self, timer: "RunTimer", component: str):
        self.timer = timer
        self.component = component
        self.elapsed = 0.0
        self._start = 0.0

    def __enter__(self):
        self._start = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.elapsed = time.perf_counter() - self._start
        self.timer.add(self.component, self.elapsed)
        return False


class RunTimer:
    """Bộ đếm thời gian cho một lượt xét hồ sơ."""

    def __init__(self, run_id: str | None = None):
        started_at = datetime.now()
        self.started_at = started_at
        self.run_id = run_id or self._build_run_id(started_at)
        self._durations = {component: 0.0 for component in _COMPONENTS}
        self._lock = Lock()

    @staticmethod
    def _build_run_id(started_at: datetime) -> str:
        # Tên file là ngày giờ chạy, thêm mili giây để tránh trùng khi chạy liên tiếp.
        base = started_at.strftime("%Y%m%d_%H%M%S")
        candidate = f"{base}_{started_at.microsecond // 1000:03d}"
        run_id = candidate
        index = 1
        while (TIMING_DIR / f"{run_id}.csv").exists():
            run_id = f"{candidate}_{index}"
            index += 1
        return run_id

    def measure(self, component: str) -> _Measure:
        return _Measure(self, component)

    def add(self, component: str, seconds: float) -> None:
        with self._lock:
            self._durations[component] = self._durations.get(component, 0.0) + seconds

    def get(self, component: str) -> float:
        with self._lock:
            return self._durations.get(component, 0.0)

    def snapshot(self) -> dict[str, float]:
        with self._lock:
            return dict(self._durations)

    def csv_path(self) -> Path:
        return TIMING_DIR / f"{self.run_id}.csv"

    def save(self, rows: list[dict]) -> Path:
        """Ghi các dòng thống kê vào file CSV của lượt chạy này."""
        TIMING_DIR.mkdir(parents=True, exist_ok=True)
        path = self.csv_path()
        with self._lock:
            file_exists = path.exists() and path.stat().st_size > 0
            with path.open("a", encoding="utf-8", newline="") as file:
                writer = csv.DictWriter(file, fieldnames=CSV_HEADERS)
                if not file_exists:
                    writer.writeheader()
                writer.writerows(rows)
        return path

    def build_row(self, candidate: dict, qwen_seconds: float) -> dict:
        vit5_seconds = self.get("vit5")
        gliner_seconds = self.get("gliner")
        total_seconds = vit5_seconds + gliner_seconds + qwen_seconds
        return {
            "thoi_gian_chay": self.started_at.strftime("%Y-%m-%d %H:%M:%S"),
            "ma_ho_so": candidate.get("id", ""),
            "ten_ho_so": candidate.get("name", ""),
            "vit5_giay": round(vit5_seconds, 3),
            "gliner_giay": round(gliner_seconds, 3),
            "qwen_giay": round(qwen_seconds, 3),
            "tong_giay": round(total_seconds, 3),
        }


def start_run() -> RunTimer:
    """Bắt đầu một lượt chạy mới và lưu vào registry để dùng lại ở bước sau."""
    timer = RunTimer()
    with _registry_lock:
        _runs[timer.run_id] = timer
    return timer


def get_run(run_id: str | None) -> RunTimer | None:
    if not run_id:
        return None
    with _registry_lock:
        return _runs.get(run_id)
