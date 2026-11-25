from typing import Any
def generate_controller(candidates: list[dict[str, Any]]):
    from app.services.report_service import load_llm_model, excute_generation
    from app.utils.timing_utils import get_run, start_run

    # Lấy lại bộ đếm thời gian của lượt xét đã tạo ở API /evaluate.
    run_id = next(
        (
            candidate.get("_timing_run_id")
            for candidate in candidates
            if candidate.get("_timing_run_id")
        ),
        None,
    )
    timer = get_run(run_id) or start_run()

    model, tokenizer, device = load_llm_model()
    model.eval()

    results = []
    rows = []
    for candidate in candidates:
        # Bỏ mã lượt chạy nội bộ trước khi đưa vào prompt của Qwen.
        generation_input = {
            key: value
            for key, value in candidate.items()
            if key != "_timing_run_id"
        }
        # Ghi nhận thời gian chạy của Qwen khi sinh báo cáo cho từng hồ sơ.
        with timer.measure("qwen") as qwen_measure:
            report = excute_generation(
                generation_input,
                model,
                tokenizer,
                device
            )
        results.append(report)
        rows.append(timer.build_row(candidate, qwen_measure.elapsed))

    # Lưu thống kê thời gian vào file CSV đặt tên theo ngày giờ chạy.
    timing_file = timer.save(rows) if rows else None

    return {
        "results": results,
        "timing_file": str(timing_file) if timing_file else None
    }
