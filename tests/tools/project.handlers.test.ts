import { describe, expect, it, vi, afterEach } from "vitest";
import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import type { SDElementsClient } from "../../src/utils/apiClient.js";
import { registerProjectTools } from "../../src/tools/project.js";

type ToolResult = {
  content: Array<{ type: string; text: string }>;
};
type ToolHandler = (args: Record<string, unknown>) => Promise<ToolResult>;

class TestMcpServer {
  tools = new Map<string, { meta: unknown; handler: ToolHandler }>();
  registerTool(name: string, meta: unknown, handler: ToolHandler) {
    this.tools.set(name, { meta, handler });
  }
}

function parseToolText<T = unknown>(result: ToolResult): T {
  return JSON.parse(result.content[0].text) as T;
}

describe("project tool handlers (unit)", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("create_project returns a clear error when name is missing", async () => {
    const server = new TestMcpServer();
    const client = {} as unknown as SDElementsClient;
    registerProjectTools(server as unknown as McpServer, client);

    const tool = server.tools.get("create_project")!;
    const res = await tool.handler({ application_id: 1 });
    const body = parseToolText<{ error: string }>(res);
    expect(body.error).toMatch(/Project name is required/);
  });

  it("create_project returns available profiles when no default/detection is possible", async () => {
    const server = new TestMcpServer();
    const client = {
      listProfiles: vi.fn().mockResolvedValue({
        results: [
          { id: "A", name: "Alpha", default: false },
          { id: "B", name: "Beta", default: false },
        ],
      }),
    } as unknown as SDElementsClient;

    registerProjectTools(server as unknown as McpServer, client);

    const tool = server.tools.get("create_project")!;
    const res = await tool.handler({
      application_id: 1,
      name: "Some Project",
      description: "no keywords",
    });

    const body = parseToolText<{ error: string; available_profiles: unknown[] }>(
      res
    );
    expect(body.error).toMatch(/Profile is required/);
    expect(body.available_profiles).toEqual([
      { id: "A", name: "Alpha" },
      { id: "B", name: "Beta" },
    ]);
  });

  it("update_project returns an error when risk_policy is a non-numeric string", async () => {
    const server = new TestMcpServer();
    const client = {} as unknown as SDElementsClient;
    registerProjectTools(server as unknown as McpServer, client);

    const tool = server.tools.get("update_project")!;
    const res = await tool.handler({ project_id: 1, risk_policy: "abc" });
    const body = parseToolText<{ error: string; suggestion?: string }>(res);
    expect(body.error).toMatch(/risk_policy must be an integer ID/i);
    expect(body.suggestion).toMatch(/list_risk_policies/i);
  });

  it("get_profile returns profile with answer IDs converted to question/answer text", async () => {
    const server = new TestMcpServer();
    const client = {
      getProfile: vi.fn().mockResolvedValue({
        id: "P2",
        name: "Java EE Web App",
        description: "Java Enterprise Edition Web Application",
        default: false,
        answers: ["A1061", "A740", "A1078"],
      }),
      getAnswerDetailsFromIds: vi.fn().mockResolvedValue({
        answers: [
          {
            id: "A1061",
            text: "Set of default answers for software profiles",
            question_id: "Q1",
            question_text:
              "Internal Properties (Use this, for all hidden answers)",
            question_description: "",
            question_format: "",
            question_mandatory: false,
            description: "",
            display_text:
              "Internal Properties (Use this, for all hidden answers) - Set of default answers for software profiles",
            section_title: null,
            section_id: null,
          },
          {
            id: "A740",
            text: "This is a new project",
            question_id: "Q2",
            question_text:
              "Internal Properties (Use this, for all hidden answers)",
            question_description: "",
            question_format: "",
            question_mandatory: false,
            description: "",
            display_text:
              "Internal Properties (Use this, for all hidden answers) - This is a new project",
            section_title: null,
            section_id: null,
          },
          {
            id: "A1078",
            text: "Uses a database",
            question_id: "Q3",
            question_text: "Components In Use",
            question_description: "",
            question_format: "",
            question_mandatory: false,
            description: "",
            display_text: "Components In Use - Uses a database",
            section_title: null,
            section_id: null,
          },
        ],
        not_found: [],
      }),
    } as unknown as SDElementsClient;

    registerProjectTools(server as unknown as McpServer, client);

    const tool = server.tools.get("get_profile")!;
    const res = await tool.handler({
      profile_id: "P2",
      include_answer_details: true,
    });

    const body = parseToolText<{
      id: string;
      name: string;
      answer_ids: string[];
      answer_details: Array<{
        answer_id: string;
        question_text: string;
        answer_text: string;
        formatted: string;
      }>;
    }>(res);

    expect(body.id).toBe("P2");
    expect(body.name).toBe("Java EE Web App");
    expect(body.answer_ids).toEqual(["A1061", "A740", "A1078"]);
    expect(body.answer_details).toHaveLength(3);

    // Verify formatted output
    expect(body.answer_details[0].formatted).toBe(
      "A1061: Internal Properties (Use this, for all hidden answers) - Set of default answers for software profiles"
    );
    expect(body.answer_details[0].answer_id).toBe("A1061");
    expect(body.answer_details[0].question_text).toBe(
      "Internal Properties (Use this, for all hidden answers)"
    );
    expect(body.answer_details[0].answer_text).toBe(
      "Set of default answers for software profiles"
    );

    expect(client.getProfile).toHaveBeenCalledWith("P2");
    expect(client.getAnswerDetailsFromIds).toHaveBeenCalledWith(
      ["A1061", "A740", "A1078"],
      undefined
    );
  });

  it("get_profile handles profiles with answer_ids field instead of answers", async () => {
    const server = new TestMcpServer();
    const client = {
      getProfile: vi.fn().mockResolvedValue({
        id: "P1",
        name: "Test Profile",
        answer_ids: ["A1", "A2"],
      }),
      getAnswerDetailsFromIds: vi.fn().mockResolvedValue({
        answers: [
          {
            id: "A1",
            text: "Java",
            question_id: "Q1",
            question_text: "Programming Language",
            question_description: "",
            question_format: "",
            question_mandatory: false,
            description: "",
            display_text: "Programming Language - Java",
            section_title: null,
            section_id: null,
          },
        ],
        not_found: ["A2"],
      }),
    } as unknown as SDElementsClient;

    registerProjectTools(server as unknown as McpServer, client);

    const tool = server.tools.get("get_profile")!;
    const res = await tool.handler({
      profile_id: "P1",
      include_answer_details: true,
    });

    const body = parseToolText<{
      answer_ids: string[];
      answer_details: unknown[];
      not_found_answers: string[];
    }>(res);

    expect(body.answer_ids).toEqual(["A1", "A2"]);
    expect(body.answer_details).toHaveLength(1);
    expect(body.not_found_answers).toEqual(["A2"]);
  });

  it("get_profile can skip answer details conversion", async () => {
    const server = new TestMcpServer();
    const client = {
      getProfile: vi.fn().mockResolvedValue({
        id: "P3",
        name: "Simple Profile",
        answers: ["A1"],
      }),
      getAnswerDetailsFromIds: vi.fn(),
    } as unknown as SDElementsClient;

    registerProjectTools(server as unknown as McpServer, client);

    const tool = server.tools.get("get_profile")!;
    const res = await tool.handler({
      profile_id: "P3",
      include_answer_details: false,
    });

    const body = parseToolText<{
      answer_ids: string[];
      answer_details: unknown;
    }>(res);

    expect(body.answer_ids).toEqual(["A1"]);
    expect(body.answer_details).toBeUndefined();
    expect(client.getAnswerDetailsFromIds).not.toHaveBeenCalled();
  });
});




