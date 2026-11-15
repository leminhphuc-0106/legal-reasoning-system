#Hàm chuẩn hóa relation name để phù hợp với quy tắc đặt tên trong Neo4j
def normalize_relation_name(relation_name):
    import re
    ralation_name = re.sub(r"[^A-Za-z0-9_]", "_", relation_name.strip())

    if not relation_name:
        raise ValueError("Relationship type không hợp lệ")

    if not relation_name[0].isalpha():
        relation_name = "REL_" + relation_name
    return relation_name.upper()