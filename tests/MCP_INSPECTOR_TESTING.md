# Testing `get_answer_details_from_ids` with MCP Inspector (WSL)

This guide shows you how to test the new `get_answer_details_from_ids` tool using the Model Context Protocol Inspector in WSL (Windows Subsystem for Linux).

## Prerequisites

1. **WSL installed and configured**
   - WSL 2 recommended
   - Access to your project files (either in WSL filesystem or mounted Windows drive)

2. **Node.js and npm installed in WSL**
   ```bash
   # Check if installed
   node --version
   npm --version
   
   # If not installed, install Node.js:
   # Ubuntu/Debian:
   curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
   sudo apt-get install -y nodejs
   ```

3. **Python installed in WSL**
   ```bash
   # Check if installed
   python3 --version
   
   # If not installed:
   sudo apt update
   sudo apt install python3 python3-pip python3-venv
   ```

4. **Virtual Environment and Project Dependencies**
   
   **WSL/Ubuntu requires a virtual environment** (Python 3.12+ prevents system-wide installs).
   
   **If you have a Windows `.venv` already:**
   - **Option A (Recommended):** Create a separate WSL venv to keep both working:
     ```bash
     # Create WSL-specific venv
     python3 -m venv .venv-wsl
     source .venv-wsl/bin/activate
     ```
   - **Option B:** Replace the Windows venv (if you only use WSL now):
     ```bash
     # Remove Windows venv and create new one for WSL
     rm -rf .venv
     python3 -m venv .venv
     source .venv/bin/activate
     ```
   
   **If no venv exists yet:**
   ```bash
   # Navigate to project ROOT directory (where pyproject.toml is)
   cd /mnt/c/Users/kjohnson/Documents/sandbox/Cursor/sde-mcp
   # OR if in WSL filesystem:
   # cd ~/sde-mcp
   
   # Verify you're in the right place
   ls -la  # Should show pyproject.toml, README.md, src/, tests/
   
   # Create virtual environment
   python3 -m venv .venv-wsl  # or .venv if replacing Windows one
   
   # Activate the virtual environment
   source .venv-wsl/bin/activate  # or .venv/bin/activate
   
   # Your prompt should now show (.venv-wsl) or (.venv) at the beginning
   
   # Install the project (this installs dependencies and makes the package importable)
   pip install -e .
   
   # Verify installation
   python -c "import sde_mcp_server; print('✓ Package installed correctly')"
   ```
   
   **Note:** After activating the venv, you can use `python` and `pip` instead of `python3` and `pip3`.

## Step-by-Step Instructions

### Step 1: Navigate to Project Root Directory

**IMPORTANT:** You must be in the project root directory (where `pyproject.toml` is), NOT inside `src/` or `src/sde_mcp_server/`.

**If project is in Windows filesystem (mounted):**
```bash
cd /mnt/c/Users/kjohnson/Documents/sandbox/Cursor/sde-mcp
```

**If project is in WSL filesystem:**
```bash
cd ~/path/to/sde-mcp
```

**Verify you're in the right place:**
```bash
# You should see these files/directories:
ls -la
# Should show: pyproject.toml, README.md, src/, tests/, etc.
# You should NOT be inside src/ or src/sde_mcp_server/
```

### Step 2: Activate Virtual Environment

**If you have a Windows `.venv` and want to keep it:**

```bash
# Create a separate WSL venv (recommended)
python3 -m venv .venv-wsl
source .venv-wsl/bin/activate
```

**If you want to replace the Windows venv:**

```bash
# Remove Windows venv
rm -rf .venv

# Create new WSL venv
python3 -m venv .venv
source .venv/bin/activate
```

**If the WSL virtual environment already exists:**

```bash
# Activate it (use .venv-wsl if you created that, or .venv if you replaced)
source .venv-wsl/bin/activate
# OR
source .venv/bin/activate
```

**Verify activation:**
```bash
which python  # Should show: /path/to/sde-mcp/.venv-wsl/bin/python (or .venv/bin/python)
pip --version  # Should work without errors
# Your prompt should show (.venv-wsl) or (.venv) at the beginning
```

