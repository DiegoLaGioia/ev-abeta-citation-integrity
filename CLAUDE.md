# Instructions for Claude

- **Read the blueprint first.** Before building or changing any pipeline stage, read `blueprint_EV-Abeta_citation-integrity.md` in the repo root. It is the spec — architecture, stage scope, and MVP boundaries are decided there, not improvised.
- **Never commit anything under `data/` or `cache/`.** These hold raw/derived data (PDFs, JATS XML, API cache, generated reports) and are gitignored on purpose. Don't `git add -f` files in these paths even if asked to commit "everything."
- **Diego is not a professional software engineer.** Keep explanations of design choices brief and in plain language — what was chosen and why, not a lecture. Before adding a new dependency, ask first rather than installing it silently.
