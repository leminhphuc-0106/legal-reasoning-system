# Thực hiện quy trình đánh giá hồ sơ ứng viên dựa trên dữ liệu thành tích và các quy định pháp lý trong Knowledge Graph.
# Kết hợp embedding, truy vấn vector, trích xuất tiêu chí, ánh xạ dữ liệu và thống kê mức độ bao phủ tiêu chí.
def flow_evaluate(text = """Cá nhân: Đinh Thị O
    Loại xét: Khen thưởng - Bằng khen của Chủ tịch UBND thành phố
    Thời điểm xét: tháng 08/2024
    Danh hiệu thi đua: Lao động tiên tiến 2022 - 2023; Lao động tiên tiến 2023 - 2024
    Kết quả đánh giá: Hoàn thành xuất sắc nhiệm vụ 2022 - 2023; Hoàn thành xuất sắc nhiệm vụ 2023 - 2024
    Hình thức khen thưởng: Giấy khen của Hiệu trưởng 2022 - 2023; Giấy khen của Hiệu trưởng 2023 - 2024
    Sáng kiến NCKH: 02 sáng kiến được công nhận có hiệu quả áp dụng và phạm vi ảnh hưởng ở cơ sở trong năm học 2022 - 2023 và 2023 - 2024
    """, ):
    from app.utils.evaluate_utils import parse_text_to_dict
    data = parse_text_to_dict(text)
    award = data["LOAI_XET"]
    type_ = data["LOAI_DOI_TUONG"]

    # 1. Khởi tạo model và tokenizer
    from app.services.graph_service import load_embedding_model, build_name_embeddings, create_vector_index
    embedding_model, tokenizer, device = load_embedding_model()
    # 2. Tạo embedding cho tất cả node trong Neo4j
    build_name_embeddings(
        batch_size=100,
        tokenizer=tokenizer,
        embedding_model=embedding_model,
        device=device
    )

    # 3. Tạo Vector Index
    create_vector_index()

    # 4. Thử nghiệm truy vấn Knowledge Graph
    from app.services.graph_service import query_graph
    results = query_graph(
        text_name=award,
        top_k=5,
        tokenizer=tokenizer,
        embedding_model=embedding_model,
        device=device
    )

    print(f"\nKết quả truy vấn cho: {award}")

    for i, result in enumerate(results, start=1):
        print(f"\nKết quả {i}:")
        print(f"Node ID: {result['node_id']}")
        print(f"Name: {result['name']}")
        print(f"Type: {result['type']}")
        print(f"Article ID: {result['article_id']}")
        print(f"Section ID: {result['section_id']}")
        print(f"Similarity Score: {result['score']:.4f}")
    from app.services.graph_service import find_criterion, map_data_to_criteria, evaluate_criterion_coverage
    criteria = find_criterion(results=results, type_=type_)

    # Mapping dữ liệu hồ sơ với tiêu chí
    mapped_results = map_data_to_criteria(
        data=data,
        criteria=criteria,
        model=embedding_model,
        tokenizer=tokenizer,
        device=device,
        threshold=0.65
    )

    coverage = evaluate_criterion_coverage(
        criteria=criteria,
        mapped_results=mapped_results
    )

    return mapped_results, criteria, data, coverage