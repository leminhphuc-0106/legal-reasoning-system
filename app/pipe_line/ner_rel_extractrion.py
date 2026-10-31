def load_gliner(model_path):
    from gliner import GLiNER
    import torch
    model_path = (
        "./models/GLiNER-Model"
    )

    device = "cuda" if torch.cuda.is_available() else "cpu"

    model = GLiNER.from_pretrained(model_path)
    model = model.to(device)
    return model


# 4. Hàm dự đoán Entity + Relation
def predict_kg(model, text, entity_threshold=0.5, relation_threshold=0.5):
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
    result = model.predict_relations(
        text,
        labels=entity_labels,
        relations=relation_labels,
        threshold=entity_threshold,
        relation_threshold=relation_threshold
    )
    return result


def excute_predict(data):
    results = []
    from tqdm.auto import tqdm
    for sample in tqdm(data, desc="Predict KG"):
        sentence = sample["text"]
        result = predict_kg(sentence)
        results.append(result)
    return results


def filter_results(results, data):
    samples = []

    for index, result in enumerate(results):
        entities = result[0]
        relations = result[1]

        # Bỏ qua câu không có entity hoặc relation
        if len(entities) == 0 or len(relations) == 0:
            continue

        # Thêm kết quả vào samples
        sample = {
            "Origin": data[index]["text"],
            "article_id": data[index]["article_id"],
            "section_id": data[index]["section_id"],
            "point_label": data[index]["point_label"],
            "entities": entities,
            "relations": relations
        }
        samples.append(sample)

    return samples