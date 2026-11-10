#Hàm kết nối với cơ sở dữ liệu Neo4j
import json
from unicodedata import name

entity_labels = [
    "CA_NHAN", "TO_CHUC", "CO_QUAN_NHA_NUOC", "TAP_THE",
    "HOI_DONG_KHEN_THUONG", "DANH_HIEU_THI_DUA",
    "HINH_THUC_KHEN_THUONG", "THANH_TICH", "DIEU_KIEN",
    "TIEU_CHUAN", "SANG_KIEN", "CONG_TRINH_KHOA_HOC",
    "VAN_BAN_PHAP_LUAT", "DIEU_KHOAN_PHAP_LUAT",
    "THOI_GIAN", "THOI_HAN", "CAP_KHEN_THUONG",
    "QUY_TRINH_KHEN_THUONG"
]

relation_labels = [
    "AP_DUNG_CHO", "DAT_DANH_HIEU", "PHAI_DAT_DANH_HIEU",
    "DAT_TIEU_CHUAN", "DAP_UNG_DIEU_KIEN", "CO_THANH_TICH",
    "CO_SANG_KIEN", "CO_CONG_TRINH_KHOA_HOC",
    "CO_THAM_QUYEN_QUYET_DINH", "DUOC_CONG_NHAN_BOI",
    "CAN_CU_XET_TANG", "DUOC_QUY_DINH_TAI", "BAN_HANH_BOI",
    "KE_THUA_TU", "DUOC_XET_TRONG_THOI_GIAN",
    "DUOC_BINH_XET_THONG_QUA", "THAM_GIA_QUY_TRINH"
]


def connect_neo4j():
    from neo4j import GraphDatabase

    URI = "neo4j+s://5e8a567c.databases.neo4j.io"
    USERNAME = "5e8a567c"
    PASSWORD = "LPht7m3RjZsUvJNGeuiXEt2emHn9o-OHWPtfqcnsWYE"

    driver = GraphDatabase.driver(
        URI,
        auth=(USERNAME, PASSWORD)
    )

    # Kiểm tra kết nối
    try:
        driver.verify_connectivity()
        print("Kết nối Neo4j thành công!")

    except Exception as e:
        print("Kết nối Neo4j thất bại:")
        print(e)

    return driver

#Hàm chuẩn hóa relation name để phù hợp với quy tắc đặt tên trong Neo4j
def normalize_relation_name(name):
    import re
    name = re.sub(r"[^A-Za-z0-9_]", "_", name.strip())

    if not name:
        raise ValueError("Relationship type không hợp lệ")

    if not name[0].isalpha():
        name = "REL_" + name

    return name.upper()

#Hàm xây dựng đồ thị trong Neo4j từ dữ liệu thực thể và quan hệ

import re
from collections import defaultdict



from collections import defaultdict
import re

def prepare_graph_data(batch_samples, article_ids):

    entity_rows = []
    # Ví dụ: [
    # {"name": "Bằng khen", 
    # "type": "KHEN_THUONG", 
    # "article_id": 9, 
    # "section_id": 1
    # }]
    relation_groups = defaultdict(list)
    #   relation_groups = {
    #     (
    #         "AP_DUNG_CHO",
    #         ("article_id", "section_id")
    #     ): [
    #         {
    #             "head_name": "Bằng khen",
    #             "tail_name": "Cá nhân",
    #             "article_id": 9,
    #             "props": {
    #                 "article_id": 9,
    #                 "section_id": 1
    #             }
    #         },
    #         {
    #             "head_name": "Giấy khen",
    #             "tail_name": "Cá nhân",
    #             "article_id": 10,
    #             "props": {
    #                 "article_id": 10,
    #                 "section_id": 2
    #             }
    #         }
    #     ]
    # }

    total_entities = 0
    total_relations = 0
    skipped_relations = 0

    for sample in batch_samples:

        article_id = sample.get("article_id")

        if article_ids and article_id not in article_ids:
            continue

        entities = sample.get("entities", [])
        relations = sample.get("relations", [])

        section_id = sample.get("section_id")
        point_label = sample.get("point_label")

        rel_props = {
            k: v for k, v in {
                "article_id": article_id,
                "section_id": section_id,
                "point_label": point_label
            }.items()
            if v is not None
        }

        entity_map = {}

        # Thu thập entities
        for idx, entity in enumerate(entities):

            node_data = {
                "name": entity["text"],
                "type": entity["label"],
                "article_id": article_id,
                "section_id": section_id,
                "point_label": point_label
            }

            entity_rows.append(node_data)
            entity_map[idx] = node_data

        total_entities += len(entities)

        # Thu thập relationships
        for relation in relations:

            head = relation["head"]
            tail = relation["tail"]

            h = entity_map.get(head.get("entity_idx"))
            t = entity_map.get(tail.get("entity_idx"))

            if h is None or t is None:
                skipped_relations += 1
                continue

            rel_type = relation["relation"]

            if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", rel_type):
                raise ValueError(f"Relationship không hợp lệ: {rel_type}")

            rel_type = normalize_relation_name(rel_type)

            if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", rel_type):
                raise ValueError(f"Relationship sau normalize không hợp lệ: {rel_type}")

            row = {
                "head_name": h["name"],
                "head_type": h["type"],
                "tail_name": t["name"],
                "tail_type": t["type"],
                "article_id": article_id,
                "props": rel_props
            }

            group_key = (
                rel_type,
                tuple(sorted(rel_props.keys()))
            )

            relation_groups[group_key].append(row)
            total_relations += 1

    return {
        "entity_rows": entity_rows,
        "relation_groups": relation_groups,
        "total_entities": total_entities,
        "total_relations": total_relations,
        "skipped_relations": skipped_relations
    }




