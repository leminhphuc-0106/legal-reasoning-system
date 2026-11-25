async def evaluate_controller(
    criteria_file,
    candidate_files
):
    import json
    from fastapi import HTTPException 
    from app.services.workflows import flow_evaluate
    from app.utils.timing_utils import start_run
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

    # Bắt đầu ghi nhận thời gian chạy cho lượt xét này.
    timer = start_run()

    #FLOW 1: Xây dựng đồ thị từ file tiêu chí
    criteria_bytes = await criteria_file.read()
    from app.services.workflows import flow_build
    status_graph = await flow_build(criteria_file=criteria_bytes, timer=timer)


    #FLOW 2: ĐÁNH GIÁ HỒ SƠ ỨNG VIÊN
    candidate_files_data = [
        (await file.read()).decode("utf-8")
        for file in candidate_files
    ]
    candidates = []
    for idx, candidate in enumerate(candidate_files_data, start=1):
        # Chạy pipeline đánh giá hồ sơ
        mapped_results, criteria, data_candidate, coverage = flow_evaluate(candidate)
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
            "coverage": coverage,

            # Mã lượt chạy để bước sinh báo cáo ghi chung một file CSV.
            "_timing_run_id": timer.run_id
        }

        candidates.append(candidate_result)
    # Lưu kết quả JSON
    # with open(
    #     "app/result/predict_profile/predicted_profile.json",
    #     "w",
    #     encoding="utf-8"
    # ) as f:
    #     json.dump(candidates, f, ensure_ascii=False, indent=4)
    result = {
        "message": "Files received successfully",
        "candidate_files_count": len(candidates),
        "status_graph": status_graph,
        "candidates": candidates
    }
    from app.utils.controller_utils import check_coroutines
    check_coroutines(result)

    return result
