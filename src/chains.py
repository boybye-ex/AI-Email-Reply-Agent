from langchain_groq import ChatGroq
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.messages import AIMessage
from src.config import GROQ_API_KEY, MODEL_NAME
from src.prompts import (
    EMAIL_CATEGORIZER_PROMPT,
    RESEARCH_ROUTER_PROMPT,
    SEARCH_KEYWORDS_PROMPT,
    EMAIL_DRAFT_PROMPT
)
import json

_groq_llm = None

def get_groq_llm() -> ChatGroq:
    global _groq_llm
    if _groq_llm is None:
        if not GROQ_API_KEY:
            raise ValueError(
                "GROQ_API_KEY is not set. Add it to .env in the project root."
            )
        _groq_llm = ChatGroq(
            api_key=GROQ_API_KEY,
            model=MODEL_NAME,
            temperature=0.1,
        )
    return _groq_llm

def create_json_parser_with_fallback():
    """Creates a JSON parser with error handling"""
    parser = JsonOutputParser()
    
    def parse_with_fallback(text_or_message) -> dict:
        try:
            if isinstance(text_or_message, AIMessage):
                text = text_or_message.content
            else:
                text = str(text_or_message)

            try:
                return json.loads(text)
            except:
                pass

            clean_text = text.strip()
            start = clean_text.find('{')
            end = clean_text.rfind('}')
            
            if start != -1 and end != -1:
                try:
                    json_str = clean_text[start:end+1]
                    return json.loads(json_str)
                except:
                    pass

            if "router_decision" in text.lower():
                if "research_info" in text.lower():
                    return {"router_decision": "research_info"}
                else:
                    return {"router_decision": "draft_email"}

            if "category" in text.lower():
                return {
                    "category": "product_inquiry",
                    "urgency_level": "low",
                    "needs_human_escalation": False,
                    "reasoning": "",
                }

            if "email_draft" in text.lower():
                return {"email_draft": text}
            elif "keywords" in text.lower():
                return {"keywords": ["default_keyword"]}
            else:
                return {"error": "Parsing failed", "original_text": text}

        except Exception as e:
            return {"error": str(e), "original_text": str(text_or_message)}

    return parse_with_fallback

class LazyChain:
    """Builds an LCEL chain on first invoke to defer LLM initialization."""

    def __init__(self, prompt):
        self._prompt = prompt
        self._chain = None

    def _get_chain(self):
        if self._chain is None:
            self._chain = self._prompt | get_groq_llm() | create_json_parser_with_fallback()
        return self._chain

    def invoke(self, *args, **kwargs):
        return self._get_chain().invoke(*args, **kwargs)

email_category_chain = LazyChain(EMAIL_CATEGORIZER_PROMPT)
research_router_chain = LazyChain(RESEARCH_ROUTER_PROMPT)
search_keyword_chain = LazyChain(SEARCH_KEYWORDS_PROMPT)
draft_writer_chain = LazyChain(EMAIL_DRAFT_PROMPT)