import re
from collections import defaultdict


def insert_graph_to_neo4j(driver, graph_data, batch_size=1000):

    entity_rows = graph_data["entity_rows"]
    relation_groups = graph_data["relation_groups"]

    # 1. Tạo unique constraint cho node
    with driver.session() as session:

        session.run("""
            CREATE CONSTRAINT entity_unique IF NOT EXISTS
            FOR (n:Entity)
            REQUIRE (n.name, n.type, n.article_id) IS UNIQUE
        """)

        # 2. Insert nodes
        entity_query = """
            UNWIND $rows AS row

            MERGE (n:Entity {
                name: row.name,
                type: row.type,
                article_id: row.article_id
            })
        """

        for i in range(0, len(entity_rows), batch_size):

            batch = entity_rows[i:i + batch_size]

            session.run(entity_query, rows=batch)

        # 3. Insert relationships
        total_inserted = 0

        for (rel_type, prop_keys), relations in relation_groups.items():

            # Kiểm tra tên relationship và property để tránh Cypher injection
            if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", rel_type):
                raise ValueError(f"Invalid relationship type: {rel_type}")

            for key in prop_keys:
                if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key):
                    raise ValueError(f"Invalid property key: {key}")

            # Xây dựng phần khóa của relationship
            merge_props = ", ".join(
                f"{key}: row.props.{key}"
                for key in prop_keys
            )

            merge_pattern = (
                f"{{{merge_props}}}" if merge_props else ""
            )

            relation_query = f"""
                UNWIND $rows AS row

                MATCH (h:Entity {{
                    name: row.head_name,
                    type: row.head_type,
                    article_id: row.article_id
                }})

                MATCH (t:Entity {{
                    name: row.tail_name,
                    type: row.tail_type,
                    article_id: row.article_id
                }})

                MERGE (h)-[r:{rel_type} {merge_pattern}]->(t)

                SET r += row.props
            """

            for i in range(0, len(relations), batch_size):

                batch = relations[i:i + batch_size]

                result = session.run(
                    relation_query,
                    rows=batch
                )

                summary = result.consume()

                total_inserted += summary.counters.relationships_created

    return {
        "total_entities": graph_data["total_entities"],
        "total_relations": graph_data["total_relations"],
        "skipped_relations": graph_data["skipped_relations"],
        "relationships_created": total_inserted
    }




#Hàm reset toàn bộ dữ liệu trong cơ sở dữ liệu Neo4j
def delete_all_data(tx):
    tx.run("""
        MATCH (n)
        DETACH DELETE n
    """)

def reset_neo4j_data(driver):
    try:
        with driver.session() as session:
            session.execute_write(delete_all_data)

        print("Đã xóa toàn bộ dữ liệu Neo4j!")

    except Exception as e:
        print("Xóa dữ liệu Neo4j thất bại:")
        print(e)


async def build_graph_from_json(samples, article_ids):
    driver = connect_neo4j()
    if driver is None:
        return {"error": "Không thể kết nối đến cơ sở dữ liệu Neo4j"}
    reset_neo4j_data(driver)

    graph_data = prepare_graph_data(
        samples,
        article_ids
    )

    # Bước 2: Ghi vào Neo4j
    insert_graph_to_neo4j(
        driver,
        graph_data
    )
    driver.close()
    return {"message": "Đã build graph thành công!"}