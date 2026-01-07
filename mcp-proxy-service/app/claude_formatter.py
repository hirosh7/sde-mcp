"""Claude adapter for response formatting"""
import json
import asyncio
import logging
from typing import Any, Dict, Optional, List
from anthropic import Anthropic

logger = logging.getLogger(__name__)


class ClaudeResponseFormatter:
    """Uses Claude to format tool results into natural language"""
    
    def __init__(self, api_key: str, model: str = "claude-3-5-haiku-20241022", timeout: float = 30.0):
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
            conversation_history: Optional list of previous conversation entries
            
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
        
        # Add current formatting request
        result_json = json.dumps(result, indent=2)
        user_prompt = f"""Tool: {tool_name}
Original user query: {original_query}

Tool result (JSON):
{result_json}

IMPORTANT: Format this result according to the user's specific request in the original query.
- If the user asked to "summarize", "group by", "organize by", or format in a specific way, follow those instructions EXACTLY
- Extract and present only the fields the user requested (e.g., if they asked for "task ID and title", show ONLY those fields)
- Group or organize the data as requested (e.g., if they asked to "summarize by phase", group tasks by phase)
- DO NOT return raw JSON - always format it as natural language
- For countermeasures/tasks, if the user asked to summarize by phase, group them by phase and show only the requested fields

Consider the conversation history above for context:"""
        
        messages.append({"role": "user", "content": user_prompt})
        
        # Create prompt for Claude
        system_prompt = """You are a response formatter for SD Elements operations.
You have access to the conversation history above. Use this context to provide more relevant and contextual responses.

CRITICAL RULES:
1. ALWAYS return formatted natural language text - NEVER return raw JSON, code blocks with JSON, or structured data formats
2. Pay close attention to the original user query. If the user requested a specific format, summary, or organization of the data (e.g., "summarize by phase", "group by status", "show only task ID and title"), you MUST format the response accordingly
3. Default behavior: Always summarize and format data in a human-readable way unless the user explicitly requests raw JSON or structured data
4. If the user asks to "summarize", "group by", "organize by", or format data in a specific way, follow those instructions exactly

Guidelines:
- Be concise but informative
- Highlight key information (IDs, names, URLs, status)
- For lists, show count and key details for each item
- For errors, clearly explain what went wrong
- Use a friendly, professional tone
- Format dates/timestamps in a readable way
- Include relevant URLs when available
- Reference previous operations when relevant (e.g., "As mentioned earlier, 3 answers were deselected")
- For countermeasures/tasks, common formatting requests include:
  * Grouping by phase (X2, X3, X5, X7, etc.)
  * Showing only specific fields (task ID, title, status, etc.)
  * Summarizing or aggregating data
  * Creating tables or structured lists using plain text formatting

OUTPUT FORMAT:
- Use plain text with clear headings, bullet points, and line breaks
- Use markdown-style formatting (## for headings, - for bullets) but keep it simple
- NEVER wrap your response in code blocks or JSON
- NEVER include JSON syntax like {, }, [, ] unless it's part of natural language explanation

Respond with ONLY the formatted natural language text, no additional commentary, no code blocks, no JSON."""
        
        try:
            # Call Claude with timeout
            response = await asyncio.wait_for(
                self._call_claude(system_prompt, messages),
                timeout=self.timeout
            )
            formatted_response = response.strip()
            
            # Final validation: ensure we didn't get JSON back
            if formatted_response.startswith(("{", "[")):
                # Last attempt: try to detect and warn
                logger.warning("Claude formatter returned JSON-like response, attempting to extract formatted content")
                # If it's wrapped in markdown, try to extract
                if "```" in formatted_response:
                    # Already handled in _call_claude, but double-check
                    pass
            
            return formatted_response
            
        except asyncio.TimeoutError:
            raise ValueError(f"Claude formatting timed out after {self.timeout} seconds")
        except ValueError as e:
            # Re-raise ValueError (JSON detection) as-is
            raise
        except Exception as e:
            raise ValueError(f"Claude formatting failed: {str(e)}")
    
    async def _call_claude(self, system_prompt: str, messages: list) -> str:
        """Make the actual Claude API call"""
        # Run in executor to avoid blocking
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: self.anthropic.messages.create(
                model=self.model,
                max_tokens=4000,  # Increased for longer formatted responses
                system=system_prompt,
                messages=messages
            )
        )
        
        text = response.content[0].text
        
        # Validate that response is not raw JSON
        # Check if response looks like JSON (starts with { or [)
        text_stripped = text.strip()
        if text_stripped.startswith(("{", "[", "```json", "```")):
            # If it looks like JSON, try to parse and reformat
            try:
                # Try to parse as JSON to confirm
                json.loads(text_stripped.replace("```json", "").replace("```", "").strip())
                # If we get here, it's JSON - raise error to trigger retry or fallback
                raise ValueError("Claude returned JSON instead of formatted text. Response appears to be raw JSON.")
            except (json.JSONDecodeError, ValueError):
                # If it's not valid JSON but starts with those chars, might be markdown code block
                # Remove markdown code blocks if present
                if text_stripped.startswith("```"):
                    # Extract content between code blocks
                    lines = text_stripped.split("\n")
                    if lines[0].startswith("```"):
                        # Remove first and last lines if they're code block markers
                        if lines[-1].strip() == "```":
                            text = "\n".join(lines[1:-1])
                        else:
                            text = "\n".join(lines[1:])
        
        return text
    
    async def transform_data(
        self,
        query: str,
        conversation_history: Optional[List[Dict]] = None
    ) -> str:
        """
        Use Claude to transform/summarize data from conversation history.
        This is used when the user wants to transform data that was already retrieved
        in a previous conversation, without needing to call a new tool.
        
        Args:
            query: The user's transformation request (e.g., "summarize by showing task ID and Title")
            conversation_history: List of previous conversation entries containing the data to transform
            
        Returns:
            Transformed/summarized natural language string
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
        
        # Add current transformation request
        user_prompt = f"""User request: {query}

Based on the conversation history above, please transform or summarize the data as requested.
If the previous response contained JSON data or structured information, extract and transform it according to the user's request.
If you need to reference specific data from previous responses, use the conversation history to find it.

Respond with ONLY the transformed/summarized result in natural language."""
        
        messages.append({"role": "user", "content": user_prompt})
        
        # Create prompt for Claude
        system_prompt = """You are a data transformation assistant for SD Elements operations.
You have access to the conversation history above, which contains previous queries and responses.

When a user asks to transform, summarize, or reformat data from a previous response:
- Extract the relevant data from the conversation history
- Transform it according to the user's specific request
- Present the result in a clear, natural language format
- If the user asks for specific fields (e.g., "show only task ID and Title"), extract only those fields
- Maintain accuracy - don't add or remove data that wasn't in the original response
- Be concise and focused on what the user requested

Respond with ONLY the transformed result, no additional commentary or explanation."""
        
        try:
            # Call Claude with timeout
            response = await asyncio.wait_for(
                self._call_claude(system_prompt, messages),
                timeout=self.timeout
            )
            return response.strip()
            
        except asyncio.TimeoutError:
            raise ValueError(f"Claude data transformation timed out after {self.timeout} seconds")
        except Exception as e:
            raise ValueError(f"Claude data transformation failed: {str(e)}")

