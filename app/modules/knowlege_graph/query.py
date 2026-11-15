# Tìm kiếm các node trong Knowledge Graph có tên tương đồng về mặt ngữ nghĩa với tên đầu vào.
# Sử dụng Vector Index để truy xuất top_k node phù hợp nhất dựa trên embedding và similarity score.
def query_graph(text_name: str, top_k: int = 1, tokenizer=None, embedding_model=None, device=None):

    from app.database.connection import Neo4jConnection
    neo4j = Neo4jConnection()
    driver = neo4j.get_driver()

    if not text_name or not text_name.strip():
        raise ValueError("Tên đầu vào không được để trống.")

    if top_k < 1:
        raise ValueError("top_k phải lớn hơn hoặc bằng 1.")

    from app.modules.knowlege_graph.embedding import get_embedding
    # Tạo embedding cho text đầu vào
    embedding = get_embedding(text_name, tokenizer, embedding_model, device)

    query = """
    CALL db.index.vector.queryNodes(
        'name_embedding',
        $top_k,
        $embedding
    )
    YIELD node, score

    RETURN
        elementId(node) AS node_id,
        node.name AS name,
        node.type AS type,
        node.article_id AS article_id,
        node.section_id AS section_id,
        score

    ORDER BY score DESC
    """

    try:
        with driver.session() as session:

            records = session.run(
                query,
                embedding=embedding,
                top_k=top_k
            )

            return [record.data() for record in records]

    finally:
        driver.close()