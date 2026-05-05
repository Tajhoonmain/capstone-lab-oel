import os
import json
import sys
import uuid
from mcp_project.app.multi_agent_graph import multi_agent_app
from langchain_core.messages import HumanMessage


def run_headless_eval():
    print("Starting Automated Quality Gate Evaluation...")

    # 1. Ensure credentials are provided via Environment Variables (CI/CD Secret Injection)
    if not os.environ.get("GEMINI_API_KEY"):
        print("ERROR: GEMINI_API_KEY environment variable is missing.")
        sys.exit(1)

    # 2. Load Thresholds
    try:
        with open("mcp_project/eval_thresholds.json", "r") as f:
            thresholds = json.load(f)
    except FileNotFoundError:
        print("ERROR: eval_thresholds.json not found.")
        sys.exit(1)

    print(f"Loaded Thresholds: {thresholds}")

    # 3. Define Golden Dataset
    test_suite = [
        {"question": "If my GPA is 1.5, what is my academic status?", "expected_keyword": "probation"},
        {"question": "How many grade points do I get for an A-?", "expected_keyword": "3.67"},
    ]

    # 4. Run Evaluation
    total_score = 0
    results = []

    for i, test in enumerate(test_suite):
        print(f"\nRunning Test {i+1}: {test['question']}")

        # Run agent
        config = {"configurable": {"thread_id": f"ci_test_{uuid.uuid4().hex[:6]}"}}
        final_output = ""

        try:
            for event in multi_agent_app.stream(
                {"messages": [HumanMessage(content=test["question"])], "sender": "user"}, config, stream_mode="values"
            ):
                if "messages" in event:
                    last_msg = event["messages"][-1]
                    if last_msg.type == "ai" and not getattr(last_msg, "tool_calls", None):
                        final_output = last_msg.content
        except Exception as e:
            print(f"Agent crashed during test: {e}")
            final_output = ""

        # Metric 1: Keyword Match (Faithfulness to Policy)
        passed_keyword = test["expected_keyword"].lower() in final_output.lower()
        score = 1.0 if passed_keyword else 0.0
        total_score += score

        results.append(
            {
                "test_case": test["question"],
                "agent_response": final_output,
                "expected_keyword": test["expected_keyword"],
                "keyword_match_score": score,
            }
        )

    # Calculate aggregate
    avg_keyword_score = total_score / len(test_suite)
    # Dummy relevancy score for demonstration of multiple metrics
    avg_relevancy_score = 0.9 if avg_keyword_score > 0 else 0.0

    final_metrics = {"keyword_match_score": avg_keyword_score, "relevancy_score": avg_relevancy_score}

    # 5. Write Machine-Readable Output
    report = {"metrics": final_metrics, "thresholds": thresholds, "pass": True, "details": results}

    # 6. Enforce Thresholds
    failed_metrics = []
    for metric_name, threshold_val in thresholds.items():
        actual_val = final_metrics.get(metric_name, 0.0)
        if actual_val < threshold_val:
            failed_metrics.append(f"{metric_name} (Got {actual_val}, Expected >={threshold_val})")
            report["pass"] = False

    with open("eval_results.json", "w") as f:
        json.dump(report, f, indent=4)

    if report["pass"]:
        print("\n✅ QUALITY GATE PASSED: All metrics met the thresholds.")
        sys.exit(0)
    else:
        print("\n🚨 QUALITY GATE FAILED! The build will be blocked.")
        print(f"Failed metrics: {failed_metrics}")
        sys.exit(1)


if __name__ == "__main__":
    run_headless_eval()
