# Product Requirements Document (PRD)

## Project: Academic Advisor Agent (LangGraph + MCP)

### Problem Statement
Students frequently have complex queries that require both fetching information from academic policies (like course handbooks) and performing specific actions (like calculating a GPA or checking an exam schedule). A standard single-prompt LLM cannot fulfill these needs reliably. We need an agentic architecture that can reason, retrieve domain-specific data, and use external execution tools accurately.

### User Personas
1. **Students**: Need quick answers about their courses, graduation requirements, and scheduling.
2. **Academic Advisors**: Need a reliable tool to cross-reference student inquiries with official policies.

### Success Metrics
1. **Accuracy (Faithfulness & Relevancy)**: The agent must answer based strictly on the retrieved context (no hallucinations) with a target RAGAS score of > 85%.
2. **Tool Execution Accuracy**: The agent must successfully invoke the correct tool (GPA calculation, exam schedule) with valid parameters 95% of the time.
3. **Latency**: The end-to-end response time via streaming should provide first-token feedback under 2 seconds.

### High-Level Architecture
- **Frontend**: React + Vite + Tailwind CSS.
- **API Layer**: FastAPI bridging HTTP to LangGraph.
- **Orchestration**: LangGraph (ReAct Loop) managing an Academic Researcher persona and an Advisor Executor persona.
- **Vector DB**: ChromaDB containing chunked academic policies.
- **External Tools**: Existing MCP tools (`calculate_gpa`, `check_exam_schedule`).
