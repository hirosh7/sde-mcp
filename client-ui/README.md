# Client UI

A simple web interface for sending natural language queries to SD Elements via the Mock Seaglass service.

## Features

- Clean, chat-like interface
- Example queries for quick testing
- Response time display
- Error handling and display

## Running Locally

```bash
# Using Python's built-in HTTP server
cd static
python -m http.server 8080
```

Then open `http://localhost:8080` in your browser.

## Docker

```bash
# Build
docker build -t client-ui .

# Run
docker run -p 8080:8080 client-ui
```

## Configuration

The UI connects to the Mock Seaglass service at `http://localhost:8003` by default. To change this, edit `static/app.js` and update the `SEAGLASS_URL` constant.

## Example Queries

- "List all projects"
- "Create a new project called Mobile Banking App"
- "Get details for project 29023"
- "Show me projects created this month"

