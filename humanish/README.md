# humanish

This directory holds the committed definitions of this app's humanish studies: study files,
personas and scenarios.

Keep this directory public-safe:

- synthetic personas only;
- synthetic fixtures only;
- env var names only, never values;
- no PII, PHI, secrets, raw private transcripts, private screenshots, customer data, or patient data.

Generated run bundles, screenshots, traces, logs, and local overrides belong in ignored `.humanish/`.

Studies:

- committed reusable studies live in humanish/studies/*.yaml;
- private or machine-local studies live in ignored .humanish/studies/*.yaml or
  .humanish/local/studies/*.yaml;
- run a study with `npx humanish run <study>`, or `npx humanish watch <study>` to stay attached;
- a live run ends with findings from a separate analyst; `npx humanish review --run latest` shows them;
- files under humanish/labs/ move there with `npx humanish migrate`.

Format standard:

- human-authored humanish source uses .yaml;
- generated artifacts, synthetic fixtures, and event streams use .json or .ndjson;
- .yml is reserved for outside ecosystem files such as GitHub Actions, not humanish source.
