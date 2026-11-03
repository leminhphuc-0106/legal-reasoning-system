
import json
from pathlib import Path
import re

# Tách dấu chấm và dấu phẩy ở cuối token
def normalize_tokens(tokenized_text):
    tokens = []

    for token in tokenized_text:
        # Ví dụ: "nhân." -> ["nhân", "."]
        #        "nhân," -> ["nhân", ","]
        parts = re.match(r"^(.*?)([.,])$", token)

        if parts and parts.group(1):
            tokens.extend([parts.group(1), parts.group(2)])
        else:
            tokens.append(token)

    return tokens

def convert_sample(sample):
    # 1. Ghép token thành văn bản gốc
    tokens = normalize_tokens(sample["tokenized_text"])
    instruction = " ".join(tokens)

    # 2. Chuyển NER thành entities
    entities = []
    entity_texts = []

    for start, end, label in sample["ner"]:
        # GLiNER sử dụng end inclusive
        entity_text = " ".join(tokens[start:end+1])

        entities.append({
            "text": entity_text,
            "label": label
        })

        entity_texts.append(entity_text)

    # 3. Chuyển relations thành quan hệ dạng văn bản
    relations = []

    for subject_idx, object_idx, predicate in sample["relations"]:
        # Kiểm tra chỉ số entity hợp lệ
        if not (
            0 <= subject_idx < len(entity_texts)
            and 0 <= object_idx < len(entity_texts)
        ):
            raise ValueError(
                f"Relation có chỉ số entity không hợp lệ: "
                f"{subject_idx}, {object_idx}"
            )

        relations.append({
            "subject": entity_texts[subject_idx],
            "predicate": predicate,
            "object": entity_texts[object_idx]
        })

    return {
        "instruction": instruction,
        "response": {
            "entities": entities,
            "relations": relations
        }
    }


def convert_dataset(input_path, output_path):
    input_path = Path(input_path)
    output_path = Path(output_path)

    with input_path.open("r", encoding="utf-8") as f:
        dataset = json.load(f)

    converted = [convert_sample(sample) for sample in dataset]

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(
            converted,
            f,
            ensure_ascii=False,
            indent=2
        )

    print(f"Đã chuyển {len(converted)} mẫu.")
    print(f"File đầu ra: {output_path}")


def format_example(example, prompt, tokenizer):
    response_text = json.dumps(
      example["response"],
      ensure_ascii=False
    )
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": example["instruction"]},
        {"role": "assistant", "content": response_text},
    ]

    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=False
    )

    return {"text": text}
    
