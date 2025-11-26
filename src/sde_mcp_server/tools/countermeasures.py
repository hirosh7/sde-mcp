"""Countermeasure-related tools"""
import json
from typing import Optional, Union

from fastmcp import Context

from ..server import mcp, api_client, init_api_client


def normalize_countermeasure_id(project_id: int, countermeasure_id: Union[int, str]) -> str:
    """
    Normalize countermeasure ID to full format (project_id-task_id).
    
    Accepts:
    - Integer: 21 -> "T21" -> "{project_id}-T21"
    - String starting with "T": "T21" -> "{project_id}-T21"
    - String in full format: "31244-T21" -> "31244-T21" (as-is)
    
    Args:
        project_id: The project ID
        countermeasure_id: Countermeasure ID as int or str
        
    Returns:
        Full task ID format: "{project_id}-T{number}" or existing full format
    """
    # If integer, convert to "T{number}" format
    if isinstance(countermeasure_id, int):
        task_id = f"T{countermeasure_id}"
    else:
        # Already a string
        task_id = countermeasure_id
    
    # If already in full format (contains project_id), return as-is
    if task_id.startswith(f"{project_id}-"):
        return task_id
    
    # Otherwise, construct full format
    return f"{project_id}-{task_id}"


@mcp.tool()
async def list_countermeasures(ctx: Context, project_id: int, status: Optional[str] = None, page_size: Optional[int] = None, risk_relevant: bool = True) -> str:
    """List all countermeasures for a project. Use this to see countermeasures associated with a project, not get_project which returns project details."""
    global api_client
    if api_client is None:
        api_client = init_api_client()
    params = {}
    if status is not None:
        params["status"] = status
    if page_size is not None:
        params["page_size"] = page_size
    params["risk_relevant"] = str(risk_relevant).lower()
    result = api_client.list_countermeasures(project_id, params)
    return json.dumps(result, indent=2)


@mcp.tool()
async def get_countermeasure(ctx: Context, project_id: int, countermeasure_id: Union[int, str], risk_relevant: bool = True) -> str:
    """Get details of a SPECIFIC countermeasure by its ID. Use this when the user asks about a particular countermeasure (e.g., "countermeasure 123", "T21", "countermeasure 456"). Accepts countermeasure ID as integer (e.g., 21) or string (e.g., "T21" or "31244-T21"). Filter by risk relevance - if true, only return risk-relevant countermeasures. Defaults to true. Do NOT use this tool when the user asks about available status choices or what statuses are valid - use get_task_status_choices instead."""
    global api_client
    if api_client is None:
        api_client = init_api_client()
    normalized_id = normalize_countermeasure_id(project_id, countermeasure_id)
    params = {"risk_relevant": risk_relevant}
    result = api_client.get_countermeasure(project_id, normalized_id, params)
    return json.dumps(result, indent=2)


def resolve_status_to_id(status: str, api_client) -> str:
    """
    Resolve a status name or slug to its ID.
    
    The API requires status IDs (e.g., "TS1", "TS2") not names (e.g., "Complete").
    This function looks up the status ID from the task-statuses endpoint.
    
    Args:
        status: Status name (e.g., "Complete"), slug (e.g., "DONE"), or ID (e.g., "TS1")
        api_client: The API client instance
        
    Returns:
        Status ID (e.g., "TS1") or the original value if not found
    """
    if not status or not status.strip():
        return status
    
    try:
        # Get all available statuses
        statuses_response = api_client.get_task_status_choices()
        status_choices = statuses_response.get('status_choices', [])
        
        if not status_choices:
            # If we can't get statuses, return original (might already be an ID)
            return status
        
        # Normalize input for comparison
        status_normalized = status.strip()
        status_lower = status_normalized.lower()
        
        # Check if it's already an ID (starts with "TS")
        if status_normalized.upper().startswith('TS'):
            # Verify it's a valid ID
            for s in status_choices:
                if s.get('id', '').upper() == status_normalized.upper():
                    return s['id']
            return status_normalized  # Return as-is if not found
        
        # Try to match by exact name, slug, or meaning first (most reliable)
        for status_obj in status_choices:
            name = status_obj.get('name', '')
            slug = status_obj.get('slug', '')
            meaning = status_obj.get('meaning', '')
            status_id = status_obj.get('id', '')
            
            # Exact matches (case-insensitive)
            if (status_lower == name.lower() or 
                status_lower == slug.lower() or 
                status_lower == meaning.lower()):
                return status_id
        
        # Try partial/fuzzy matching as fallback (e.g., "complete" -> "Complete")
        # Only match if the input is a substring of the name/slug (not the other way around)
        # This avoids false positives like "complete" matching "incomplete"
        for status_obj in status_choices:
            name = status_obj.get('name', '').lower()
            slug = status_obj.get('slug', '').lower()
            meaning = status_obj.get('meaning', '').lower()
            status_id = status_obj.get('id', '')
            
            # Check if normalized input matches the start of name/slug/meaning
            # or if it's a common variation
            if (name.startswith(status_lower) or 
                slug.startswith(status_lower) or
                meaning.startswith(status_lower) or
                # Handle common variations like "completed" -> "complete"
                (status_lower in ['completed', 'done', 'finished'] and 'complete' in name) or
                (status_lower in ['completed', 'done', 'finished'] and 'done' in slug)):
                return status_id
        
        # If no match found, return original (might be a valid ID we don't know about)
        return status_normalized
        
    except Exception as e:
        # If lookup fails, log the error but still return original value
        # In production, you might want to log this for debugging
        # For now, we'll return the original value
        return status.strip()


