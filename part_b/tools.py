from langchain_core.tools import tool
from pydantic import BaseModel, Field
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
from langchain_community.tools import DuckDuckGoSearchResults

class WebSearchInput(BaseModel):
    query: str = Field(description="The search query to look up on the web.")

@tool("web_search_tool", args_schema=WebSearchInput)
def web_search_tool(query: str) -> str:
    """
    Search the web for information when the knowledge base fails or does not contain relevant information.
    Returns search results as a string.
    """
    try:
        wrapper = DuckDuckGoSearchAPIWrapper(max_results=3)
        search = DuckDuckGoSearchResults(api_wrapper=wrapper)
        return search.run(query)
    except Exception as e:
        return f"Web search failed: {str(e)}"
