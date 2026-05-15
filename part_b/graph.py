import operator
from typing import TypedDict, Annotated, List, Dict, Any, Sequence
from langchain_core.messages import BaseMessage
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END
from tools import web_search_tool

# --- State Definition ---
class AgentState(TypedDict):
    question: str
    generation: str
    documents: List[Document]
    web_fallback: bool
    retries: int

# --- Pydantic Models for Structured Output ---
class RouteQuery(BaseModel):
    """Route query to web search, vectorstore, or direct answer."""
    route: str = Field(
        description="Given a user question, choose to route it to 'vectorstore', or 'direct_answer'."
    )

class GradeDocuments(BaseModel):
    """Binary score for relevance check on retrieved documents."""
    binary_score: str = Field(
        description="Documents are relevant to the question, 'yes' or 'no'"
    )

class GradeHallucination(BaseModel):
    """Binary score for hallucination present in generation answer."""
    binary_score: str = Field(
        description="Answer is grounded in the facts, 'yes' or 'no'"
    )

class GradeAnswer(BaseModel):
    """Binary score to assess if answer addresses question."""
    binary_score: str = Field(
        description="Answer addresses the question, 'yes' or 'no'"
    )

# --- Graph Builder Class ---
class SelfRAGGraph:
    def __init__(self, llm, retriever):
        self.llm = llm
        self.retriever = retriever
        self.max_retries = 3

        # Prompts
        self.router_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert at routing a user question to a vectorstore or direct answer. "
                       "If the question is a conversational greeting (e.g., 'Hi', 'Hello') or general knowledge (e.g., 'What is GPA?'), route to 'direct_answer'. "
                       "If it requires specific university catalog information (courses, policies, faculty), route to 'vectorstore'."),
            ("human", "{question}")
        ])

        self.grader_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a grader assessing relevance of a retrieved document to a user question. "
                       "If the document contains keywords or semantic meaning related to the question, grade it as relevant. "
                       "Give a binary score 'yes' or 'no' to indicate relevance."),
            ("human", "Retrieved document: \n\n {document} \n\n User question: {question}")
        ])

        self.generate_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a university advisory assistant. Answer the question based ONLY on the following context. "
                       "If the context is empty, you can use general knowledge if appropriate, or say you don't know.\n\n"
                       "Context: {context}"),
            ("human", "Question: {question}")
        ])

        self.hallucination_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a grader assessing whether an LLM generation is grounded in / supported by a set of retrieved facts. "
                       "Give a binary score 'yes' or 'no'. 'yes' means the answer is grounded in facts."),
            ("human", "Set of facts: \n\n {documents} \n\n LLM generation: {generation}")
        ])

    def retrieve(self, state: AgentState):
        """Retrieve documents from vector store."""
        print("---RETRIEVE---")
        question = state["question"]
        documents = self.retriever.invoke(question)
        return {"documents": documents, "question": question}

    def direct_answer(self, state: AgentState):
        """Answer conversational/general questions directly without retrieval."""
        print("---DIRECT ANSWER---")
        question = state["question"]
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a friendly university advisory assistant. Answer the user's conversational or general question directly."),
            ("human", "{question}")
        ])
        chain = prompt | self.llm | StrOutputParser()
        generation = chain.invoke({"question": question})
        return {"generation": generation}

    def grade_documents(self, state: AgentState):
        """Grade retrieved documents for relevance."""
        print("---CHECK DOCUMENT RELEVANCE---")
        question = state["question"]
        documents = state.get("documents", [])
        
        structured_llm_grader = self.llm.with_structured_output(GradeDocuments)
        grade_chain = self.grader_prompt | structured_llm_grader

        filtered_docs = []
        web_fallback = False

        for d in documents:
            score = grade_chain.invoke({"question": question, "document": d.page_content})
            grade = score.binary_score
            if grade.lower() == "yes":
                filtered_docs.append(d)

        if not filtered_docs:
            print("---ALL DOCUMENTS IRRELEVANT, ENABLING WEB FALLBACK---")
            web_fallback = True

        return {"documents": filtered_docs, "web_fallback": web_fallback}

    def web_search(self, state: AgentState):
        """Search the web if vectorstore docs are irrelevant."""
        print("---WEB SEARCH FALLBACK---")
        question = state["question"]
        docs = state.get("documents", [])
        
        web_results = web_search_tool.invoke(question)
        web_doc = Document(page_content=web_results, metadata={"source": "web_search"})
        docs.append(web_doc)
        
        return {"documents": docs, "web_fallback": False}

    def generate(self, state: AgentState):
        """Generate answer using retrieved documents."""
        print("---GENERATE---")
        question = state["question"]
        documents = state.get("documents", [])
        retries = state.get("retries", 0)

        context = "\n\n".join([d.page_content for d in documents])
        chain = self.generate_prompt | self.llm | StrOutputParser()
        generation = chain.invoke({"context": context, "question": question})

        return {"generation": generation, "retries": retries}

    # --- Conditional Edges ---
    def route_question(self, state: AgentState):
        """Route to vectorstore or direct answer."""
        print("---ROUTE QUESTION---")
        question = state["question"]
        
        structured_llm_router = self.llm.with_structured_output(RouteQuery)
        router_chain = self.router_prompt | structured_llm_router
        source = router_chain.invoke({"question": question})
        
        if source.route == "vectorstore":
            print("ROUTING TO: vectorstore")
            return "retrieve"
        else:
            print("ROUTING TO: direct_answer")
            return "direct_answer"

    def decide_to_generate(self, state: AgentState):
        """Decide whether to generate or fallback to web search."""
        if state.get("web_fallback"):
            return "web_search"
        return "generate"

    def check_hallucination(self, state: AgentState):
        """Check if generation is grounded in facts."""
        print("---CHECK HALLUCINATION---")
        question = state["question"]
        documents = state.get("documents", [])
        generation = state["generation"]
        retries = state.get("retries", 0)

        if not documents:
            # If no docs, we can't check for grounding in facts
            return "end"

        structured_llm_grader = self.llm.with_structured_output(GradeHallucination)
        hallucination_chain = self.hallucination_prompt | structured_llm_grader
        
        context = "\n\n".join([d.page_content for d in documents])
        score = hallucination_chain.invoke({"documents": context, "generation": generation})
        
        if score.binary_score.lower() == "yes":
            print("---DECISION: GENERATION IS GROUNDED---")
            return "end"
        else:
            print("---DECISION: HALLUCINATION DETECTED---")
            if retries < self.max_retries:
                print(f"---RETRYING... ({retries + 1}/{self.max_retries})---")
                return "retry"
            else:
                print("---MAX RETRIES REACHED---")
                return "end"

    def increment_retries(self, state: AgentState):
        """Increment retry counter."""
        return {"retries": state.get("retries", 0) + 1}

    def build(self):
        workflow = StateGraph(AgentState)

        # Add Nodes
        workflow.add_node("retrieve", self.retrieve)
        workflow.add_node("grade_documents", self.grade_documents)
        workflow.add_node("web_search", self.web_search)
        workflow.add_node("generate", self.generate)
        workflow.add_node("direct_answer", self.direct_answer)
        workflow.add_node("increment_retries", self.increment_retries)

        # Build Graph
        workflow.set_conditional_entry_point(
            self.route_question,
            {
                "retrieve": "retrieve",
                "direct_answer": "direct_answer"
            }
        )
        workflow.add_edge("direct_answer", END)
        workflow.add_edge("retrieve", "grade_documents")
        
        workflow.add_conditional_edges(
            "grade_documents",
            self.decide_to_generate,
            {
                "web_search": "web_search",
                "generate": "generate"
            }
        )
        
        workflow.add_edge("web_search", "generate")
        
        workflow.add_conditional_edges(
            "generate",
            self.check_hallucination,
            {
                "end": END,
                "retry": "increment_retries"
            }
        )
        
        workflow.add_edge("increment_retries", "generate")

        return workflow.compile()
