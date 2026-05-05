import os
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()

# --- 1. Define the Pydantic Schema ---
class StudentResponse(BaseModel):
    """
    This defines the exact JSON structure the LLM MUST return.
    It forces the LLM to organize its thoughts into these specific fields.
    """
    is_action_required: bool = Field(
        description="True if the student needs to take a physical action (like filling a form or meeting an advisor). False if this is just informational."
    )
    summary: str = Field(
        description="A concise, 1-sentence summary of the answer."
    )
    detailed_explanation: str = Field(
        description="The full, polite explanation of the academic policy or calculation."
    )
    suggested_next_steps: list[str] = Field(
        description="A list of 1-3 actionable next steps the student can take."
    )

# --- 2. Initialize Model with Structured Output ---
def get_structured_model():
    model = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash-lite", # Using the lite model to avoid 404/Quota limits
        google_api_key=os.getenv("GEMINI_API_KEY"),
        temperature=0
    )
    
    # This is the magic LangChain method that forces the LLM to return JSON matching the schema
    structured_model = model.with_structured_output(StudentResponse)
    return structured_model
