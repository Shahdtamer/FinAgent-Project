from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.runnables import RunnableSequence
import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_core.output_parsers import PydanticOutputParser
load_dotenv()
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash", 
    api_key=os.getenv("GOOGLE_API_KEY"),
    temperature=0.7
)
class FinancialSummary(BaseModel):
    key_finding:str=Field(description="A concise summary of the key findings from the financial report.")
    supporting_data:str=Field(description="A detailed description of the data and evidence that supports the key findings.")
    confidence_score:float=Field(description="A numerical score between 0 and 1 that indicates the confidence level of the key findings based on the supporting data.")
parser=PydanticOutputParser(pydantic_object=FinancialSummary)
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            (
                "You are an expert financial analyst. "
                "Analyze the user's query and respond ONLY with a structured JSON object. "
                "Do not include any explanation outside the JSON.\n\n"
                "{format_instructions}"
            ),
        ),
        ("human", "{query}"),
    ]
).partial(format_instructions=parser.get_format_instructions())
chain = prompt | llm | parser
if name == "main":
    user_query = (
        "What is the impact of rising interest rates on tech stock valuations in 2024?"
    )
 
    result: FinancialSummary = chain.invoke({"query": user_query})
 
    print("=== Financial Summary ===")
    print(f"Key Finding      : {result.key_finding}")
    print(f"Supporting Data  : {result.supporting_data}")
    print(f"Confidence Score : {result.confidence_score:.2f}")

