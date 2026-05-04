from langchain_core.prompts import ChatPromptTemplate,MessagesPlaceholder
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentExecutor
from langchain.agents import create_tool_calling_agent
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain.tools.retriever import create_retriever_tool
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.vectorstores import Chroma
import os
import shutil
from dotenv import load_dotenv
load_dotenv()
Report_path=r"data\report.txt"
chunk_size=500
chunk_overlap=50
Chroma_Dir="data\chroma_db"
#reset vector store directory
def reset_vector_store():
 if os.path.exists(Chroma_Dir):
  shutil.rmtree(Chroma_Dir)
  print("Vector data base is clean")
 else:
  print("No existing vector data vase found")

#Data ingestion
def documents_loading(Report_path: str):
 loader=TextLoader(Report_path)
 docs=loader.load()
 return docs
#Chunking
def chunking(docs):
  text_splitter=RecursiveCharacterTextSplitter(chunk_size=chunk_size,
                                               chunk_overlap=chunk_overlap)
  chunks=text_splitter.split_documents(docs)
  return chunks
#Embeddings and Vector Data Base
def create_vectorstore(chunks):
 embeddings=HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
 vector_store=Chroma.from_documents(
                     documents=chunks,
                     embedding=embeddings,
                     persist_directory=Chroma_Dir)
 return vector_store
#Retrieval tool
def build_retrieval(vector_store):
  retriever=vector_store.as_retriever(search_kwargs={"k": 1})
  retrieval_tool=create_retriever_tool(retriever,
                                       name="financial_knowledge_tool",
                                       description="Use this tool to answer questions about ACME Corporation's financial report. ")
  return retriever,retrieval_tool
#Memory
store={}
def get_session_history(session_id):
 if session_id not in store:
  store[session_id]=ChatMessageHistory()
 return store[session_id]
#Agent
def building_react_agent(retrieval_tool):
 #llm
 llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash", 
    api_key=os.getenv("GOOGLE_API_KEY"),
    temperature=0)
 #prompt
 prompt = ChatPromptTemplate.from_messages([
        ("system", """You are FinAgent, an expert financial assistant for ACME Corporation.
 
   You have access to:
 1. A financial knowledge tool containing ACME's 2024 annual report (Q1-Q4 data).
 2. Conversation history to recall previous context from the user.
 
 Rules:
  - Always use the financial_knowledge_tool for questions about revenue, profit, EBITDA, margins, or any financial figures.
  - Use conversation history to answer questions about previously mentioned context.
  - If the question combines both tool data and memory (e.g., comparing report data to something the user mentioned), use the tool AND recall from history.
  - CRITICAL: Do NOT repeat or restate the tool output. Return it once, clearly and concisely.
  - Always show your reasoning before acting (Thought → Action → Observation → Answer).
 """),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

 agent=create_tool_calling_agent(llm=llm,
                                prompt=prompt,
                                tools=[retrieval_tool])
 agent_excuter=AgentExecutor(agent=agent,
                             tools=[retrieval_tool],
                             verbose=True)
 agent_with_memory=RunnableWithMessageHistory(
                        agent_excuter,
                        get_session_history,
                        input_messeges_key="input",
                        history_messages_key="chat_history")
  
 return agent_with_memory
if __name__ == "__main__":
 reset_vector_store()
 docs=documents_loading(Report_path)
 chunks=chunking(docs)
 vector_store=create_vectorstore(chunks)
 retriever,retrieval_tool=build_retrieval(vector_store)
 agent_with_memory=building_react_agent(retrieval_tool)
    # Simulate user interactions
turn1 = agent_with_memory.invoke(
    {"input": 'Our internal target for Q3 revenue was $14,000,000.'},
    config={"configurable": {"session_id": "user1"}})
turn2 = agent_with_memory.invoke(
    {"input": "What was our internal Q3 revenue target that I just mentioned?"},
    config={"configurable": {"session_id": "user1"}})
turn3 = agent_with_memory.invoke(
    {"input":"What was the Q4 profit margin based on the report, "
            "and how does that compare to the Q3 revenue mentioned in our previous chat?"},
    config={"configurable": {"session_id": "user1"}})
#Lang Smith
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY")
os.environ["LANGCHAIN_PROJECT"] = "FinAgent"


 
 
  
 