### Step 3: Set Environment Variables

**Option 1: Export in current session (REQUIRED for inspector)**
```bash
# MUST use 'export' not just assignment - this makes vars available to child processes
export SDE_HOST="https://your-instance.sdelements.com"
export SDE_API_KEY="your-api-key-here"

# Verify they're exported (available to subprocesses)
env | grep SDE  # Should show both variables
echo $SDE_HOST
echo $SDE_API_KEY
```

**Option 2: Create `.env` file in project root (RECOMMENDED - auto-loaded by server)**
```bash
# Create .env file (server auto-loads this via python-dotenv)
cat > .env << EOF
SDE_HOST=https://your-instance.sdelements.com
SDE_API_KEY=your-api-key-here
EOF

# Verify file exists
cat .env
```

**Option 3: Add to `~/.bashrc` or `~/.zshrc` (persistent)**
```bash
# Add to ~/.bashrc or ~/.zshrc
echo 'export SDE_HOST="https://your-instance.sdelements.com"' >> ~/.bashrc
echo 'export SDE_API_KEY="your-api-key-here"' >> ~/.bashrc
source ~/.bashrc  # Reload shell config

# Verify
env | grep SDE
```

**Why `export` is critical:**
- The inspector runs Python as a **subprocess** (child process)
- Only **exported** variables are inherited by child processes
- Without `export`, variables are only in the current shell, not subprocesses
- The server's `load_dotenv()` will load `.env` file, but exported vars are still needed for the inspector subprocess

### Step 4: Install Project (If Not Already Installed)

**If you just created the virtual environment, install the project:**

```bash
# Make sure venv is activated (prompt shows (.venv))
pip install -e .
```

**If already installed, skip this step.**

### Step 5: Test Server Startup (Recommended First)

**Before using the inspector, verify the server starts correctly:**

**IMPORTANT:** Make sure you're in the project ROOT directory (where `pyproject.toml` is):

```bash
# Verify you're in project root
pwd  # Should show: /mnt/c/Users/kjohnson/Documents/sandbox/Cursor/sde-mcp
ls -la  # Should show pyproject.toml, README.md, src/, tests/

# Test server startup
python3 -m sde_mcp_server
```

**Common mistake:** Don't run from inside `src/` or `src/sde_mcp_server/` directories!

**Expected behavior:**
- Server should start and wait (no errors)
- If you see "Configuration error", your environment variables aren't set
- Press `Ctrl+C` to stop the test

**If you see errors:**
- Check environment variables: `echo $SDE_HOST $SDE_API_KEY`
- Verify `.env` file exists and has correct values
- See troubleshooting section below

### Step 6: Start the MCP Inspector

Once the server starts correctly on its own, start the inspector:

**IMPORTANT:** 
- Make sure you're still in the project ROOT directory
- Make sure virtual environment is activated (if using one)
- **CRITICAL:** Environment variables must be exported in the same shell session

```bash
# Verify location
pwd  # Should be project root, not inside src/

# Verify venv is activated (if using one)
which python  # Should show .venv-wsl/bin/python or .venv/bin/python

# CRITICAL: Export environment variables in the SAME shell session
export SDE_HOST="https://your-instance.sdelements.com"
export SDE_API_KEY="your-api-key-here"

# Verify environment variables are exported
env | grep SDE  # Should show SDE_HOST and SDE_API_KEY

# Start inspector (env vars will be inherited by the subprocess)
# IMPORTANT: Use venv Python, NOT system python3!

# Option 1: With venv activated and env vars exported (RECOMMENDED)
source .venv-wsl/bin/activate  # Make sure venv is activated first!
export SDE_HOST="https://your-instance.sdelements.com"
export SDE_API_KEY="your-api-key"
npx @modelcontextprotocol/inspector python -m sde_mcp_server

# Option 2: Using full path to venv Python (MOST RELIABLE - use this if Option 1 fails)
export SDE_HOST="https://your-instance.sdelements.com"
export SDE_API_KEY="your-api-key"
npx @modelcontextprotocol/inspector .venv-wsl/bin/python -m sde_mcp_server

# Option 3: Inline environment variables with venv Python
SDE_HOST="https://your-instance.sdelements.com" \
SDE_API_KEY="your-api-key" \
npx @modelcontextprotocol/inspector .venv-wsl/bin/python -m sde_mcp_server
```

