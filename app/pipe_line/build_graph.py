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


def build_neo4j_graph(driver, batch_samples, batch_size=1000):
    
    entity_rows = []
    relation_groups = defaultdict(list)

    total_entities = 0
    total_relations = 0
    skipped_relations = 0

    # 1. Duyệt qua từng sample
    for sample in batch_samples:

        entities = sample.get("entities", [])
        relations = sample.get("relations", [])

        article_id = sample.get("article_id")
        section_id = sample.get("section_id")
        point_label = sample.get("point_label")

        # Metadata của relationship
        rel_props = {
            "article_id": article_id,
            "section_id": section_id,
            "point_label": point_label
        }

        rel_props = {
            k: v for k, v in rel_props.items()
            if v is not None
        }

        entity_map = {}

        # 2. Thu thập entity nodes
        for idx, entity in enumerate(entities):
            node_data = {
                "name": entity["text"],
                "type": entity["label"],
                "article_id": rel_props.get("article_id"),
                "section_id": rel_props.get("section_id"),
                "point_label": rel_props.get("point_label")
            }

            # Bổ sung thông tin Điều, Khoản, Điểm
            if entity["label"] == "HINH_THUC_KHEN_THUONG":
                node_data.update({
                    "dieu": sample.get("article_id")
                })

            entity_rows.append(node_data)
            entity_map[idx] = node_data
        total_entities += len(entities)

        # 3. Thu thập relationships
        for relation in relations:

            head = relation["head"]
            tail = relation["tail"]

            h = entity_map.get(head.get("entity_idx"))
            t = entity_map.get(tail.get("entity_idx"))

            if h is None or t is None:
                skipped_relations += 1
                continue

            rel_type = relation["relation"]


            # Kiểm tra tên relationship để tránh Cypher injection
            if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", rel_type):
                raise ValueError(
                    f"Relationship type không hợp lệ: {rel_type}"
                )

            rel_type = normalize_relation_name(rel_type)

            row = {
                "head_name": h["name"],
                "head_type": h["type"],
                "tail_name": t["name"],
                "tail_type": t["type"],
                "props": rel_props
            }

            # Nhóm theo relationship type và tập thuộc tính
            group_key = (
                rel_type,
                tuple(sorted(rel_props.keys()))
            )

            relation_groups[group_key].append(row)

            total_relations += 1

    # 4. Ghi dữ liệu vào Neo4j
    with driver.session() as session:

        # Tạo constraint
        session.run("""
            CREATE CONSTRAINT entity_name_type_unique IF NOT EXISTS
            FOR (e:Entity)
            REQUIRE (e.name, e.type) IS UNIQUE
        """).consume()

        # 5. Batch tạo entity nodes
        for i in range(0, len(entity_rows), batch_size):

            batch = entity_rows[i:i + batch_size]

            session.run("""
                UNWIND $batch AS row
                    MERGE (e:Entity {
                        name: row.name,
                        type: row.type
                    })

                    SET e += row
            """, batch=batch).consume()

        # 6. Batch tạo relationships
        for (rel_type, prop_keys), rows in relation_groups.items():

            # Tạo biểu thức thuộc tính cho MERGE
            prop_conditions = ", ".join(
                f"{key}: row.props.{key}"
                for key in prop_keys
            )

            if prop_conditions:
                relationship_pattern = (
                    f"[r:{rel_type} {{{prop_conditions}}}]"
                )
            else:
                relationship_pattern = f"[r:{rel_type}]"

            cypher = f"""
                UNWIND $batch AS row

                MATCH (h:Entity {{
                    name: row.head_name,
                    type: row.head_type
                }})

                MATCH (t:Entity {{
                    name: row.tail_name,
                    type: row.tail_type
                }})

                MERGE (h)-{relationship_pattern}->(t)
            """

            for i in range(0, len(rows), batch_size):

                batch = rows[i:i + batch_size]

                session.run(
                    cypher,
                    batch=batch
                ).consume()

    print(
        f"""
        Đã build graph thành công!

        Samples: {len(batch_samples)}
        Entities: {total_entities}
        Relations: {total_relations}
        Skipped relations: {skipped_relations}
        """
    )

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


async def build_graph_from_json(samples):
    driver = connect_neo4j()
    if driver is None:
        return {"error": "Không thể kết nối đến cơ sở dữ liệu Neo4j"}
    reset_neo4j_data(driver)

    build_neo4j_graph(driver, samples, batch_size=1000)
    driver.close()
    return {"message": "Đã build graph thành công!"}