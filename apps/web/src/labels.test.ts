import { describe, expect, it } from "vitest";

import { APP_NAV_GROUPS, APP_ROUTES } from "./appRoutes";
import { DATA_SOURCE_LABEL, TASK_STATUS_LABEL, labelOf } from "./labels";
import { moistureFill } from "./mapColors";

describe("chinese labels", () => {
  it("covers data sources used by the honesty policy", () => {
    expect(DATA_SOURCE_LABEL.REAL).toContain("真实");
    expect(DATA_SOURCE_LABEL.SIMULATION).toContain("仿真");
    expect(DATA_SOURCE_LABEL.MANUAL).toContain("台账");
  });

  it("falls back to the raw key", () => {
    expect(labelOf(TASK_STATUS_LABEL, "todo")).toBe("待办");
    expect(labelOf(TASK_STATUS_LABEL, "unknown")).toBe("unknown");
  });
});

describe("navigation registry", () => {
  it("registers dashboard irrigation plants twin and tasks once", () => {
    const paths = APP_ROUTES.map((item) => item.path);
    expect(paths).toEqual([...new Set(paths)]);
    expect(paths).toContain("/dashboard");
    expect(paths).toContain("/irrigation");
    expect(paths).toContain("/plants");
    expect(paths).toContain("/twin");
    expect(paths).toContain("/tasks");
    expect(APP_NAV_GROUPS.some((group) => group.items.some((item) => item.stub))).toBe(true);
  });
});

describe("moisture colors", () => {
  it("uses a drier color below the agronomy threshold", () => {
    const dry = moistureFill(41, 51);
    const ok = moistureFill(62, 51);
    expect(dry).not.toBe(ok);
    expect(moistureFill(null, 51)).toBe("#c9c2b3");
  });
});