@mcp.tool()
async def update_countermeasure(ctx: Context, project_id: int, countermeasure_id: Union[int, str], status: Optional[str] = None, notes: Optional[str] = None) -> str:
    """Update a countermeasure (status or notes). Use when user says 'update status', 'mark as complete', or 'change status'. Do NOT use for 'add note', 'document', or 'note' - use add_countermeasure_note instead. Accepts countermeasure ID as integer (e.g., 21) or string (e.g., "T21" or "31244-T21").
    
    Status can be provided as name (e.g., 'Complete', 'Not Applicable'), slug (e.g., 'DONE', 'NA'), or ID (e.g., 'TS1'). The tool will automatically resolve names/slugs to the correct status ID required by the API.
    
    IMPORTANT: The 'notes' parameter sets a status_note, which is only saved when the status actually changes. If the countermeasure already has the target status, use add_countermeasure_note instead to add a note, or change the status to a different value first, then back to the target status to trigger saving the status_note."""
    global api_client
    if api_client is None:
        api_client = init_api_client()
    normalized_id = normalize_countermeasure_id(project_id, countermeasure_id)
    data = {}
    if status is not None:
        # Resolve status name/slug to ID (API requires status IDs like "TS1", not names like "Complete")
        status_id = resolve_status_to_id(status, api_client)
        
        # Validate that we got a proper status ID (should start with "TS")
        # If the resolved status doesn't look like an ID and doesn't match the original input,
        # it means the conversion might have failed
        if not status_id.upper().startswith('TS') and status_id.lower() == status.strip().lower():
            # The status wasn't converted - this means we couldn't find a match
            # Try to get available statuses to provide a helpful error message
            try:
                statuses_response = api_client.get_task_status_choices()
                status_choices = statuses_response.get('status_choices', [])
                available_statuses = [s.get('name', '') for s in status_choices if s.get('name')]
                return json.dumps({
                    "error": f"Could not resolve status '{status}' to a status ID. The API requires status IDs (e.g., 'TS1', 'TS2'), not names.",
                    "provided_status": status,
                    "available_status_names": available_statuses[:10],  # Show first 10
                    "suggestion": "Use get_task_status_choices to see all available statuses and their IDs."
                }, indent=2)
            except Exception:
                return json.dumps({
                    "error": f"Could not resolve status '{status}' to a status ID. The API requires status IDs (e.g., 'TS1', 'TS2'), not names like '{status}'.",
                    "provided_status": status,
                    "suggestion": "Use get_task_status_choices to see all available statuses and their IDs."
                }, indent=2)
        
        data["status"] = status_id
    if notes is not None:
        data["status_note"] = notes
    
    if not data:
        return json.dumps({"error": "No update data provided. Specify either 'status' or 'notes'."}, indent=2)
    
    result = api_client.update_countermeasure(project_id, normalized_id, data)
    return json.dumps(result, indent=2)


@mcp.tool()
async def add_countermeasure_note(ctx: Context, project_id: int, countermeasure_id: Union[int, str], note: str) -> str:
    """Add a note to a countermeasure. Use when user says 'add note', 'document', 'note that', 'record that', or wants to add documentation. Use update_countermeasure if user wants to change status. Accepts countermeasure ID as integer (e.g., 21) or string (e.g., "T21" or "31244-T21").
    
    IMPORTANT: Use this tool when adding notes to countermeasures that already have the target status. The update_countermeasure tool's 'notes' parameter only saves status_note when the status actually changes. For countermeasures that already have the desired status, always use add_countermeasure_note to ensure the note is saved."""
    global api_client
    if api_client is None:
        api_client = init_api_client()
    normalized_id = normalize_countermeasure_id(project_id, countermeasure_id)
    result = api_client.add_task_note(project_id, normalized_id, note)
    return json.dumps(result, indent=2)


@mcp.tool()
async def get_task_status_choices(ctx: Context) -> str:
    """Get the complete list of ALL available task status choices. Returns all valid status values that can be used when updating countermeasures (e.g., 'Complete', 'Not Applicable', 'In Progress', 'DONE', 'NA'). Use this tool when the user asks: "What task statuses are available?", "What statuses can I use?", "Show me valid status values", "What status values are valid for countermeasures?", or any question about available/valid status options. Task statuses are standardized across all projects. This tool returns the list of possible statuses, NOT the status of a specific countermeasure. For a specific countermeasure's status, use get_countermeasure instead."""
    global api_client
    if api_client is None:
        api_client = init_api_client()
    result = api_client.get_task_status_choices()
    return json.dumps(result, indent=2)

