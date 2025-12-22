"""Claude adapter for response formatting"""
import json
import asyncio
from typing import Any, Dict, List, Optional
from anthropic import Anthropic


class ClaudeResponseFormatter:
    """Uses Claude to format tool results into natural language"""
    
    def __init__(self, api_key: str, model: str = "claude-3-5-haiku-20241022", timeout: float = 10.0):
        self.anthropic = Anthropic(api_key=api_key)
        self.model = model
        self.timeout = timeout
    
    async def format_result(
        self, 
        tool_name: str, 
        result: Dict[str, Any], 
        original_query: str,
        conversation_history: Optional[List[Dict]] = None
    ) -> str:
        """
        Use Claude to format a tool result into natural language.
        
        Args:
            tool_name: Name of the tool that was called
            result: The result dictionary from the tool
            original_query: The original user query for context
            conversation_history: Optional list of previous conversation turns
            
        Returns:
            Formatted natural language string
        """
        # Build messages with history
        messages = []
        
        if conversation_history:
            for conv in conversation_history:
                messages.append({
                    "role": "user",
                    "content": conv.get("query", "")
                })
                messages.append({
                    "role": "assistant",
                    "content": conv.get("response", "")
                })
        
        # Format the JSON result for the prompt
        result_json = json.dumps(result, indent=2)
        
        # Add current formatting request
        user_prompt = f"""Tool: {tool_name}
Original user query: {original_query}

Tool result (JSON):
{result_json}

Format this result into natural language. Consider the conversation history above for context:"""
        
        messages.append({"role": "user", "content": user_prompt})
        
        # Create prompt for Claude
        system_prompt = """You are a response formatter for SD Elements operations.
You have access to the conversation history above. Use this context to provide more relevant and contextual responses.

Guidelines:
- Be concise but informative
- Highlight key information (IDs, names, URLs, status)
- For lists, show count and key details for each item
- For errors, clearly explain what went wrong
- Use a friendly, professional tone
- Format dates/timestamps in a readable way
- Include relevant URLs when available
- Reference previous operations when relevant (e.g., "As mentioned earlier, 3 answers were deselected")

Respond with ONLY the formatted natural language text, no additional commentary."""
        
        try:
            # Call Claude with timeout
            response = await asyncio.wait_for(
                self._call_claude(system_prompt, messages),
                timeout=self.timeout
            )
            return response.strip()
            
        except asyncio.TimeoutError:
            raise ValueError(f"Claude formatting timed out after {self.timeout} seconds")
        except Exception as e:
            raise ValueError(f"Claude formatting failed: {str(e)}")
    
    async def _call_claude(self, system_prompt: str, messages: List[Dict]) -> str:
        """Make the actual Claude API call"""
        # Run in executor to avoid blocking
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: self.anthropic.messages.create(
                model=self.model,
                max_tokens=2000,
                system=system_prompt,
                messages=messages
            )
        )
        
        return response.content[0].text

