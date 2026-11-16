# MediDoc AI - agent rules

- Source of truth: SPEC.md. Work on ONE phase or task at a time and stop when it is done.
- Do not start a later phase unless asked. Do not refactor unrelated files.
- Use only SYNTHETIC data. Never include real patient information anywhere.
- Never log or store raw document text or PII. The audit log holds metadata only.
- Python 3.12, type hints, docstrings. Pydantic models for all API inputs and outputs.
- LangChain: use the versions pinned in requirements.txt and follow the installed
  version's documentation, not memory. Do not upgrade packages without asking.
- Secrets only via environment variables. Provide .env.example. Never commit .env.
- Every new module gets a pytest test. Run the tests and show the result before saying done.
- After each task, add 3 to 5 lines to DECISIONS.md: what was built and WHY this design.
- After each task, tell me exactly how to run it and how to verify it (command or URL).
- Keep code simple and readable. The developer must be able to explain every file.
- If something is unclear or a package fails to install, stop and ask instead of guessing.

- After each phase, update README.md so it matches the current project: features,
  quickstart commands that actually work, endpoint list, and a status table.