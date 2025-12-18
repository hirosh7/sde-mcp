"""Claude adapter for tool selection"""
import json
import logging
from typing import Tuple, Optional
from anthropic import Anthropic

logger = logging.getLogger(__name__)


class ClaudeToolSelector:
    """Uses Claude to select the appropriate tool for a natural language query"""
    
    def __init__(self, api_key: str, model: str = "claude-3-5-haiku-20241022"):
        self.anthropic = Anthropic(api_key=api_key)
        self.model = model
    
    async def select_tool(self, query: str, available_tools: list) -> Tuple[str, dict]:
        """
        Use Claude to determine which tool to call and with what arguments.
        
        Returns:
            Tuple of (tool_name, arguments_dict)
        """
        # Format tools for Claude
        tools_description = self._format_tools_for_claude(available_tools)
        
        # Create prompt for Claude
        system_prompt = """You are a tool selector for SD Elements operations. 
Given a user's natural language query, determine which tool should be called and with what arguments.

IMPORTANT RULES:
1. For create_project: If the query doesn't specify an application, you should first call list_applications to see available applications, then either:
   - Infer the application from the project name/description (e.g., "Mobile Banking App" might match an application with "Banking" or "Mobile" in the name)
   - Use the application_id from the most relevant application
   - If you cannot determine which application to use, you may omit application_id and let the tool handle it (it will try to auto-detect or return available options)

2. You must respond with ONLY a JSON object in this exact format:
{
    "tool_name": "name_of_tool",
    "arguments": {
        "arg1": "value1",
        "arg2": "value2"
    }
}

3. If no tool matches the query, return:
{
    "tool_name": null,
    "arguments": {},
    "error": "No matching tool found"
}

4. Only provide arguments that are explicitly mentioned in the query or that you can reasonably infer. Do not make up values for required parameters unless you can infer them."""

        user_prompt = f"""Available tools:
{tools_description}

User query: {query}

Respond with JSON only:"""

        try:
            response = self.anthropic.messages.create(
                model=self.model,
                max_tokens=1000,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ],
            )
            
            # Extract JSON from response
            raw_response = response.content[0].text.strip()
            response_text = raw_response
            
            # Log the raw response for debugging
            logger.debug(f"Claude raw response: {raw_response}")
            
            # Try to parse JSON (might be wrapped in markdown code blocks)
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            # Try to extract JSON object if there's extra text
            # Look for first { and last } to extract just the JSON object
            original_text = response_text
            if "{" in response_text and "}" in response_text:
                start_idx = response_text.find("{")
                # Find the matching closing brace
                brace_count = 0
                end_idx = start_idx
                for i in range(start_idx, len(response_text)):
                    if response_text[i] == "{":
                        brace_count += 1
                    elif response_text[i] == "}":
                        brace_count -= 1
                        if brace_count == 0:
                            end_idx = i + 1
                            break
                if end_idx > start_idx:
                    extracted_json = response_text[start_idx:end_idx]
                    if len(extracted_json) < len(response_text):
                        # There was extra text, log it
                        extra_text = response_text[end_idx:].strip()
                        logger.warning(f"Claude returned extra text after JSON: {extra_text}")
                        logger.info(f"Full Claude response: {raw_response}")
                    response_text = extracted_json
            
            result = json.loads(response_text)
            
            tool_name = result.get("tool_name")
            arguments = result.get("arguments", {})
            
            if not tool_name:
                error = result.get("error", "No tool selected")
                raise ValueError(f"Tool selection failed: {error}")
            
            return tool_name, arguments
            
        except json.JSONDecodeError as e:
            # Include the raw response in the error for debugging
            raw_response = response.content[0].text.strip() if 'response' in locals() else "No response captured"
            error_msg = f"Failed to parse Claude response as JSON: {e}\n\nRaw Claude response:\n{raw_response}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        except Exception as e:
            # Try to capture raw response if available
            raw_response = ""
            try:
                if 'response' in locals():
                    raw_response = f"\n\nRaw Claude response:\n{response.content[0].text.strip()}"
            except:
                pass
            error_msg = f"Claude tool selection failed: {e}{raw_response}"
            logger.error(error_msg)
            raise ValueError(error_msg)
    
    def _format_tools_for_claude(self, tools: list) -> str:
        """Format tools list for Claude prompt"""
        formatted = []
        for tool in tools:
            name = tool.get("name", "")
            description = tool.get("description", "")
            schema = tool.get("input_schema", {})
            
            tool_info = f"- {name}: {description}"
            if schema and "properties" in schema:
                props = schema["properties"]
                required = schema.get("required", [])
                tool_info += "\n  Parameters:"
                for prop_name, prop_info in props.items():
                    param_type = prop_info.get("type", "unknown")
                    param_desc = prop_info.get("description", "")
                    req_marker = " (required)" if prop_name in required else ""
                    tool_info += f"\n    - {prop_name} ({param_type}){req_marker}: {param_desc}"
            
            formatted.append(tool_info)
        
        return "\n\n".join(formatted)

