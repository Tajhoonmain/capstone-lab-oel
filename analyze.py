import json
import os
from collections import Counter

def analyze_feedback():
    log_file = "feedback_log.json"
    
    if not os.path.exists(log_file):
        print(f"Error: {log_file} does not exist.")
        return

    with open(log_file, "r") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            print("Error: Invalid JSON format in feedback log.")
            return
            
    total_responses = len(data)
    
    negative_feedbacks = [entry for entry in data if entry.get("feedback") == "Bad"]
    total_negative = len(negative_feedbacks)
    
    # Top 3 failed queries (based on exact match of user_input for bad feedback)
    failed_queries = [entry.get("user_input") for entry in negative_feedbacks if entry.get("user_input")]
    query_counts = Counter(failed_queries)
    top_3_failed = query_counts.most_common(3)
    
    print("=" * 40)
    print("        FEEDBACK ANALYSIS REPORT        ")
    print("=" * 40)
    print(f"Total Responses Logged: {total_responses}")
    print(f"Total Negative Feedback: {total_negative}")
    
    print("\nTop 3 Failed Queries:")
    if not top_3_failed:
        print("  None found!")
    else:
        for i, (query, count) in enumerate(top_3_failed, 1):
            print(f"  {i}. \"{query}\" (Failed {count} times)")
    print("=" * 40)

if __name__ == "__main__":
    analyze_feedback()
