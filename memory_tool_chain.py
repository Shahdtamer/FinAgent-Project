from langchain_core.prompts import ChatPromptTemplate,MessagesPlaceholder
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentExecutor
from langchain.agents import create_tool_calling_agent
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain.tools.retriever import create_retriever_tool
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.runnables.history import RunnableWithMessageHistory

import os
from dotenv import load_dotenv

load_dotenv()
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash", 
    api_key=os.getenv("GOOGLE_API_KEY"),
    temperature=0.7
)
# Defoine the prompt with system instructions and human input that choose between using memory or tool based on the question
prompt = ChatPromptTemplate.from_messages([
    ("system","""You are a helpful financial assistant.

You have access to:
1. Conversation history (memory) to recall previous user inputs.
2. A financial knowledge tool to retrieve definitions.

Rules:
- Use the conversation history to answer questions about previous context.
- If the question is about financial definitions (e.g., EBITDA), use the tool.
- If the answer is already in the conversation, do NOT use the tool.
- do not repeat the answer in the same response
- If tool is used, return ONLY tool output.
- Always provide clear and concise answers."""),
MessagesPlaceholder(variable_name="chat_history"),
    ("human","{input}") ,
    MessagesPlaceholder(variable_name="agent_scratchpad")  
])
#the MOCK Vector data base 
mock_financial_facts = [
    "EBITDA stands for Earnings Before Interest, Taxes, Depreciation, and Amortization. "
    "It measures a company's core operational profitability by removing the effects of "
    "financing decisions, accounting choices, and tax environments.",
 
    "A P/E ratio (Price-to-Earnings ratio) compares a company's stock price to its "
    "earnings per share. A high P/E suggests investors expect strong future growth; "
    "a low P/E may indicate an undervalued stock or weak growth prospects.",
 
    "Working capital is current assets minus current liabilities. It measures a company's "
    "short-term liquidity and its ability to fund day-to-day operations.",
]
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)
vector_db = FAISS.from_texts(mock_financial_facts, embeddings)
#Retrieval function
retriever=vector_db.as_retriever(search_kwargs={"k": 1})
retrieval_tool=create_retriever_tool(retriever,
        name="financial_knowledge_tool",
        description="Use this tool to answer financial definition questions like EBITDA, P/E ratio, etc."
)
#conersational buffer memory
store={}
def get_session_history(session_id:str):
    if session_id not in store:
        store[session_id]=ChatMessageHistory()
    return store[session_id]
#the agent
agent=create_tool_calling_agent(
    llm=llm,
    tools=[retrieval_tool],
    prompt=prompt
)
agent_executor = AgentExecutor(
    agent=agent,
    tools=[retrieval_tool],
    verbose=True
)
agent_with_memory = RunnableWithMessageHistory(
    agent_executor,          
    get_session_history,     
    input_messages_key="input",
    history_messages_key="chat_history",
)
turn1 = agent_with_memory.invoke(
    {"input": "The company's Q1 revenue was $10M."},
    config={"configurable": {"session_id": "user1"}}
)
turn2 = agent_with_memory.invoke({"input": "What was the Q1 revenue?"},config={"configurable": {"session_id": "user1"}})
turn3 = agent_with_memory.invoke({"input": "What is the definition of EBITDA?"},config={"configurable": {"session_id": "user2"}})








