import json
from pathlib import Path

from app.schemas.ai import HybridSearchRequest
from app.services.hybrid_search_service import hybrid_search

PROJECT_ROOT = Path(__file__).resolve().parents[2]
EVALUATION_FILE = PROJECT_ROOT / "data" / "evaluation" / "grocery_retrieval_eval.json"
REPORT_FILE = PROJECT_ROOT / "data" / "evaluation" / "retrieval_report.json"


def evaluate_retrieval():
    cases = json.loads(EVALUATION_FILE.read_text(encoding="utf-8"))
    results = []
    reciprocal_ranks = []
    hits = 0

    for case in cases:
        response = hybrid_search(HybridSearchRequest(query=case["query"], limit=5))
        returned_ids = [product["id"] for product in response["products"]]
        expected_ids = set(case["expected_product_ids"])
        rank = next(
            (index + 1 for index, product_id in enumerate(returned_ids) if product_id in expected_ids),
            None,
        )
        if rank:
            hits += 1
            reciprocal_ranks.append(1 / rank)
        else:
            reciprocal_ranks.append(0)

        results.append(
            {
                "query": case["query"],
                "expected_product_ids": case["expected_product_ids"],
                "returned_product_ids": returned_ids,
                "first_relevant_rank": rank,
            }
        )

    report = {
        "model": "sentence-transformers/all-MiniLM-L6-v2",
        "queries": len(cases),
        "recall_at_5": round(hits / len(cases), 4),
        "mrr_at_5": round(sum(reciprocal_ranks) / len(cases), 4),
        "results": results,
    }
    REPORT_FILE.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({key: report[key] for key in ["queries", "recall_at_5", "mrr_at_5"]}))


if __name__ == "__main__":
    evaluate_retrieval()
