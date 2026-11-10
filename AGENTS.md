# AGENTS.md

## humanish <!-- humanish:agents-guide -->

This project uses humanish: synthetic participants use the product and leave evidence.

```bash
npx humanish study list --json             # the studies in this project
npx humanish run first-run --no-open       # dry run: no browser, model, keys, or spend
npx humanish doctor --study try-live       # what the hosted starter study still needs
npx humanish run try-live --no-open        # demo app study: E2B plus the selected participant's authentication
npx humanish doctor --study local-browser  # local Docker/Firecracker + Codex-account readiness
npx humanish run local-browser --no-open   # your loopback app; no E2B or model API key
npx humanish verify --run <id> --json      # is the evidence share-safe
npx humanish review --run <id>             # the run's outcome and its analysis findings
```

- After a live run, run `npx humanish review --run <id>` (or `--json`) and report its findings
  to the person you are working for: each one's title, impact, confidence, recovery and cited
  captures. When it shows no findings, report its message and the command it names. Every run
  prints its id; `latest` moves with each run, dry runs included.
- Studies are declared in `humanish/studies/*.yaml`. Edit `try-live.yaml`'s `subject` to point
  at this project's own app once you have seen a run work.
- Configure the local study without editing YAML: `npx humanish init --yes --local-browser
  http://127.0.0.1:3000 --local-mission "Complete the primary flow"` on first setup.
- Evidence lands in gitignored `.humanish/runs/`. Never commit it, and never paste raw run
  bundles into an issue; `npx humanish feedback issue` writes a redacted, share-safe draft.
- `npx humanish tui` is for people and refuses to run in an agent session. Use the commands
  above instead, and tell the person you are working for that the TUI exists.
- A live run spends money. `caps.maxUsd` in each study caps estimated model spend: the run
  stops before its next request once the estimate passes it, so the last request can go over, and
  hosted desktop time is billed on top. Do not raise it without asking the person you are working for.
- `npx humanish init --yes` rewrites this section, between its two markers, to match the installed
  humanish. Write your own notes outside it.

<!-- /humanish:agents-guide -->
