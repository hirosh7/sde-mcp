"""Response formatter for converting tool results to natural language"""
import json
from typing import Any, Dict


class ResponseFormatter:
    """Formats tool results into natural language responses"""
    
    def format_tool_result(self, tool_name: str, result: Dict[str, Any]) -> str:
        """
        Format a tool result into natural language.
        
        Args:
            tool_name: Name of the tool that was called
            result: The result dictionary from the tool
            
        Returns:
            Formatted natural language string
        """
        # Get tool-specific formatter or use generic
        formatters = {
            "create_project": self._format_project_creation,
            "list_projects": self._format_project_list,
            "get_project": self._format_project_details,
            "update_project": self._format_project_update,
            "create_application": self._format_application_creation,
            "list_applications": self._format_application_list,
            "get_application": self._format_application_details,
            "create_profile": self._format_profile_creation,
            "list_profiles": self._format_profile_list,
            "get_profile": self._format_profile_details,
        }
        
        formatter = formatters.get(tool_name, self._format_generic)
        return formatter(result)
    
    def _format_project_creation(self, result: Dict[str, Any]) -> str:
        """Format project creation result"""
        if result.get("success"):
            project = result.get("project", {})
            name = project.get("name", "Unknown")
            project_id = project.get("id", "Unknown")
            url = project.get("url", "")
            
            response = f"Successfully created project '{name}' (ID: {project_id})"
            if url:
                response += f". You can view it at: {url}"
            return response
        return f"Failed to create project: {result.get('error', 'Unknown error')}"
    
    def _format_project_list(self, result: Dict[str, Any]) -> str:
        """Format project list result"""
        # SD Elements API returns projects in a "results" array
        projects = result.get("results", result.get("projects", []))
        if not projects:
            return "No projects found."
        
        response = f"Found {len(projects)} project(s):\n"
        for idx, proj in enumerate(projects[:10], 1):  # Show first 10
            name = proj.get("name", "Unknown")
            proj_id = proj.get("id", "Unknown")
            status = proj.get("status", "")
            status_str = f" - {status}" if status else ""
            response += f"{idx}. {name} (ID: {proj_id}){status_str}\n"
        
        if len(projects) > 10:
            response += f"\n... and {len(projects) - 10} more projects."
        
        return response.strip()
    
    def _format_project_details(self, result: Dict[str, Any]) -> str:
        """Format project details result"""
        # SD Elements API returns project data directly, not wrapped in "project" key
        # Check if result itself is a project (has "id" field) or if it's wrapped
        if "id" in result and "name" in result:
            # Result is the project object directly
            project = result
        elif "project" in result:
            # Result is wrapped in "project" key
            project = result.get("project", {})
        else:
            return "Project not found."
        
        if not project or not project.get("id"):
            return "Project not found."
        
        name = project.get("name", "Unknown")
        proj_id = project.get("id", "Unknown")
        url = project.get("url", "")
        
        response = f"Project: {name} (ID: {proj_id})"
        if url:
            response += f"\nURL: {url}"
        
        # Add description if available
        description = project.get("description")
        if description:
            response += f"\nDescription: {description}"
        
        # Add created/updated dates (API uses "created" and "updated", not "created_date")
        created = project.get("created") or project.get("created_date")
        if created:
            response += f"\nCreated: {created}"
        
        updated = project.get("updated") or project.get("modified_date")
        if updated:
            response += f"\nUpdated: {updated}"
        
        # Add profile information if available
        profile = project.get("profile")
        if profile:
            profile_name = profile.get("name") if isinstance(profile, dict) else str(profile)
            response += f"\nProfile: {profile_name}"
        
        return response
    
    def _format_project_update(self, result: Dict[str, Any]) -> str:
        """Format project update result"""
        if result.get("success"):
            project = result.get("project", {})
            name = project.get("name", "Unknown")
            return f"Successfully updated project '{name}'"
        return f"Failed to update project: {result.get('error', 'Unknown error')}"
    
    def _format_application_creation(self, result: Dict[str, Any]) -> str:
        """Format application creation result"""
        if result.get("success"):
            app = result.get("application", {})
            name = app.get("name", "Unknown")
            app_id = app.get("id", "Unknown")
            return f"Successfully created application '{name}' (ID: {app_id})"
        return f"Failed to create application: {result.get('error', 'Unknown error')}"
    
    def _format_application_list(self, result: Dict[str, Any]) -> str:
        """Format application list result"""
        applications = result.get("applications", [])
        if not applications:
            return "No applications found."
        
        response = f"Found {len(applications)} application(s):\n"
        for idx, app in enumerate(applications[:10], 1):
            name = app.get("name", "Unknown")
            app_id = app.get("id", "Unknown")
            response += f"{idx}. {name} (ID: {app_id})\n"
        
        if len(applications) > 10:
            response += f"\n... and {len(applications) - 10} more applications."
        
        return response.strip()
    
    def _format_application_details(self, result: Dict[str, Any]) -> str:
        """Format application details result"""
        app = result.get("application", {})
        if not app:
            return "Application not found."
        
        name = app.get("name", "Unknown")
        app_id = app.get("id", "Unknown")
        return f"Application: {name} (ID: {app_id})"
    
    def _format_profile_creation(self, result: Dict[str, Any]) -> str:
        """Format profile creation result"""
        if result.get("success"):
            profile = result.get("profile", {})
            name = profile.get("name", "Unknown")
            profile_id = profile.get("id", "Unknown")
            return f"Successfully created profile '{name}' (ID: {profile_id})"
        return f"Failed to create profile: {result.get('error', 'Unknown error')}"
    
    def _format_profile_list(self, result: Dict[str, Any]) -> str:
        """Format profile list result"""
        profiles = result.get("profiles", [])
        if not profiles:
            return "No profiles found."
        
        response = f"Found {len(profiles)} profile(s):\n"
        for idx, profile in enumerate(profiles[:10], 1):
            name = profile.get("name", "Unknown")
            profile_id = profile.get("id", "Unknown")
            response += f"{idx}. {name} (ID: {profile_id})\n"
        
        if len(profiles) > 10:
            response += f"\n... and {len(profiles) - 10} more profiles."
        
        return response.strip()
    
    def _format_profile_details(self, result: Dict[str, Any]) -> str:
        """Format profile details result"""
        profile = result.get("profile", {})
        if not profile:
            return "Profile not found."
        
        name = profile.get("name", "Unknown")
        profile_id = profile.get("id", "Unknown")
        return f"Profile: {name} (ID: {profile_id})"
    
    def _format_generic(self, result: Dict[str, Any]) -> str:
        """Generic formatter for unknown tool results"""
        # Handle success/error responses
        if "success" in result:
            if result["success"]:
                message = result.get("message", "Operation completed successfully")
                # Include key data if present
                for key in ["project", "application", "profile", "result"]:
                    if key in result and result[key]:
                        data = result[key]
                        if isinstance(data, dict):
                            message += f"\n\n{key.title()}: {json.dumps(data, indent=2)}"
                        else:
                            message += f"\n\n{key.title()}: {data}"
                return message
            else:
                return f"Operation failed: {result.get('error', 'Unknown error')}"
        
        # Format as structured text
        formatted_parts = []
        for key, value in result.items():
            if isinstance(value, (dict, list)):
                formatted_parts.append(f"{key}:\n{json.dumps(value, indent=2)}")
            else:
                formatted_parts.append(f"{key}: {value}")
        
        return "\n".join(formatted_parts) if formatted_parts else json.dumps(result, indent=2)

