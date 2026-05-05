import os
import uuid
from langsmith import Client
from langsmith.evaluation import evaluate
from mcp_project.app.multi_agent_graph import multi_agent_app
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv, find_dotenv

# Ensure environment variables (API Keys) are loaded
load_dotenv(find_dotenv())

# --- 1. Initialize LangSmith Client ---
client = Client()

# --- 2. Define the Target Function ---
# This wrapper adapts our LangGraph agent so LangSmith can feed it dataset questions
def predict_agent_response(inputs: dict) -> dict:
    question = inputs["question"]
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    final_output = ""
    # Run the graph and extract the final message
    for event in multi_agent_app.stream({"messages": [HumanMessage(content=question)], "sender": "user"}, config, stream_mode="values"):
        if "messages" in event:
            last_msg = event["messages"][-1]
            if last_msg.type == "ai" and not getattr(last_msg, "tool_calls", None):
                final_output = last_msg.content
                
    return {"response": final_output}

# --- 3. Define the Evaluator ---
# In production, this might be another LLM ("LLM-as-a-Judge"). For this lab, we use Keyword Matching.
def exact_keyword_match(run, example) -> dict:
    """Grades the agent's response by checking if it contains the required keyword."""
    expected_keyword = example.outputs["expected_keyword"].lower()
    actual_response = run.outputs["response"].lower()
    
    # Score is 1 (Pass) if the keyword is found, 0 (Fail) otherwise
    score = 1 if expected_keyword in actual_response else 0
    return {"key": "keyword_match_score", "score": score}

def run_evaluation():
    # 4. Create a Dataset in LangSmith
    dataset_name = f"Academic Advisor Eval {uuid.uuid4().hex[:6]}"
    print(f"Creating dataset '{dataset_name}' in LangSmith...")
    
    dataset = client.create_dataset(dataset_name=dataset_name, description="Test dataset for Academic Advisor")
    
    # 5. Define "Golden" Test Cases
    examples = [
        (
            {"question": "If my GPA is 1.5, what is my academic status?"},
            {"expected_keyword": "probation"} # Must mention probation
        ),
        (
            {"question": "How many grade points do I get for an A-?"},
            {"expected_keyword": "3.67"} # Must mention 3.67 based on the handbook
        )
    ]
    
    # Upload examples to the dataset
    for input_dict, output_dict in examples:
        client.create_example(inputs=input_dict, outputs=output_dict, dataset_id=dataset.id)
        
    print(f"Dataset created with {len(examples)} examples.")
    print("Running automated evaluation pipeline (this will take a few seconds)...\n")
    
    # 6. Run the Evaluation
    experiment_results = evaluate(
        predict_agent_response,
        data=dataset_name,
        evaluators=[exact_keyword_match],
        experiment_prefix="automated_test",
    )
    
    print("\n✅ Evaluation complete!")
    print("You can view the detailed grading report on your LangSmith dashboard under 'Testing & Datasets'.")

if __name__ == "__main__":
    run_evaluation()
