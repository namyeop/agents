from firecrawl import Firecrawl
from crewai.tools import tool
from tavily import TavilyClient
import os


@tool
def firecrawl_search(query: str, num_results: int = 5):
    """
    Perform a web search using the Firecrawl API.

    Args:
        query (str): The search query.
        num_results (int): The number of search results to return.

    Returns:
        list[dict]: A list of search results, each represented as a dictionary.
    """
    firecrawl = Firecrawl(api_key=os.getenv("FIRECRAWL_API_KEY"))  # type: ignore

    results = firecrawl.search(
        query="2025년 9월 현재 사람들의 어그로를 가장 잘 끄는 밈", limit=3
    )

    return results


@tool
def tavily_search(query: str):
    """
    Perform a web search using the Tavily API.

    Args:
        query (str): The search query.

    Returns:
        list[dict]: A list of search results, each represented as a dictionary.
    """
    client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))  # type: ignore
    response = client.search(query=query)

    return response
