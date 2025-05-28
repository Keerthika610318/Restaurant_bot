
from langchain_openai import AzureChatOpenAI
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("AZURE_OPENAI_API_KEY")
deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
api_version = os.getenv("AZURE_OPENAI_API_VERSION")
azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")

llm = AzureChatOpenAI(
    openai_api_version=api_version,
    deployment_name=deployment_name,
    model="gpt-3.5-turbo",  
    temperature=0.3,
    api_key=api_key,
    azure_endpoint=azure_endpoint,
    max_tokens=500
)