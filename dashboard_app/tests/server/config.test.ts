import os from "node:os";
import path from "node:path";

import { afterEach, beforeEach, describe, expect, it } from "vitest";

import { getConfig } from "@/lib/config";

const ENV_KEY = "PRAXION_PROJECT_ROOT";

describe("getConfig multi-instance contract", () => {
  let originalEnv: string | undefined;

  beforeEach(() => {
    originalEnv = process.env[ENV_KEY];
  });

  afterEach(() => {
    if (originalEnv === undefined) {
      delete process.env[ENV_KEY];
    } else {
      process.env[ENV_KEY] = originalEnv;
    }
  });

  it("resolves projectRoot from PRAXION_PROJECT_ROOT at call time", () => {
    const dir = path.join(os.tmpdir(), "praxion-config-test-a");
    process.env[ENV_KEY] = dir;
    const config = getConfig();
    expect(config.projectRoot).toBe(path.resolve(dir));
  });

  it("throws when PRAXION_PROJECT_ROOT is unset", () => {
    delete process.env[ENV_KEY];
    expect(() => getConfig()).toThrow(/PRAXION_PROJECT_ROOT/);
  });

  it("returns different projectRoot for different env values without cross-instance bleed", () => {
    const dirA = path.join(os.tmpdir(), "praxion-config-test-b");
    const dirB = path.join(os.tmpdir(), "praxion-config-test-c");

    process.env[ENV_KEY] = dirA;
    const configA = getConfig();

    process.env[ENV_KEY] = dirB;
    const configB = getConfig();

    expect(configA.projectRoot).toBe(path.resolve(dirA));
    expect(configB.projectRoot).toBe(path.resolve(dirB));
    expect(configA.projectRoot).not.toBe(configB.projectRoot);
  });

  it("derives projectName from the last path segment of PRAXION_PROJECT_ROOT", () => {
    process.env[ENV_KEY] = path.join(os.tmpdir(), "my-project");
    const config = getConfig();
    expect(config.projectName).toBe("my-project");
  });
});
