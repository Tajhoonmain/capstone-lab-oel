import json
from mcp_project.app.output_parser import get_structured_model
from langchain_core.messages import HumanMessage


def test_json_output():
    structured_model = get_structured_model()

    query = "I have a GPA of 1.5. What does the handbook say about my academic standing and what should I do?"
    print(f"USER QUERY: {query}\n")

    # We invoke the model directly (For testing purposes, we skip the tools/vector db here
    # and just give it the prompt. In production, this sits at the very end of the graph.)
    system_prompt = """
    You are an Academic Advisor. 
    A student has a GPA of 1.5. According to the handbook, a GPA below 2.0 puts them on Academic Probation.
    They are only allowed to register for 10-13 credit hours. 
    If it stays below 2.0 for two consecutive semesters, they will be removed from the roll.
    Respond to the student using the structured JSON format.
    """

    messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": query}]

    print("Generating Structured JSON Output...\n")
    response_obj = structured_model.invoke(messages)

    # response_obj is a Pydantic object! We can dump it to JSON or access properties directly:
    print(f"--- Raw Pydantic Object ---")
    print(response_obj)

    print(f"\n--- Beautiful JSON Output (For the Frontend) ---")
    print(json.dumps(response_obj.dict(), indent=4))


if __name__ == "__main__":
    test_json_output()
