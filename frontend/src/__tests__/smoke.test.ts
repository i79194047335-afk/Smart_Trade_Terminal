/**
 * Smoke test — minimal sanity check.
 *
 * Its only purpose is to prove the test runner (Vitest) is wired correctly.
 * Real tests for chart wrapper, data hooks, etc. will be added in later phases.
 */

import { describe, it, expect } from "vitest";

describe("smoke", () => {
  it("arithmetic still works", () => {
    // If this ever fails, JavaScript itself is broken — i.e. something is very wrong.
    expect(1 + 1).toBe(2);
  });
});
