import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { SDElementsClient } from "../../src/utils/apiClient.js";

function mockFetchOnce(impl: Parameters<typeof vi.fn>[0]) {
  const fn = vi.fn(impl);
  vi.stubGlobal("fetch", fn as unknown as typeof fetch);
  return fn;
}

describe("SDElementsClient.request (via public methods)", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("normalizes host (trailing slash) and builds URLs with query params", async () => {
    const fetchMock = mockFetchOnce(async (url: string, init?: RequestInit) => {
      expect(url).toBe(
        "https://example.test/api/v2/projects/?page_size=10&include=profile"
      );
      expect(init?.method).toBe("GET");
      expect((init?.headers as Record<string, string>).Authorization).toBe(
        "Token abc"
      );
      return new Response(
        JSON.stringify({ count: 0, next: null, previous: null, results: [] }),
        {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }
      );
    });

    const client = new SDElementsClient({
      host: "https://example.test/",
      apiKey: "abc",
      timeout: 1000,
    });

    const res = await client.listProjects({
      page_size: 10,
      include: "profile",
    });
    expect(res.count).toBe(0);
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("stringifies body for non-GET methods", async () => {
    const fetchMock = mockFetchOnce(
      async (_url: string, init?: RequestInit) => {
        expect(init?.method).toBe("PATCH");
        expect(init?.body).toBe(JSON.stringify({ name: "New Name" }));
        return new Response(
          JSON.stringify({
            id: 1,
            name: "New Name",
            slug: "x",
            application: 1,
            profile: "p",
          }),
          {
            status: 200,
            headers: { "Content-Type": "application/json" },
          }
        );
      }
    );

    const client = new SDElementsClient({
      host: "https://example.test",
      apiKey: "abc",
      timeout: 1000,
    });

    const res = await client.updateProject(1, { name: "New Name" });
    expect(res.name).toBe("New Name");
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("returns {} for HTTP 204", async () => {
    // Node's Response constructor rejects 204 in some environments; we only need
    // the minimal surface used by the client (status + ok).
    mockFetchOnce(async () => ({ status: 204, ok: true } as unknown as Response));

    const client = new SDElementsClient({
      host: "https://example.test",
      apiKey: "abc",
      timeout: 1000,
    });

    const res = await client.apiRequest("DELETE", "projects/1/");
    expect(res).toEqual({});
  });

  it("throws a formatted Error using 'detail' when response is not ok", async () => {
    mockFetchOnce(async () => {
      return new Response(JSON.stringify({ detail: "Nope" }), { status: 401 });
    });

    const client = new SDElementsClient({
      host: "https://example.test",
      apiKey: "abc",
      timeout: 1000,
    });

    await expect(client.get("users/me/")).rejects.toThrow(
      /\[SDElements\] HTTP 401 \(Unauthorized\):/
    );
  });

  it("falls back to raw text when error body isn't JSON", async () => {
    mockFetchOnce(async () => new Response("plain error", { status: 500 }));

    const client = new SDElementsClient({
      host: "https://example.test",
      apiKey: "abc",
      timeout: 1000,
    });

    await expect(client.get("users/me/")).rejects.toThrow(/plain error/);
  });

  it("maps AbortError to a timeout message", async () => {
    mockFetchOnce(async () => {
      const err = new Error("aborted");
      (err as Error & { name: string }).name = "AbortError";
      throw err;
    });

    const client = new SDElementsClient({
      host: "https://example.test",
      apiKey: "abc",
      timeout: 123,
    });

    await expect(client.get("users/me/")).rejects.toThrow(
      "[SDElements] Request timed out after 123ms"
    );
  });

  it("normalizes task IDs for getTask/updateTask/addTaskNote", async () => {
    const fetchMock = mockFetchOnce(async (url: string) => {
      expect(url).toContain("/api/v2/projects/123/tasks/123-T456/");
      return new Response(
        JSON.stringify({
          id: "123-T456",
          title: "x",
          status: "Open",
          project: 123,
        }),
        {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }
      );
    });

    const client = new SDElementsClient({
      host: "https://example.test",
      apiKey: "abc",
      timeout: 1000,
    });

    const task = await client.getTask(123, "T456");
    expect(task.id).toBe("123-T456");
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("listProjectDiagrams calls project-diagrams/ with project=<id>", async () => {
    const fetchMock = mockFetchOnce(async (url: string) => {
      expect(url).toBe("https://example.test/api/v2/project-diagrams/?project=123");
      return new Response(JSON.stringify({ results: [] }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    });

    const client = new SDElementsClient({
      host: "https://example.test",
      apiKey: "abc",
      timeout: 1000,
    });

    const res = await client.listProjectDiagrams(123);
    expect(res).toEqual({ results: [] });
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("listTeamOnboardingConnections hits team-onboarding/connections/", async () => {
    const fetchMock = mockFetchOnce(async (url: string) => {
      expect(url).toBe("https://example.test/api/v2/team-onboarding/connections/");
      return new Response(JSON.stringify({ results: [] }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    });

    const client = new SDElementsClient({
      host: "https://example.test",
      apiKey: "abc",
      timeout: 1000,
    });

    const res = await client.listTeamOnboardingConnections();
    expect(res).toEqual({ results: [] });
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("runAdvancedReport returns {query,data} when query exists and cube executes", async () => {
    const client = new SDElementsClient({
      host: "https://example.test",
      apiKey: "abc",
      timeout: 1000,
    });

    const getAdvancedReportSpy = vi
      .spyOn(client, "getAdvancedReport")
      .mockResolvedValue({
        id: 7,
        query: {
          schema: "application",
          dimensions: ["Application.name"],
          measures: ["Project.count"],
        },
      } as unknown as never);

    const executeCubeQuerySpy = vi
      .spyOn(client, "executeCubeQuery")
      .mockResolvedValue({ data: [{ x: 1 }] } as unknown as never);

    const res = await client.runAdvancedReport(7);
    expect(getAdvancedReportSpy).toHaveBeenCalledWith(7, undefined);
    expect(executeCubeQuerySpy).toHaveBeenCalledTimes(1);
    expect(res).toEqual({
      query: {
        id: 7,
        query: {
          schema: "application",
          dimensions: ["Application.name"],
          measures: ["Project.count"],
        },
      },
      data: { data: [{ x: 1 }] },
    });
  });

  it("runAdvancedReport returns {query,data:null,error} when cube execution fails", async () => {
    const client = new SDElementsClient({
      host: "https://example.test",
      apiKey: "abc",
      timeout: 1000,
    });

    vi.spyOn(client, "getAdvancedReport").mockResolvedValue({
      id: 9,
      query: { schema: "application", dimensions: [], measures: [] },
    } as unknown as never);

    vi.spyOn(client, "executeCubeQuery").mockRejectedValue(
      new Error("cube down") as unknown as never
    );

    const res = await client.runAdvancedReport(9);
    expect(res).toEqual({
      query: { id: 9, query: { schema: "application", dimensions: [], measures: [] } },
      data: null,
      error: expect.stringMatching(/Failed to execute cube query: .*cube down/),
    });
  });

  it("executeCubeQuery fetches a JWT then calls cubejs-api/v1/load with Bearer token", async () => {
    const fetchMock = vi.fn(async (url: string, init?: RequestInit) => {
      if (url === "https://example.test/api/v2/users/me/auth-token/") {
        expect(init?.method).toBe("GET");
        return new Response(JSON.stringify({ token: "jwt-123" }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }

      expect(url).toContain("https://example.test/cubejs-api/v1/load?query=");
      const headers = init?.headers as unknown as { Authorization?: string };
      expect(headers.Authorization).toBe("Bearer jwt-123");
      expect(init?.method).toBe("GET");

      return new Response(JSON.stringify({ data: [{ ok: 1 }] }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    });

    vi.stubGlobal("fetch", fetchMock as unknown as typeof fetch);

    const client = new SDElementsClient({
      host: "https://example.test",
      apiKey: "abc",
      timeout: 1000,
    });

    const res = await client.executeCubeQuery({
      schema: "application",
      dimensions: ["Application.name"],
      measures: ["Project.count"],
    });
    expect(res).toEqual({ data: [{ ok: 1 }] });
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  describe("getAnswerDetailsFromIds", () => {
    it("extracts answer text from display_text field when available", async () => {
      const client = new SDElementsClient({
        host: "https://example.test",
        apiKey: "abc",
        timeout: 1000,
      });

      // Mock loadLibraryAnswers to populate cache
      const libraryAnswersResponse = {
        count: 3,
        next: null,
        previous: null,
        results: [
          {
            id: "A1061",
            text: "Set of default answers for software profiles",
            question: "Q1",
            display_text:
              "Internal Properties (Use this, for all hidden answers) - Set of default answers for software profiles",
            description: "",
          },
          {
            id: "A740",
            text: "This is a new project",
            question: "Q2",
            display_text:
              "Internal Properties (Use this, for all hidden answers) - This is a new project",
            description: "",
          },
          {
            id: "A1078",
            text: "Uses a database",
            question: "Q3",
            display_text: "Components In Use - Uses a database",
            description: "",
          },
        ],
      };

      mockFetchOnce(async (url: string) => {
        if (url.includes("/api/v2/library/answers/")) {
          return new Response(JSON.stringify(libraryAnswersResponse), {
            status: 200,
            headers: { "Content-Type": "application/json" },
          });
        }
        // Mock library question endpoint
        if (url.includes("/api/v2/library/questions/")) {
          const questionId = url.match(/questions\/([^/]+)/)?.[1];
          return new Response(
            JSON.stringify({
              id: questionId,
              text: questionId === "Q1" 
                ? "Internal Properties (Use this, for all hidden answers)"
                : questionId === "Q2"
                ? "Internal Properties (Use this, for all hidden answers)"
                : "Components In Use",
              description: "",
              format: "choice",
              mandatory: false,
            }),
            {
              status: 200,
              headers: { "Content-Type": "application/json" },
            }
          );
        }
        return new Response(JSON.stringify({}), { status: 404 });
      });

      const result = await client.getAnswerDetailsFromIds([
        "A1061",
        "A740",
        "A1078",
      ]);

      expect(result.answers).toHaveLength(3);
      expect(result.not_found).toHaveLength(0);

      // Verify A1061
      const a1061 = result.answers.find((a) => a.id === "A1061");
      expect(a1061).toBeDefined();
      expect(a1061?.text).toBe("Set of default answers for software profiles");
      expect(a1061?.question_text).toBe(
        "Internal Properties (Use this, for all hidden answers)"
      );

      // Verify A740
      const a740 = result.answers.find((a) => a.id === "A740");
      expect(a740).toBeDefined();
      expect(a740?.text).toBe("This is a new project");
      expect(a740?.question_text).toBe(
        "Internal Properties (Use this, for all hidden answers)"
      );

      // Verify A1078
      const a1078 = result.answers.find((a) => a.id === "A1078");
      expect(a1078).toBeDefined();
      expect(a1078?.text).toBe("Uses a database");
      expect(a1078?.question_text).toBe("Components In Use");
    });

    it("falls back to answerData.text when display_text doesn't contain ' - '", async () => {
      const client = new SDElementsClient({
        host: "https://example.test",
        apiKey: "abc",
        timeout: 1000,
      });

      const libraryAnswersResponse = {
        count: 1,
        next: null,
        previous: null,
        results: [
          {
            id: "A1",
            text: "Java",
            question: "Q1",
            display_text: "Programming Language",
            description: "",
          },
        ],
      };

      mockFetchOnce(async (url: string) => {
        if (url.includes("/api/v2/library/answers/")) {
          return new Response(JSON.stringify(libraryAnswersResponse), {
            status: 200,
            headers: { "Content-Type": "application/json" },
          });
        }
        if (url.includes("/api/v2/library/questions/")) {
          return new Response(
            JSON.stringify({
              id: "Q1",
              text: "Programming Language",
              description: "",
              format: "choice",
              mandatory: false,
            }),
            {
              status: 200,
              headers: { "Content-Type": "application/json" },
            }
          );
        }
        return new Response(JSON.stringify({}), { status: 404 });
      });

      const result = await client.getAnswerDetailsFromIds(["A1"]);

      expect(result.answers).toHaveLength(1);
      const a1 = result.answers[0];
      expect(a1.id).toBe("A1");
      expect(a1.text).toBe("Java"); // Should use answerData.text as fallback
      expect(a1.question_text).toBe("Programming Language");
    });

    it("handles answer text that contains ' - ' in the text", async () => {
      const client = new SDElementsClient({
        host: "https://example.test",
        apiKey: "abc",
        timeout: 1000,
      });

      const libraryAnswersResponse = {
        count: 1,
        next: null,
        previous: null,
        results: [
          {
            id: "A47",
            text: "Java EE",
            question: "Q1",
            display_text: "Technology/Framework - Java EE",
            description: "",
          },
        ],
      };

      mockFetchOnce(async (url: string) => {
        if (url.includes("/api/v2/library/answers/")) {
          return new Response(JSON.stringify(libraryAnswersResponse), {
            status: 200,
            headers: { "Content-Type": "application/json" },
          });
        }
        if (url.includes("/api/v2/library/questions/")) {
          return new Response(
            JSON.stringify({
              id: "Q1",
              text: "Technology/Framework",
              description: "",
              format: "choice",
              mandatory: false,
            }),
            {
              status: 200,
              headers: { "Content-Type": "application/json" },
            }
          );
        }
        return new Response(JSON.stringify({}), { status: 404 });
      });

      const result = await client.getAnswerDetailsFromIds(["A47"]);

      expect(result.answers).toHaveLength(1);
      const a47 = result.answers[0];
      expect(a47.id).toBe("A47");
      expect(a47.text).toBe("Java EE");
      expect(a47.question_text).toBe("Technology/Framework");
    });
  });
});


