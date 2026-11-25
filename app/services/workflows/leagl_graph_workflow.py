#Hàm chạy từ lúc nhận hồ sơ đến khi build được đồ thị
async def flow_build(criteria_file, timer=None):
    #Đọc dữ liệu đầu vào
    from contextlib import nullcontext
    from app.services.legal_document_service import chunk_document, simplify_chunk
    from app.services.legal_document_service import filter_sentence, excute_extraction

    text_chunks, article_ids = await chunk_document(criteria_file=criteria_file)

    # Ghi nhận thời gian chạy của ViT5 khi tách câu.
    vit5_scope = timer.measure("vit5") if timer else nullcontext()
    with vit5_scope:
        splited_results = simplify_chunk(text_chunks=text_chunks)

    filtered_sentences = filter_sentence(data=splited_results)

    # Ghi nhận thời gian chạy của GLiNER khi trích xuất thực thể và quan hệ.
    gliner_scope = timer.measure("gliner") if timer else nullcontext()
    with gliner_scope:
        extracted_results = excute_extraction(data=filtered_sentences)

    from app.services.graph_service import build_graph
    build_result = await build_graph(samples=extracted_results, article_ids=article_ids)
    return build_result
