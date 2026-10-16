import { defineConfig, defineContainer, exports } from "cf/config";

import * as entrypoint from "./src/index.ts" with { type: "cf-worker" };

const runner = defineContainer({
  name: "qg-runner",
  image: { dockerfile: "../Dockerfile", buildContext: "../.." },
  instanceType: "basic",
  maxInstances: 3,
});

export default defineConfig({
  worker: {
    name: "qg-runner",
    compatibilityDate: "2026-10-01",
    entrypoint,
    exports: {
      Runner: exports.durableObject({ storage: "sqlite", container: runner }),
    },
  },
  containers: [runner],
});
