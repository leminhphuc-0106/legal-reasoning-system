from typing import Any
def generate_controller(candidates: list[dict[str, Any]]):
    from app.services.generate_report import load_llm_model, run

    model, tokenizer, device = load_llm_model()
    model.eval()

    results = []
    for candidate in candidates:
        report = run(
            candidate,
            model,
            tokenizer,
            device
        )
        results.append(report)

    return {"results": results}