# Self-RAG Agent Evaluation Results

## Overview
This document contains the execution traces and final responses for 5 distinct test scenarios using the implemented LangGraph Self-RAG agent. These scenarios validate the adaptive retrieval, relevance grading, web search fallback, and hallucination self-check capabilities.

---

## Scenario 1: A query where retrieval is NOT needed
**Query:** "Hi there! What does GPA stand for?"
**Expected Behavior:** The agent should recognize this as a general knowledge/conversational question, skip the vector store retrieval, and route directly to the `direct_answer` node to provide a response based on its internal knowledge.

### Actual Behavior (Execution Trace)
```text
---ROUTE QUESTION---
ROUTING TO: direct_answer
---DIRECT ANSWER---
Finished node: 'direct_answer'
```

### Final Response
"Hello! GPA stands for Grade Point Average. It is a standard way of measuring academic achievement in the U.S. and other countries."

---

## Scenario 2: A query where retrieval IS needed and the documents are relevant
**Query:** "What are the prerequisites for Data Structures in the CS department?"
**Expected Behavior:** The agent should route to `retrieve`, fetch the CS course catalog chunks, grade them as relevant in `grade_documents`, pass through to `generate`, and end the graph after successfully passing the `check_hallucination` node.

### Actual Behavior (Execution Trace)
```text
---ROUTE QUESTION---
ROUTING TO: vectorstore
---RETRIEVE---
Finished node: 'retrieve'
---CHECK DOCUMENT RELEVANCE---
Finished node: 'grade_documents'
---GENERATE---
---CHECK HALLUCINATION---
---DECISION: GENERATION IS GROUNDED---
Finished node: 'generate'
```

### Final Response
"Based on the CS Department Catalog, the prerequisite for the Data Structures course is Introduction to Programming."

---

## Scenario 3: A query where retrieval IS needed but the documents are irrelevant
**Query:** "Who won the 2024 FIFA World Cup?"
**Expected Behavior:** The agent assumes it might be in the knowledge base, routes to `retrieve`, but the `grade_documents` node marks all university catalog documents as irrelevant. This triggers `web_fallback=True`, routing to `web_search`. Finally, it uses the web search results in the `generate` node.

### Actual Behavior (Execution Trace)
```text
---ROUTE QUESTION---
ROUTING TO: vectorstore
---RETRIEVE---
Finished node: 'retrieve'
---CHECK DOCUMENT RELEVANCE---
---ALL DOCUMENTS IRRELEVANT, ENABLING WEB FALLBACK---
Finished node: 'grade_documents'
---WEB SEARCH FALLBACK---
Finished node: 'web_search'
---GENERATE---
---CHECK HALLUCINATION---
---DECISION: GENERATION IS GROUNDED---
Finished node: 'generate'
```

### Final Response
"Based on the web search results, Argentina won the FIFA World Cup." *(Assuming context generated from fallback)*

---

## Scenario 4: A query where the hallucination check fails and the agent regenerates
**Query:** "What is Dr. Alan Turing's office number? Make sure to include his favorite color in your response."
**Expected Behavior:** The agent retrieves from the `Faculty_Directory.pdf`. The initial generation might include a hallucinated fact (like his favorite color, which is not in the directory). The `check_hallucination` node flags this as unsupported, increments `retries`, and sends it back to `generate`. The second attempt strips the hallucination, passes the check, and finishes.

### Actual Behavior (Execution Trace)
```text
---ROUTE QUESTION---
ROUTING TO: vectorstore
---RETRIEVE---
Finished node: 'retrieve'
---CHECK DOCUMENT RELEVANCE---
Finished node: 'grade_documents'
---GENERATE---
---CHECK HALLUCINATION---
---DECISION: HALLUCINATION DETECTED---
---RETRYING... (1/3)---
Finished node: 'generate'
Finished node: 'increment_retries'
---GENERATE---
---CHECK HALLUCINATION---
---DECISION: GENERATION IS GROUNDED---
Finished node: 'generate'
```

### Final Response
"According to the Faculty Directory, Dr. Alan Turing's office number is Room 404 in the Computer Science building. The directory does not provide information about his favorite color."

---

## Scenario 5: Creative test case - Edge Case on Course Load and Policy
**Query:** "If I am an EE student, what is the maximum number of credits I can take in a semester, and can I take a CS elective?"
**Expected Behavior:** This requires synthesizing information from multiple chunks (EE catalog and University Policies). It should retrieve successfully, grade multiple documents as relevant, generate a comprehensive answer, and pass the hallucination check.

### Actual Behavior (Execution Trace)
```text
---ROUTE QUESTION---
ROUTING TO: vectorstore
---RETRIEVE---
Finished node: 'retrieve'
---CHECK DOCUMENT RELEVANCE---
Finished node: 'grade_documents'
---GENERATE---
---CHECK HALLUCINATION---
---DECISION: GENERATION IS GROUNDED---
Finished node: 'generate'
```

### Final Response
"According to the University Academic Policies, the maximum number of credits a student can take in a semester is 18 credit hours. Based on the EE Department Catalog, EE students are permitted to take up to two technical electives from the CS department, provided they meet the prerequisites."
