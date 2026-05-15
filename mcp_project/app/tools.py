import os
from typing import List, Optional
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

# Configuration
DB_DIR = "chroma_db"
COLLECTION_NAME = "academic_knowledge"


# 1. Pydantic Schemas for Validation
class GPACalculatorSchema(BaseModel):
    grades: List[str] = Field(description="A list of letter grades (e.g., ['A', 'B', 'C'])")


class ExamScheduleSchema(BaseModel):
    course_code: str = Field(description="The course code to check (e.g., 'AI407')")


class AcademicPolicySchema(BaseModel):
    query: str = Field(description="The question about academic policies or course details")


# 2. Tool Implementations
@tool("calculate_gpa", args_schema=GPACalculatorSchema)
def calculate_gpa_tool(grades: List[str]):
    """
    Calculates the GPA from a list of letter grades.
    Use this when a student asks for their average or GPA.
    """
    grade_points = {
        "A+": 4.0, "A": 4.0, "A-": 3.7,
        "B+": 3.3, "B": 3.0, "B-": 2.7,
        "C+": 2.3, "C": 2.0, "C-": 1.7,
        "D+": 1.3, "D": 1.0, "F": 0.0
    }
    if not grades:
        return "No grades provided."

    total = 0
    valid_count = 0
    for g in grades:
        point = grade_points.get(g.upper())
        if point is not None:
            total += point
            valid_count += 1

    if valid_count == 0:
        return "Invalid grades provided."

    gpa = total / valid_count
    return f"The calculated GPA for grades {grades} is {round(gpa, 2)}."


@tool("check_exam_schedule", args_schema=ExamScheduleSchema)
def check_exam_schedule_tool(course_code: str):
    """
    Returns the scheduled exam time for a specific course code.
    """
    exam_db = {"AI407": "Monday 2:30 PM", "CS101": "Tuesday 9:00 AM", "SE302": "Wednesday 11:00 AM"}
    time = exam_db.get(course_code.upper())
    if time:
        return f"The exam for {course_code} is scheduled for {time}."
    return f"No exam schedule found for course {course_code}."


@tool("academic_policy_lookup", args_schema=AcademicPolicySchema)
def academic_policy_lookup_tool(query: str):
    """
    Searches the academic handbook and course catalog for information.
    Use this for any general questions about university rules, grading policies, or course prerequisites.
    """
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vectorstore = Chroma(persist_directory=DB_DIR, embedding_function=embeddings, collection_name=COLLECTION_NAME)

    results = vectorstore.similarity_search(query, k=3)
    context = "\n---\n".join([doc.page_content for doc in results])
    return f"Retrieved Context:\n{context}"


# Export tools
tools = [calculate_gpa_tool, check_exam_schedule_tool, academic_policy_lookup_tool]
