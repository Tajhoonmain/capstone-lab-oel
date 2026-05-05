from mcp_project.app.graph import app
from langchain_core.messages import HumanMessage
import os
from dotenv import load_dotenv

load_dotenv()


def test_query(query: str):
    print(f"\n--- Testing Query: {query} ---")
    inputs = {"messages": [HumanMessage(content=query)]}
    for output in app.stream(inputs):
        for key, value in output.items():
            print(f"Node: {key}")
            # print(value) # Full state

    # We already have the final output from the stream loop
    if "messages" in value:
        print("\nFinal Answer:")
        print(value["messages"][-1].content)


if __name__ == "__main__":
    # Test 1: Tool Usage (GPA)
    test_query("I got an A, B, and A. What is my GPA?")

    # Test 2: RAG Usage
    test_query("What is the policy on plagiarism?")

    # Test 3: Complex Reasoning
    test_query("If I got a C in AI407, what is my GPA, and when is the exam for that course?")