**Note:** 
- The first time you run this, it will download the inspector package. This is normal.
- **CRITICAL:** Use venv Python (`.venv-wsl/bin/python`), NOT system `python3` - system Python doesn't have the package installed
- If you get "No module named sde_mcp_server", you're using system Python - use Option 2 with full venv path
- **CRITICAL:** Environment variables must be `export`ed in the same shell session, not just set
- **Alternative:** Create `.env` file in project root - the server will auto-load it
- **Critical:** Must run from project root where `pyproject.toml` is located

### Step 7: Access the Web Interface

Once the inspector starts, you'll see:

1. **Terminal output** showing:
   ```
   MCP Inspector running at http://localhost:5173
   ```

2. **Open the web interface** in your Windows browser:
   - Open Windows browser (Chrome, Edge, Firefox)
   - Navigate to: `http://localhost:5173`
   - **Note:** WSL2 uses port forwarding, so `localhost` should work from Windows

3. **If localhost doesn't work**, you may need to:
   - Find the WSL IP address: `ip addr show eth0 | grep inet`
   - Use that IP instead: `http://<WSL_IP>:5173`
   - Or set up port forwarding (see troubleshooting below)

### Step 8: Use the Inspector

In the web interface:

1. **Find the tool**: Look for `get_answer_details_from_ids` in the list of available tools
2. **Click on it** or select it from the tools list
3. **Enter parameters** in JSON format:
   ```json
   {
     "answer_ids": ["A701", "A493"]
   }
   ```
4. **Click "Call Tool"** or press Enter

### Step 9: View Results

The tool will return JSON with question and answer details:

```json
{
  "answers": [
    {
      "id": "A701",
      "text": "Java",
      "question_id": "Q100",
      "question_text": "What programming language do you use?",
      "description": "Java programming language",
      "question_description": "Select the primary programming language",
      "question_format": "MC",
      "question_mandatory": true
    },
    {
      "id": "A493",
      "text": "PostgreSQL",
      "question_id": "Q200",
      "question_text": "What database do you use?",
      "description": "PostgreSQL database",
      "question_description": "Select the database technology",
      "question_format": "MC",
      "question_mandatory": false
    }
  ],
  "not_found": []
}
```

## Example Test Cases

### Test Case 1: Single Answer ID

**Input:**
```json
{
  "answer_ids": ["A701"]
}
```

**Expected:** Returns details for answer ID A701 with question and answer text.

### Test Case 2: Multiple Answer IDs

**Input:**
```json
{
  "answer_ids": ["A701", "A493", "A21"]
}
```

**Expected:** Returns details for all three answer IDs.

### Test Case 3: Non-existent Answer ID

**Input:**
```json
{
  "answer_ids": ["A999"]
}
```

**Expected:** Returns empty `answers` array and `["A999"]` in `not_found` array.

### Test Case 4: Mixed Found and Not Found

**Input:**
```json
{
  "answer_ids": ["A701", "A999", "A493"]
}
```

**Expected:** Returns details for A701 and A493 in `answers`, and `["A999"]` in `not_found`.

## Troubleshooting

### Inspector Won't Start

**Error:** `npx: command not found`
- **Solution:** Install Node.js in WSL:
  ```bash
  curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
  sudo apt-get install -y nodejs
  ```

**Error:** `python: command not found` or `python3: command not found`
- **Solution:** Install Python in WSL:
  ```bash
  sudo apt update
  sudo apt install python3 python3-pip python3-venv
  ```
