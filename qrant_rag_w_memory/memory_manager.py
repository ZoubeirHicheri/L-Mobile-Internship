import logging
from collections import deque
from typing import Dict, List

logger = logging.getLogger(__name__)

class MemoryManager:
    """Manages conversation buffer, summary, and fact extraction."""
    
    def __init__(self, max_buffer_turns: int = 6, max_summary_tokens: int = 200):
        self.buffer = deque(maxlen=max_buffer_turns)
        self.summary = ""
        self.max_summary_tokens = max_summary_tokens
        
    def append_turn(self, user_text: str, assistant_text: str):
        """Add user and assistant messages to buffer."""
        self.buffer.append({"role": "user", "text": user_text})
        self.buffer.append({"role": "assistant", "text": assistant_text})
        
    def get_buffer_text(self) -> str:
        """Get formatted conversation history."""
        return "\n".join(f"{m['role']}: {m['text']}" for m in self.buffer)
        
    def build_rewrite_prompt(self, user_text: str) -> str:
        """Create prompt for query rewriting with context."""
        return f"""Rewrite the user's question to be standalone using the conversation context.

Summary: {self.summary}

Recent turns:
{self.get_buffer_text()}

User question: {user_text}

Standalone rewrite:"""

    def build_summary_prompt(self, user_text: str, assistant_text: str) -> str:
        """Create prompt for updating conversation summary."""
        return f"""Update the conversation summary to capture key context.
Keep it under {self.max_summary_tokens} tokens, concise and factual.

Current summary:
{self.summary}

New exchange:
user: {user_text}
assistant: {assistant_text}

Updated summary:"""

    def build_facts_prompt(self, user_text: str, assistant_text: str) -> str:
        """Create prompt for extracting memorable facts."""
        return f"""Extract 0-3 durable facts or preferences useful for future conversations.
Return bullet points under 20 words each, or 'NONE' if nothing worth remembering.

Exchange:
user: {user_text}
assistant: {assistant_text}

Facts:"""
