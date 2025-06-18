import os
import json
from dotenv import load_dotenv
from tools.rag_tools import retrieve_from_rag
from tools.llm_client import OpenRouterClient

# Load environment variables from .env file
load_dotenv()

def main():
    """
    Uses RAG to find information about a topic and then uses an LLM to synthesize the results.
    """
    # 1. Configure the RAG query
    topic = "time off"
    field = "start_date"
    query = f"Information about {topic} and the field '{field}'"
    collection_name = "flip_api_v2"
    
    print(f"🔍 Step 1/3: Querying RAG for '{query}'...")
    rag_results = retrieve_from_rag(
        query=query,
        collection_name=collection_name,
        limit=5,
        score_threshold=0.3,
    )

    if not rag_results:
        print("❌ No relevant information found in the RAG system. Try a different query.")
        return

    print(f"✅ Found {len(rag_results)} relevant document(s) from RAG.")
    
    # 2. Use LLM to synthesize the information
    print("\n🤖 Step 2/3: Synthesizing information with LLM...")
    llm_client = OpenRouterClient()
    
    # Create a detailed prompt for the LLM
    rag_context = json.dumps(rag_results, indent=2)
    llm_prompt = f"""
    Based on the following context retrieved from an API specification, please answer the user's question.

    USER'S QUESTION:
    "Find all information about time off and the field start_date or however it is called."

    RETRIEVED CONTEXT FROM API SPECIFICATION:
    ---
    {rag_context}
    ---

    YOUR TASK:
    Analyze the context and provide a clear, concise summary that answers the user's question. 
    Focus on:
    1.  What is the exact name of the start date field for time off requests?
    2.  What is its purpose and data format (e.g., date, datetime, string)?
    3.  Which API endpoint(s) use this field?
    
    Provide the answer in a readable markdown format.
    """

    system_prompt = "You are an expert API assistant. You help developers understand API specifications by analyzing retrieved documentation."
    
    llm_answer = llm_client.generate(llm_prompt, system_prompt=system_prompt)

    # 3. Print the final answer
    print("\n✅ Step 3/3: Here is the synthesized answer:\n")
    print("--- LLM-Generated Summary ---")
    print(llm_answer)
    print("--------------------------")

if __name__ == "__main__":
    main()