- Then create and activate a virtual environment:
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -e .
  ```
- Use the venv's Python with inspector:
  ```bash
  # Make sure venv is activated, then:
  npx @modelcontextprotocol/inspector python -m sde_mcp_server
  # Or use full path (adjust .venv-wsl if you used that name):
  npx @modelcontextprotocol/inspector .venv-wsl/bin/python -m sde_mcp_server
  # OR if using .venv:
  npx @modelcontextprotocol/inspector .venv/bin/python -m sde_mcp_server
  ```

**Error:** `No module named sde_mcp_server` (from inspector notifications)
- **Cause:** The inspector is using system Python (`/usr/bin/python3`) which doesn't have the package installed. The package is only installed in your virtual environment.
- **Solution:** Use the virtual environment Python explicitly
  
  **Step 1: Verify venv exists and package is installed**
     ```bash
     # Go to project root
     cd /mnt/c/Users/kjohnson/Documents/sandbox/Cursor/sde-mcp
     
     # Activate venv
     source .venv-wsl/bin/activate  # or .venv/bin/activate if you used that name
     
     # Verify package is installed
     python -c "import sde_mcp_server; print('✓ Package installed in venv')"
     ```
  
  **Step 2: Use full path to venv Python in inspector**
     ```bash
     # Export env vars
     export SDE_HOST="https://your-instance.sdelements.com"
     export SDE_API_KEY="your-api-key"
     
     # Use FULL PATH to venv Python (not just 'python')
     npx @modelcontextprotocol/inspector .venv-wsl/bin/python -m sde_mcp_server
     
     # If you named it .venv instead of .venv-wsl:
     # npx @modelcontextprotocol/inspector .venv/bin/python -m sde_mcp_server
     ```
  
  **Why this happens:**
  - Inspector defaults to system Python (`/usr/bin/python3`) if you just say `python3`
  - System Python doesn't have your package installed
  - Virtual environment isolates your package - you must use venv Python explicitly
  - Using full path (`.venv-wsl/bin/python`) ensures inspector uses the correct Python

**Error:** `externally-managed-environment` or `ModuleNotFoundError: No module named 'dotenv'`
- **Cause:** 
  - Not using a virtual environment (Python 3.12+ requires venv)
  - Project dependencies aren't installed
  - Running from the wrong directory
- **Solution:** 
  1. **Make sure you're in the project ROOT directory** (where `pyproject.toml` is):
     ```bash
     # Go to project root (NOT inside src/ or src/sde_mcp_server/)
     cd /mnt/c/Users/kjohnson/Documents/sandbox/Cursor/sde-mcp
     
     # Verify location
     ls -la  # Should show pyproject.toml, README.md, src/, tests/
     ```
  
  2. **Create and activate virtual environment:**
     ```bash
     # Create venv (one-time, if it doesn't exist)
     python3 -m venv .venv-wsl
     
     # Activate it
     source .venv-wsl/bin/activate
     
     # Your prompt should show (.venv-wsl) at the beginning
     ```
  
  3. **Install the project:**
     ```bash
     # Make sure venv is activated (prompt shows (.venv-wsl))
     pip install -e .
     ```
     This installs all dependencies and makes `sde_mcp_server` importable.
  
  4. **Verify installation:**
     ```bash
     python -c "import sde_mcp_server; print('✓ Installed')"
     ```
  
  5. **Run from project root:**
     ```bash
     # Make sure venv is activated, then from project root:
     python -m sde_mcp_server
     # NOT: python3 -m server (wrong!)
     # NOT from inside src/sde_mcp_server/ directory
     ```

**Error:** `Permission denied` when accessing Windows files
- **Solution:** Make sure you have proper permissions. You may need to:
  ```bash
  # Check file permissions
  ls -la /mnt/c/Users/kjohnson/Documents/sandbox/Cursor/sde-mcp
  
  # If needed, copy project to WSL filesystem
  cp -r /mnt/c/Users/kjohnson/Documents/sandbox/Cursor/sde-mcp ~/sde-mcp
  cd ~/sde-mcp
  ```

### Web Interface Not Accessible

**Issue:** Can't access `http://localhost:5173` from Windows browser

**Solution 1: Check WSL IP and use it directly**
```bash
# In WSL, get your IP
ip addr show eth0 | grep "inet\b" | awk '{print $2}' | cut -d/ -f1

# Use that IP in Windows browser: http://<WSL_IP>:5173
```

