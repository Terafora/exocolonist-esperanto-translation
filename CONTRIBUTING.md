# Contributing

Contributions are welcome through forks and pull requests. Direct write access is not required.

1. Fork the repository and create a branch from current `main`.
2. Choose a small, coherent translation batch (roughly 20–50 strings initially).
3. Read `GLOSSARY.md`, translate with care, and document new terminology as **Proposed**. A maintainer or language reviewer approves terminology; generated drafts are not automatically approved.
4. Inspect the diff and test in-game where possible using the README checklist.
5. Open a PR using the provided template. State the scope, terminology choices, checks performed and tests still pending.

## Translation and file format

- Use UTF-8 and proper `ĉ ĝ ĥ ĵ ŝ ŭ`, not x-system or h-system substitutions.
- Use infinitives for action buttons, nouns for category labels, and retain the source's casing style where practical.
- Keep names and proper nouns unchanged unless an explicit localisation decision is recorded.
- Preserve TSV row order, all three columns, the header, identifiers, notes, blank rows and existing CRLF line endings. Edit only the intended text values in `EN`.
- Preserve placeholders such as `{1}` and `{playerName}`, markup, escapes and scripting constructs exactly. Check both their spelling and number of occurrences.
- Do not translate custom-pronoun ordering patterns as ordinary prose. Defer ambiguous gameplay and world-specific terminology for discussion.
- Do not mass-translate the game. Story/Exoscript changes are outside the initial UI batch.

## Review and repository governance

Changes go through PRs to protected `main`. Ordinary contributors require at least one approving review and CODEOWNER review; new commits dismiss stale approvals and review conversations must be resolved. Force pushes and branch deletion are restricted. The intended repository-administrator bypass is limited to pull requests, preserving maintenance PR history without relaxing contributor protections. These are the project requirements; maintainers must verify the live ruleset separately when changing governance.

Human language review covers meaning, natural Esperanto, consistent terminology and UI fit. Be explicit about untested behavior. Automated checks are planned after the first successful in-game smoke test and before substantial story translation; currently no CI validator is configured.

## Source material and copyright

Keep untouched game references in ignored `local/upstream/` or `upstream/`. Never add an untouched complete English narrative, unrelated game assets or generated `*.exoc` files. `.gitignore` does not protect already tracked files, so inspect the staged file list before committing.

The localisation TSV is a whole-file override and retains untranslated rows needed by the game. Add other game files only when necessary for actual localisation work. Do not apply a broad software licence to game content or translations; any future tooling licence must be separate.
