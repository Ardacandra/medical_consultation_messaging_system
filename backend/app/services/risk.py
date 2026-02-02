from app.schemas import RiskAnalysisResult, RiskLevel
from app.db.models import Message
from typing import List
from app.services.llm_factory import LLMFactory
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

class RiskAnalysisService:
    """
    Service to analyze the risk of a user message using Gemini.
    """
    def __init__(self):
        self.llm = LLMFactory.create_llm(temperature=0.0) # Low temp for deterministic classification
        
        # Define Parser
        self.parser = JsonOutputParser(pydantic_object=RiskAnalysisResult)
        
        # Define Prompt
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a medical triage assistant. Your job is to analyze the patient's message and determine if it presents a HIGH risk (emergency), MEDIUM risk (needs attention), or LOW risk (routine). \n\n"
                       "Definitions:\n"
                       "- HIGH: Life-threatening, chest pain, suicide ideation, stroke signs, severe difficulty breathing.\n"
                       "- MEDIUM: Severe pain, high fever, concerning symptoms but not immediately life-threatening.\n"
                       "- LOW: Routine questions, medication refills, appointment booking, mild symptoms.\n\n"
                       "You MUST provide a 'summary' that is a concise 1-5 bullet point triage summary of the situation.\n\n"
                       "Output strictly valid JSON matching the schema.\n"
                       "{format_instructions}"),
            ("user", "History: {history}\n\nNew Message: {message}")
        ])
        
        self.chain = self.prompt | self.llm | self.parser
    
    async def analyze_risk(self, history: List[Message], new_message_content: str) -> RiskAnalysisResult:
        """
        Analyzes the risk of the new message given the conversation history.
        """
        # Format history string
        history_str = "\n".join([f"{msg.sender_type}: {msg.content}" for msg in history[-5:]])
        
        try:
            result = await self.chain.ainvoke({
                "history": history_str, 
                "message": new_message_content,
                "format_instructions": self.parser.get_format_instructions()
            })
            
            # Map string to Enum if needed, though Pydantic parser should handle it if prompt is good.
            # But let's be safe and validate via Pydantic model again.
            return RiskAnalysisResult(**result)
            
        except Exception as e:
            # Fallback for parsing errors or API errors
            print(f"Risk Analysis Failed: {e}")
            return RiskAnalysisResult(
                risk_level=RiskLevel.HIGH, # Fail safe
                reason="AI Analysis Failed. Defaulting to High Risk for safety.",
                summary="System Error during triage."
            )