**Solution 2: Set up port forwarding (WSL2)**
```powershell
# In Windows PowerShell (as Administrator)
netsh interface portproxy add v4tov4 listenport=5173 listenaddress=0.0.0.0 connectport=5173 connectaddress=<WSL_IP>
```

**Solution 3: Use WSL hostname**
- In Windows browser, try: `http://<WSL_HOSTNAME>:5173`
- Find hostname: `hostname` command in WSL

**Solution 4: Use Windows Terminal with WSL**
- The inspector might open automatically in Windows Terminal
- Check the terminal output for the URL

### Server Connection Issues

**Error:** `SSE connection not established` or `Error in /message route`
- **Cause:** The MCP server crashed on startup before the inspector could establish a connection. Common causes:
  1. Missing environment variables (SDE_HOST, SDE_API_KEY)
  2. Package not installed (ModuleNotFoundError)
  3. Server exits with error before SSE connection is established

- **Solution - Step by Step:**
  
  **Step 1: Test the server independently**
     ```bash
     # In WSL, from project root, test if server starts correctly
     python3 -m sde_mcp_server
     ```
     - If you see "Configuration error: SDE_HOST environment variable is required" → env vars not set
     - If you see "ModuleNotFoundError: No module named 'sde_mcp_server'" → package not installed
     - If the server starts and waits, that's good - press Ctrl+C to stop it
  
  **Step 2: Install package in a virtual environment (RECOMMENDED)**
     ```bash
     # Create and activate venv
     python3 -m venv .venv-wsl
     source .venv-wsl/bin/activate
     
     # Install the project
     pip install -e .
     
     # Test again
     python -m sde_mcp_server
     ```
  
  **Step 3: Set environment variables (MUST use export)**
     ```bash
     # CRITICAL: Must use 'export' not just assignment
     export SDE_HOST="https://your-instance.sdelements.com"
     export SDE_API_KEY="your-api-key-here"
     
     # Verify they're exported (available to child processes)
     env | grep SDE  # Should show both
     ```
     
     **OR create .env file (server auto-loads this):**
     ```bash
     # Copy example and edit
     cp env.example .env
     # Edit .env and add your values
     nano .env  # or use your preferred editor
     
     # Verify .env file
     cat .env
     ```
     
     **Note:** `.env` file is automatically loaded by the server, but you still need to `export` variables if running inspector in the same shell session.
  
  **Step 4: Test server with environment variables**
     ```bash
     # With venv activated and env vars set
     python -m sde_mcp_server
     # Should start without errors
     ```
  
  **Step 5: Run inspector with venv Python**
     ```bash
     # Make sure venv is activated
     source .venv-wsl/bin/activate  # or .venv/bin/activate
     
     # Verify env vars are set
     env | grep SDE
     
     # Run inspector using venv Python
     npx @modelcontextprotocol/inspector python -m sde_mcp_server
     
     # OR use full path to venv Python
     npx @modelcontextprotocol/inspector .venv-wsl/bin/python -m sde_mcp_server
     ```
  
  **Alternative: Run inspector with explicit environment variables**
     ```bash
     # Set variables and run in same command (no venv needed if package is installed)
     SDE_HOST="https://your-instance.sdelements.com" \
     SDE_API_KEY="your-api-key" \
     npx @modelcontextprotocol/inspector python3 -m sde_mcp_server
     ```

**Error:** Authentication failed
- **Solution:** 
  - Verify your `SDE_HOST` and `SDE_API_KEY` are set correctly:
    ```bash
    echo $SDE_HOST
    echo $SDE_API_KEY
    ```
  - Check that your API key has proper permissions
  - Make sure `.env` file is in the project root if using that method
  - Test connection manually (see above)

**Error:** Connection timeout
- **Solution:** 
  - Verify your SD Elements instance is accessible from WSL:
    ```bash
    curl -I https://your-instance.sdelements.com
    ```
  - Check network connectivity
  - If using VPN, make sure it's accessible from WSL

### Tool Not Found

**Issue:** `get_answer_details_from_ids` doesn't appear in the tools list
- **Solution:** 
  1. Make sure you're running the latest code from the feature branch
  2. Restart the inspector
  3. Check that the tool is properly registered in `src/sde_mcp_server/tools/surveys.py`

