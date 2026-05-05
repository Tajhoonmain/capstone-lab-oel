import requests
import json
import sys


def test_streaming_api():
    url = "http://127.0.0.1:8000/chat"
    payload = {
        "query": "I am looking at the BS AI degree plan. I got an A in CS101 and a B+ in MT101. What is my GPA?",
        "thread_id": "api_test_user",
    }

    print(f"Connecting to {url}...\n")
    try:
        # Use stream=True to process Server-Sent Events (SSE) as they arrive
        with requests.post(url, json=payload, stream=True) as response:
            response.raise_for_status()

            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode("utf-8")
                    if decoded_line.startswith("data: "):
                        data = decoded_line[6:]  # Strip 'data: '

                        if data == "[DONE]":
                            print("\n\n[STREAM COMPLETE]")
                            break

                        # Parse the JSON payload
                        event = json.loads(data)
                        node = event.get("node", "unknown").upper()

                        if event["type"] == "tool_call":
                            print(f"\n[{node}] [TOOL]: {event['content']}")
                        else:
                            # Stream the text output live
                            print(f"\n[{node}] [AGENT]:\n{event['content']}")

    except requests.exceptions.ConnectionError:
        print("ERROR: Connection failed. Is the FastAPI server running?")
        print("Run it using: uvicorn mcp_project.main:app --reload")


if __name__ == "__main__":
    test_streaming_api()
