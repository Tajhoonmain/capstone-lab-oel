# Feedback Analysis Report

## Overview
This report provides an analysis of the user feedback collected from the Multi-Agent Academic Advisor. By utilizing the feedback loop, we were able to monitor drift, track the agent's performance, and identify key failure queries.

## Methodology
The feedback system was implemented in the Streamlit UI, allowing users to rate the agent's response as `Good` or `Bad` via dedicated buttons. 
All interactions (user inputs, agent responses, and the feedback label) were logged sequentially into `feedback_log.json`.
The `analyze.py` script was built to parse this log file and provide high-level metrics.

## Analysis Results

* **Total Responses Logged:** 4
* **Total Negative Feedback:** 3

### Top Failed Queries
The following queries repeatedly received `Bad` feedback from users, indicating areas where the agent's logic or retrieval mechanisms failed:

1. `"I got an A in CS101, an A- in MT101, and a C in EE101. Calculate my GPA."` (Failed 2 times)
2. `"Calculate GPA for B+, A-, and C"` (Failed 1 time)

## Observations & Next Steps
It is evident that the primary cause of negative feedback stems from the agent's inability to calculate GPAs for grades with plus (`+`) or minus (`-`) modifiers (e.g., A-, B+). The tool simply returns incorrect calculations or ignores the grades.

**Recommended Action:** Update the dictionary inside the `calculate_gpa_tool` (located in `mcp_project/app/tools.py`) to correctly map `+` and `-` letter grades to their respective GPA points (e.g., A- = 3.7, B+ = 3.3).
