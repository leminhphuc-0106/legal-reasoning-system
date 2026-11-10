async def evaluate_controller(
    criteria_file,
    candidate_files
):
    import json
    from fastapi import File, HTTPException 
    from app.services.ner_rel_extractrion import extract_ner_rel
    from app.services.evaluate_profile import evaluate
    from app.services.build_graph import build_graph_from_json
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
    result_extraction_ner_rel, article_ids = await extract_ner_rel(
        criteria_file=criteria_bytes
    )
    # Xây dựng đồ thị
    status_graph = await build_graph_from_json(result_extraction_ner_rel, article_ids)
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
    # Lưu kết quả JSON
    with open(
        "app/result/predict_profile/predicted_profile.json",
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(candidates, f, ensure_ascii=False, indent=4)

    print("Đã lưu kết quả đánh giá hồ sơ.")

    return {
        "message": "Files received successfully",
        "candidate_files_count": len(candidates),
        "status_graph": status_graph,
        "candidates": candidates
    }

