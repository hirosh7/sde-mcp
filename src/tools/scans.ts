/**
 * Repository scanning tools
 * Translated from: https://github.com/sdelements/sde-mcp/blob/master/src/sde_mcp_server/tools/scans.py
 */

import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import {
  SDElementsClient,
  type SDElementsQueryParams,
} from "../utils/apiClient.js";

/**
 * Register all repository scanning tools
 */
export function registerScanTools(
  server: McpServer,
  client: SDElementsClient
): void {
  // List scan connections
  server.registerTool(
    "list_scan_connections",
    {
      title: "List Scan Connections",
      description: "List repository scan connections",
      inputSchema: z.object({}),
    },
    async () => {
      const result = await client.get("team-onboarding-connections/");

      return {
        content: [{ type: "text", text: JSON.stringify(result, null, 2) }],
      };
    }
  );

  // Scan repository
  server.registerTool(
    "scan_repository",
    {
      title: "Scan Repository",
      description: "Scan a repository",
      inputSchema: z.object({
        project_id: z.number().describe("ID of the project"),
        connection_id: z.number().describe("ID of the scan connection"),
        repository_url: z.string().describe("URL of the repository to scan"),
      }),
    },
    async ({ project_id, connection_id, repository_url }) => {
      const data = {
        project: project_id,
        connection: connection_id,
        repository_url,
      };

      const result = await client.apiRequest(
        "POST",
        "team-onboarding-scans/",
        data
      );

      return {
        content: [{ type: "text", text: JSON.stringify(result, null, 2) }],
      };
    }
  );

  // Get scan status
  server.registerTool(
    "get_scan_status",
    {
      title: "Get Scan Status",
      description: "Get status of a repository scan",
      inputSchema: z.object({
        scan_id: z.number().describe("ID of the scan"),
      }),
    },
    async ({ scan_id }) => {
      const result = await client.get(`team-onboarding-scans/${scan_id}/`);

      return {
        content: [{ type: "text", text: JSON.stringify(result, null, 2) }],
      };
    }
  );

  // List scans
  server.registerTool(
    "list_scans",
    {
      title: "List Scans",
      description: "List repository scans",
      inputSchema: z.object({
        project_id: z.number().optional().describe("Filter by project ID"),
      }),
    },
    async ({ project_id }) => {
      const params: Record<string, unknown> = {};

      if (project_id !== undefined) {
        params.project = project_id;
      }

      const result = await client.get(
        "team-onboarding-scans/",
        params as SDElementsQueryParams
      );

      return {
        content: [{ type: "text", text: JSON.stringify(result, null, 2) }],
      };
    }
  );
}
