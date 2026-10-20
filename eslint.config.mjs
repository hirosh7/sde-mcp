// @ts-check

import eslint from "@eslint/js";
import { defineConfig } from "eslint/config";
import tseslint from "typescript-eslint";
import globals from "globals";

export default defineConfig(
  {
    // Place global ignores in a configuration object
    ignores: ["dist/**/*", "build/**/*"],
  },
  eslint.configs.recommended,
  tseslint.configs.recommended,
  {
    files: ["client-ui/static/**/*.js"],
    languageOptions: {
      globals: {
        ...globals.browser,
      },
      ecmaVersion: 2022,
      sourceType: "module",
    },
  }
);