### Empty Results

**Issue:** Tool returns empty results
- **Solution:** 
  1. Verify the answer IDs exist in your SD Elements instance
  2. Check that the library answers cache loaded successfully (check server logs)
  3. Try with known answer IDs from your instance

## Getting Answer IDs to Test

To get real answer IDs from your SD Elements instance:

1. **From a Profile:**
   - Use `list_profiles` tool to see available profiles
   - Use `get_profile` with a profile ID to see the answer IDs in that profile

2. **From a Project Survey:**
   - Use `get_project_survey` with a project ID
   - Look at the `answers` field to see answer IDs

3. **From Library Answers:**
   - The tool uses cached library answers
   - Answer IDs typically start with "A" (e.g., "A1", "A21", "A701")

## Alternative: Command Line Testing

If you prefer command-line testing, you can also test the API client directly in WSL:

```bash
# Start Python3 interactive shell
python3
```

```python
from sde_mcp_server.api_client import SDElementsAPIClient
import os

# Make sure environment variables are set
client = SDElementsAPIClient(
    host=os.getenv("SDE_HOST"),
    api_key=os.getenv("SDE_API_KEY")
)

# Load library answers cache
client.load_library_answers()

# Test the method
result = client.get_answer_details_from_ids(["A701", "A493"])
print(result)
```

Or create a test script:

```bash
# Create test script
cat > test_tool.py << 'EOF'
from sde_mcp_server.api_client import SDElementsAPIClient
import os
import json

client = SDElementsAPIClient(
    host=os.getenv("SDE_HOST"),
    api_key=os.getenv("SDE_API_KEY")
)

client.load_library_answers()
result = client.get_answer_details_from_ids(["A701", "A493"])
print(json.dumps(result, indent=2))
EOF

# Run it
python3 test_tool.py
```

## Next Steps

After testing with the inspector:

1. ✅ Verify the tool works with real answer IDs from your instance
2. ✅ Test with various answer IDs (single, multiple, not found)
3. ✅ Verify the question and answer text are correct
4. ✅ Test integration with profile workflows (get profile → get answer details)

## WSL-Specific Tips

### Working with Windows Filesystem

If your project is on the Windows filesystem (`/mnt/c/...`):

1. **Performance:** WSL2 can be slower with Windows filesystem. For better performance:
   ```bash
   # Copy project to WSL filesystem
   cp -r /mnt/c/Users/kjohnson/Documents/sandbox/Cursor/sde-mcp ~/sde-mcp
   cd ~/sde-mcp
   ```

2. **Line Endings:** Git may show warnings about CRLF/LF. This is normal and won't affect functionality.

3. **Permissions:** Some operations may require different permissions on Windows filesystem.

### Quick Reference Commands

```bash
# Check Node.js
node --version
npm --version

# Check Python
python3 --version
which python3

# Navigate to project (Windows filesystem)
cd /mnt/c/Users/kjohnson/Documents/sandbox/Cursor/sde-mcp

# Navigate to project (WSL filesystem)
cd ~/sde-mcp

# Create and activate virtual environment
# Option 1: Separate WSL venv (keeps Windows venv)
python3 -m venv .venv-wsl
source .venv-wsl/bin/activate

# Option 2: Replace Windows venv
# rm -rf .venv
# python3 -m venv .venv
# source .venv/bin/activate

# Install project (in venv)
pip install -e .

# Check environment variables
env | grep SDE

# Run inspector (with venv activated)
npx @modelcontextprotocol/inspector python -m sde_mcp_server

# Or use full path to venv Python (adjust name if needed)
npx @modelcontextprotocol/inspector .venv-wsl/bin/python -m sde_mcp_server
```

## Additional Resources

- [MCP Inspector Documentation](https://github.com/modelcontextprotocol/inspector)
- [SD Elements API Documentation](https://docs.sdelements.com/master/api/docs/)
- [WSL Documentation](https://docs.microsoft.com/en-us/windows/wsl/)
- Main project README: `README.md`
- Full testing guide: `tests/TESTING_GET_ANSWER_DETAILS.md`

