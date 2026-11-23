// ESLint configuration. It enforces the JavaScript rules in CLAUDE.md.
// Never disable a rule to make a change pass. Fix the code.
import js from "@eslint/js";
import jsdoc from "eslint-plugin-jsdoc";
import globals from "globals";

// Every named function has JSDoc with `@param {Type}` and `@returns {Type}`, and every module
// starts with an `@module` block (see JavaScript and TypeScript). An inline callback, such as an
// event handler, needs none.
const jsdocRules = {
  "jsdoc/require-jsdoc": [
    "error",
    {
      require: { FunctionDeclaration: true, MethodDefinition: true, ClassDeclaration: true },
      contexts: [
        "VariableDeclarator > ArrowFunctionExpression",
        "VariableDeclarator > FunctionExpression",
      ],
    },
  ],
  "jsdoc/require-param": "error",
  "jsdoc/require-param-type": "error",
  "jsdoc/check-param-names": "error",
  "jsdoc/require-returns": ["error", { forceRequireReturn: true }],
  "jsdoc/require-returns-type": "error",
  "jsdoc/require-file-overview": [
    "error",
    { tags: { module: { initialCommentsOnly: true, mustExist: true, preventDuplicates: true } } },
  ],
};

export default [
  { ignores: ["site/**", "node_modules/**"] },
  js.configs.recommended,
  {
    files: ["src/**/*.js"],
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: "module",
      globals: { ...globals.browser },
    },
    plugins: { jsdoc },
    rules: {
      ...jsdocRules,
      // Code-smell limits (see Code smells).
      "max-lines-per-function": ["error", { max: 20, skipBlankLines: true, skipComments: true }],
      "max-params": ["error", 4],
      complexity: ["error", 8],
      "max-lines": ["warn", { max: 300, skipBlankLines: true, skipComments: true }],
      "max-classes-per-file": ["error", 1],
      // Plain, predictable code.
      "no-var": "error",
      "prefer-const": "error",
      eqeqeq: "error",
      // No TODO comments (see Naming): report the finding instead.
      "no-warning-comments": ["error", { terms: ["todo", "fixme", "xxx", "hack"], location: "start" }],
      // Only log.js uses console, and only api.js calls fetch.
      "no-console": "error",
      "no-restricted-globals": ["error", { name: "fetch", message: "Only api.js calls fetch." }],
      "no-restricted-syntax": [
        "error",
        {
          selector: "Program > VariableDeclaration[kind='let']",
          message: "No mutable module-level state. Create state in main.js and pass it in.",
        },
        {
          selector: "ExportNamedDeclaration > VariableDeclaration[kind='let']",
          message: "No mutable module-level state. Create state in main.js and pass it in.",
        },
        {
          selector: "AssignmentExpression[left.property.name='innerHTML']",
          message: "Use textContent or a <template>. Never build HTML from data.",
        },
      ],
    },
  },
  // In any folder under src/ that the design chooses, such as src/web/ next to a Python server.
  { files: ["src/**/api.js"], rules: { "no-restricted-globals": "off" } },
  { files: ["src/**/log.js"], rules: { "no-console": "off" } },
  { files: ["tests/**/*.js"], languageOptions: { globals: { ...globals.node } } },
];
