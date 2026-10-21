import js from "@eslint/js";
import reactHooks from "eslint-plugin-react-hooks";
import tseslint from "typescript-eslint";

export default tseslint.config(
  { ignores: ["dist", "node_modules", "public", "src/contrato"] },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  reactHooks.configs.flat["recommended-latest"] ?? reactHooks.configs.flat.recommended,
  {
    rules: {
      "@typescript-eslint/no-unused-vars": [
        "error",
        { argsIgnorePattern: "^_", varsIgnorePattern: "^_" },
      ],
      // Indisponível pela rede em http (contexto não seguro). Use novoId() de @/lib/utils.
      "no-restricted-properties": [
        "error",
        {
          object: "crypto",
          property: "randomUUID",
          message: "Use novoId() de @/lib/utils (funciona em http).",
        },
      ],
    },
  },
);
