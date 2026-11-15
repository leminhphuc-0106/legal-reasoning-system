from typing import Any
def generate_controller(candidates: list[dict[str, Any]]):
    from app.services.report_service import load_llm_model, excute_generation

    model, tokenizer, device = load_llm_model()
    model.eval()

    results = []
    for candidate in candidates:
        report = excute_generation(
            candidate,
            model,
            tokenizer,
            device
        )
        results.append(report)

    return {"results": results}