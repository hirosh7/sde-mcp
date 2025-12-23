#!/usr/bin/env node

import express from "express";
import { randomUUID } from "node:crypto";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import { isInitializeRequest } from "@modelcontextprotocol/sdk/types.js";
import { createServer, setupSignalHandlers } from "./server.js";

const PORT = parseInt(process.env.PORT || "8001", 10);
const HOST = process.env.HOST || "0.0.0.0";

export async function startHttpServer(): Promise<void> {
  const app = express();
  app.use(express.json());
  
  // Track active transports by session ID
  const transports: Record<string, StreamableHTTPServerTransport> = {};
  
  // Health check endpoint
  app.get("/health", (_req, res) => {
    res.json({ status: "ok", timestamp: new Date().toISOString() });
  });

  // MCP POST endpoint - handles requests and initialization
  app.post("/mcp", async (req, res) => {
    const sessionId = req.headers["mcp-session-id"] as string | undefined;
    let transport: StreamableHTTPServerTransport;

    if (sessionId && transports[sessionId]) {
      // Reuse existing session
      transport = transports[sessionId];
    } else if (!sessionId && isInitializeRequest(req.body)) {
      // New session initialization
      transport = new StreamableHTTPServerTransport({
        sessionIdGenerator: () => randomUUID(),
        onsessioninitialized: (id) => {
          transports[id] = transport;
          console.error(`MCP session initialized: ${id}`);
        },
        onsessionclosed: (id) => {
          delete transports[id];
          console.error(`MCP session closed: ${id}`);
        },
      });

      transport.onclose = () => {
        if (transport.sessionId) {
          delete transports[transport.sessionId];
        }
      };

      const server = createServer();
      await server.connect(transport);
    } else {
      res.status(400).json({
        jsonrpc: "2.0",
        error: { code: -32000, message: "Invalid session" },
        id: null,
      });
      return;
    }

    await transport.handleRequest(req, res, req.body);
  });

  // MCP GET endpoint - handles SSE streams
  app.get("/mcp", async (req, res) => {
    const sessionId = req.headers["mcp-session-id"] as string;
    const transport = transports[sessionId];
    if (transport) {
      await transport.handleRequest(req, res);
    } else {
      res.status(400).send("Invalid session");
    }
  });

  // MCP DELETE endpoint - handles session cleanup
  app.delete("/mcp", async (req, res) => {
    const sessionId = req.headers["mcp-session-id"] as string;
    const transport = transports[sessionId];
    if (transport) {
      await transport.handleRequest(req, res);
    } else {
      res.status(400).send("Invalid session");
    }
  });

  // Start the HTTP server
  const httpServer = app.listen(PORT, HOST, () => {
    console.error(`MCP HTTP server running on http://${HOST}:${PORT}/mcp`);
  });

  // Set up signal handlers for graceful shutdown
  setupSignalHandlers(async () => {
    console.error("Shutting down HTTP server...");
    // Close all active transports
    Object.values(transports).forEach((t) => t.close());
    httpServer.close();
  });
}

// Run the HTTP server if this file is executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  startHttpServer().catch((err: unknown) => {
    console.error("Failed to start HTTP server:", err);
    process.exit(1);
  });
}

