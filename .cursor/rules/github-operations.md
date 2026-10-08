# GitHub Operations Rule

When performing GitHub operations (repository management, branch operations, pull requests, issues, etc.), follow this priority order:

## 1. Primary: Use GitHub MCP Tools
Always attempt to use the GitHub MCP tools configured in Cursor first. These tools provide a standardized interface and are preferred because:
- They are integrated with Cursor's MCP system
- They handle authentication automatically
- They provide consistent error handling
- They are optimized for the Cursor environment

Available GitHub MCP tools include:
- `mcp_github_list_branches` - List branches
- `mcp_github_create_branch` - Create branches
- `mcp_github_list_pull_requests` - List PRs
- `mcp_github_create_pull_request` - Create PRs
- `mcp_github_issue_read` / `mcp_github_issue_write` - Issue operations
- `mcp_github_get_file_contents` - Read files
- `mcp_github_create_or_update_file` - Write files
- And other GitHub MCP tools as available

## 2. Fallback: GitHub API
If the GitHub MCP tool:
- Is not available for the specific operation needed
- Fails with an error that suggests the operation isn't supported
- Returns an error that indicates API-level access is required

Then fall back to using the GitHub API directly via:
- `mcp_github_api_request` - For custom API endpoints (if available)
- Terminal commands with `curl` or `gh` CLI tool
- Direct HTTP requests to GitHub REST API

## 3. Last Resort: Terminal Git Commands
For local git operations (not requiring GitHub API), use terminal commands:
- `git branch` - Local branch operations
- `git checkout` - Switch branches
- `git merge` - Merge branches
- `git push` / `git pull` - Sync with remote

## Examples

### Branch Operations
1. **First try**: `mcp_github_list_branches` to see available branches
2. **If deletion needed and MCP doesn't support it**: Use `git push origin --delete <branch>` or GitHub API
3. **For local operations**: Use `git branch -D <branch>`

### File Operations
1. **First try**: `mcp_github_get_file_contents` to read files
2. **First try**: `mcp_github_create_or_update_file` to write files
3. **Fallback**: Use GitHub API directly if MCP tools don't support the operation

### Pull Request Operations
1. **First try**: `mcp_github_list_pull_requests` to list PRs
2. **First try**: `mcp_github_create_pull_request` to create PRs
3. **First try**: `mcp_github_pull_request_read` to read PR details
4. **Fallback**: Use GitHub API if specific operation isn't available

## Important Notes
- Always check what MCP tools are available before falling back
- Document when and why you fall back to API/terminal commands
- Prefer MCP tools for consistency and better integration with Cursor
- Terminal commands should only be used for local git operations or when MCP/API are unavailable
