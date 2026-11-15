#Hàm đánh giá hồ sơ ứng viên
import inspect

def check_coroutines(data, path="root"):
    if inspect.isawaitable(data):
        print(f"[COROUTINE FOUND] {path}: {type(data)}")
        return

    if isinstance(data, dict):
        for key, value in data.items():
            check_coroutines(value, f"{path}.{key}")

    elif isinstance(data, (list, tuple)):
        for i, value in enumerate(data):
            check_coroutines(value, f"{path}[{i}]")