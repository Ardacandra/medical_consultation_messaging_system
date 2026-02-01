from langchain_google_genai import ChatGoogleGenerativeAI
import os
from dotenv import load_dotenv

load_dotenv()

class LLMFactory:
    @staticmethod
    def create_llm(model_name: str = "gemini-2.0-flash", temperature: float = 0.0):
        """
        Creates a Gemini Chat Model instance.
        """
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables.")
            
        return ChatGoogleGenerativeAI(
            model=model_name,
            temperature=temperature,
            google_api_key=api_key,
            convert_system_message_to_human=True # Sometimes needed for certain frameworks, mainly harmless
        )
