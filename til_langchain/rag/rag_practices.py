from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

client = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=1.0,
)
response = client.invoke("hi")
print(response)