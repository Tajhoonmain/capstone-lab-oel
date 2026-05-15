# Drift Improvement Demo

## Issue Identification
During the post-deployment monitoring phase, our feedback loop caught a recurring issue reported by users. The system was frequently receiving `Bad` feedback for queries involving GPA calculation. 

By running `analyze.py`, we identified that the `calculate_gpa` tool failed whenever a user provided grades with modifiers (such as `A-`, `B+`, `C-`).

### Root Cause
The `grade_points` dictionary inside `mcp_project/app/tools.py` only accounted for standard grades (`A`, `B`, `C`, `D`, `F`). If a student input an `A-`, the dictionary returned `None`, and the tool ignored the grade entirely, resulting in wildly inaccurate GPA calculations.

---

## Before Fix

**User Query:** `"I got an A in CS101, an A- in MT101, and a C in EE101. Calculate my GPA."`

**Agent Execution:**
* Extract grades: `["A", "A-", "C"]`
* GPA Tool point mapping: `A -> 4`, `A- -> None`, `C -> 2`
* The tool ignored the `A-` and calculated the GPA using only `A` and `C` ($4+2 = 6 / 2 = 3.0$).

**Agent Response:** `The calculated GPA for grades ['A', 'A-', 'C'] is 3.0.` *(Incorrect!)*

---

## The Fix
We updated the `calculate_gpa_tool` logic to support plus and minus modifiers. 

```python
grade_points = {
    "A+": 4.0, "A": 4.0, "A-": 3.7,
    "B+": 3.3, "B": 3.0, "B-": 2.7,
    "C+": 2.3, "C": 2.0, "C-": 1.7,
    "D+": 1.3, "D": 1.0, "F": 0.0
}
```

---

## After Fix

**User Query:** `"I got an A in CS101, an A- in MT101, and a C in EE101. Calculate my GPA."`

**Agent Execution:**
* Extract grades: `["A", "A-", "C"]`
* GPA Tool point mapping: `A -> 4.0`, `A- -> 3.7`, `C -> 2.0`
* Total points: $4.0 + 3.7 + 2.0 = 9.7$
* Average: $9.7 / 3 = 3.23$

**Agent Response:** `The calculated GPA for grades ['A', 'A-', 'C'] is 3.23.` *(Correct!)*

## Conclusion
By monitoring the feedback loop, we quickly identified an edge-case missing from our tools, corrected the logic, and drastically improved the accuracy of the agent. This highlights the importance of continuous monitoring in LLM agentic applications.
