import { defineConfig } from "vitest/config";

// Avoid process forking in constrained environments (e.g., sandbox/CI) which can
// trigger EPERM on worker teardown. Threads keep everything in-process.
export default defineConfig({
  test: {
    environment: "node",
    pool: "threads",
  },
});


