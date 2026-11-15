#Hàm chạy từ lúc nhận hồ sơ đến khi build được đồ thị
async def flow_build(criteria_file):
    #Đọc dữ liệu đầu vào
    from app.services.legal_document_service import chunk_document, simplify_chunk
    from app.services.legal_document_service import filter_sentence, excute_extraction

    text_chunks, article_ids = await chunk_document(criteria_file=criteria_file)

    splited_results = simplify_chunk(text_chunks=text_chunks)
    filtered_sentences = filter_sentence(data=splited_results)
    extracted_results = excute_extraction(data=filtered_sentences)

    from app.services.graph_service import build_graph
    build_result = await build_graph(samples=extracted_results, article_ids=article_ids)
    return build_result

