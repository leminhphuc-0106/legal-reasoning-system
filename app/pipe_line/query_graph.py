def build_name_embeddings(batch_size=100, tokenizer=None, embedding_model=None, device=None):
    from app.pipe_line.build_graph import connect_neo4j
    from app.pipe_line.embedding import get_embedding
    driver = connect_neo4j()
    try:
        with driver.session() as session:

            # 1. Lấy tất cả node có thuộc tính name
            records = session.run("""
                MATCH (n)
                WHERE n.name IS NOT NULL
                  AND trim(toString(n.name)) <> ''

                RETURN
                    elementId(n) AS node_id,
                    toString(n.name) AS name
            """).data()

            if not records:
                print("Không tìm thấy node nào có thuộc tính name.")
                return

            print(f"Tìm thấy {len(records)} node.")

            # 2. Chia batch và tạo embedding
            for i in range(0, len(records), batch_size):
                batch_records = records[i:i + batch_size]
                rows = []

                for record in batch_records:
                    name = record["name"]
                    embedding = get_embedding(
                        name,
                        tokenizer,
                        embedding_model,
                        device
                    )

                    rows.append({
                        "node_id": record["node_id"],
                        "embedding": embedding
                    })

                # 3. Lưu embedding và gắn label Entity
                session.run("""
                    UNWIND $rows AS row
                    MATCH (n)
                    WHERE elementId(n) = row.node_id
                    SET n:Entity
                    SET n.name_embedding = row.embedding
                """, rows=rows).consume()

    finally:
        driver.close()


def create_vector_index():
    from app.pipe_line.build_graph import connect_neo4j
    driver = connect_neo4j()
    query = """
    CREATE VECTOR INDEX name_embedding IF NOT EXISTS
    FOR (n:Entity)
    ON (n.name_embedding)
    OPTIONS {
        indexConfig: {
            `vector.dimensions`: 384,
            `vector.similarity_function`: 'cosine'
        }
    }
    """
    try:
        with driver.session() as session:
            session.run(query).consume()
    finally:
        driver.close()

# Truy vấn Knowledge Graph dựa trên embedding của tên đầu vào
def query_graph(text_name: str, top_k: int = 1, tokenizer=None, embedding_model=None, device=None):

    from app.pipe_line.build_graph import connect_neo4j

    if not text_name or not text_name.strip():
        raise ValueError("Tên đầu vào không được để trống.")

    if top_k < 1:
        raise ValueError("top_k phải lớn hơn hoặc bằng 1.")

    from app.pipe_line.embedding import get_embedding
    # Tạo embedding cho text đầu vào
    embedding = get_embedding(text_name, tokenizer, embedding_model, device)

    driver = connect_neo4j()

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


def find_criterion(results, type_):
    criteria = []

    # 1. Lấy node có Similarity Score cao nhất
    if not results:
        print("\nKhông tìm thấy node phù hợp.")
        return criteria

    best_result = max(results, key=lambda x: x["score"])
    article_id = best_result["article_id"]

    # 2. Kết nối Neo4j
    from app.pipe_line.build_graph import connect_neo4j

    driver = connect_neo4j()

    cypher = """
        MATCH path = (h:Entity)-[*1..5]->(t:Entity)

        WHERE h.type = $type_
        AND ALL(r IN relationships(path)
            WHERE r.article_id = $article_id)

        RETURN
            [n IN nodes(path) | {
                name: n.name,
                type: n.type
            }] AS nodes,

            [r IN relationships(path) | {
                relation: type(r),
                article_id: r.article_id,
                section_id: r.section_id,
                point_label: r.point_label
            }] AS relations
    """

    try:
        with driver.session() as session:
            result = session.run(
                cypher,
                article_id=article_id,
                type_=type_
            )

            # 3. Thu thập toàn bộ path
            all_paths = []

            for record in result:
                nodes = record["nodes"]
                relations = record["relations"]

                path = []

                for i, rel in enumerate(relations):
                    path.append({
                        "head": nodes[i]["name"],
                        "head_type": nodes[i]["type"],
                        "relation": rel["relation"],
                        "tail": nodes[i + 1]["name"],
                        "tail_type": nodes[i + 1]["type"],
                        "text": (
                            f'{nodes[i]["name"]} '
                            f'{rel["relation"]} '
                            f'{nodes[i + 1]["name"]}'
                        )
                    })

                if path:
                    all_paths.append({
                        "article_id": relations[0]["article_id"],
                        "section_id": relations[0]["section_id"],
                        "point_label": relations[0]["point_label"],
                        "path": path
                    })

        # 4. Kiểm tra path1 có phải tiền tố của path2 không
        def is_prefix(path1, path2):
            if len(path1) >= len(path2):
                return False

            return all(
                (
                    p1["head"],
                    p1["relation"],
                    p1["tail"]
                ) == (
                    p2["head"],
                    p2["relation"],
                    p2["tail"]
                )
                for p1, p2 in zip(path1, path2)
            )

        # 5. Loại bỏ các path dư thừa
        for i, item in enumerate(all_paths):
            current_path = item["path"]

            redundant = any(
                is_prefix(current_path, other["path"])
                and (
                    item["article_id"],
                    item["section_id"],
                    item["point_label"]
                ) == (
                    other["article_id"],
                    other["section_id"],
                    other["point_label"]
                )
                for j, other in enumerate(all_paths)
                if i != j
            )

            if not redundant:
                criteria.append(item)

    finally:
        driver.close()

    return criteria
