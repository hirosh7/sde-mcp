import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { SDElementsClient } from "./apiClient.js";

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
    mockFetchOnce(
      async () => ({ status: 204, ok: true } as unknown as Response)
    );

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
});
