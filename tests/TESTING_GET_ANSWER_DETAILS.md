# Testing Guide for `get_answer_details_from_ids` Tool

This guide explains how to test the new `get_answer_details_from_ids` tool that retrieves question and answer text for survey answer IDs.

## Overview

The `get_answer_details_from_ids` tool allows users to understand what survey answer IDs represent by returning the associated question text and answer text. This is particularly useful when working with profiles, which contain lists of answer IDs.

## Running Unit Tests

### Prerequisites

Make sure you have the test dependencies installed:

```bash
# From project root
pip install -e ".[test]"  # For unit tests
# OR
uv sync --all-extras      # Includes all test dependencies
```

### Run Unit Tests

```bash
# From project root directory
pytest tests/test_get_answer_details_from_ids.py -v
```

### Run Specific Test Classes

```bash
# Test API client methods only
pytest tests/test_get_answer_details_from_ids.py::TestGetLibraryQuestion -v
pytest tests/test_get_answer_details_from_ids.py::TestGetAnswerDetailsFromIds -v

# Test MCP tool only
pytest tests/test_get_answer_details_from_ids.py::TestGetAnswerDetailsFromIdsTool -v

# Test integration flow
pytest tests/test_get_answer_details_from_ids.py::TestAnswerDetailsIntegration -v
```

### Run with Coverage

```bash
pytest tests/test_get_answer_details_from_ids.py --cov=sde_mcp_server.api_client --cov=sde_mcp_server.tools.surveys -v
```

## Testing the Tool Manually

### Using MCP Inspector

1. Start the MCP server:
   ```bash
   python -m sde_mcp_server
   ```

2. In another terminal, start the MCP Inspector:
   ```bash
   npx @modelcontextprotocol/inspector python -m sde_mcp_server
   ```

3. In the inspector, you can call the tool:
   - Tool name: `get_answer_details_from_ids`
   - Parameters: `{"answer_ids": ["A701", "A493"]}`

### Using a Real MCP Client (Cursor, Claude Desktop, etc.)

1. Configure your MCP client with the SD Elements server (see main README.md)

2. Ask questions like:
   - "What question and answer is related to answer ID A701?"
   - "Get details for answer IDs A701 and A493"
   - "What does answer ID A701 mean?"
   - "Show me the question and answer for answer ID A701"

3. The tool should return JSON with:
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
       }
     ],
     "not_found": []
   }
   ```

## Example Use Cases

### Use Case 1: Understanding Profile Answer IDs

1. List profiles:
   ```
   "List all profiles"
   ```

2. Get a specific profile (which contains answer IDs):
   ```
   "Get profile 1"
   ```

3. Get details for the answer IDs from the profile:
   ```
   "What question and answer is related to answer ID A701?"
   ```

### Use Case 2: Batch Lookup

If you have multiple answer IDs from a profile:

```
"Get details for answer IDs A701, A493, A21, A1252"
```

The tool will return details for all found answers and list any that weren't found.

### Use Case 3: Understanding Survey Answers

When working with survey data, you might have answer IDs but need to understand what they mean:

```
"What does answer ID A701 mean?"
```

This will return the question text and answer text, making it human-readable.

## Integration Tests (CSV-Driven)

The tool is also included in the CSV-driven prompt mapping tests. To run those:

```bash
# Requires OpenAI API key
pytest tests/test_prompt_mapping_from_csv.py -m 'integration and not unit' -v
```

The CSV file (`tests/prompts_tool_mapping.csv`) includes test prompts like:
- "What question and answer is related to answer ID A701"
- "Get details for answer IDs A701 and A493"
- "What does answer ID A701 mean?"

## Expected Behavior

### Success Case

When answer IDs are found:
- Returns `answers` array with full details
- Each answer includes: `id`, `text`, `question_id`, `question_text`, and optional question metadata
- Returns empty `not_found` array

### Partial Success

When some answer IDs are found and some are not:
- Returns `answers` array with found answers
- Returns `not_found` array with IDs that weren't found

### Failure Case

When no answer IDs are found:
- Returns empty `answers` array
- Returns `not_found` array with all requested IDs

## Troubleshooting

### Tool Not Found

If the tool doesn't appear in your MCP client:
1. Ensure the server is running with the latest code
2. Check that `src/sde_mcp_server/tools/surveys.py` includes the new tool
3. Verify the tool is imported in `src/sde_mcp_server/tools/__init__.py`

### Empty Results

If you get empty results:
1. Verify the answer IDs exist in your SD Elements instance
2. Check that the library answers cache is loaded (happens automatically)
3. Verify your API key has permissions to access library data

### Question Details Missing

If question text is missing:
1. The tool falls back to extracting from `display_text` if the questions endpoint fails
2. Check API permissions for `library/questions/` endpoint
3. Verify the question IDs are valid

## Test Coverage

The unit tests cover:
- ✅ Single answer ID lookup
- ✅ Multiple answer ID lookup
- ✅ Not found answer IDs
- ✅ Mixed found/not found scenarios
- ✅ Empty input handling
- ✅ Cache loading
- ✅ Question fetch failure handling
- ✅ Display text extraction fallback
- ✅ MCP tool integration
- ✅ JSON serialization

## Next Steps

After testing:
1. Verify the tool works with real SD Elements data
2. Test with various answer IDs from your instance
3. Verify the tool integrates well with profile workflows
4. Check that the tool description is clear for LLMs to use it appropriately

