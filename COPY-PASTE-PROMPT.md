# Copy this into your AI application

Use a session with repository/file access, Python execution, and private file
output. In Codex or Claude Code, select this repository in a cloud session.
In ChatGPT, use Work with file creation and repository retrieval available.
If direct retrieval is unavailable, attach the repository ZIP from GitHub's
**Code > Download ZIP**. Reading a GitHub page alone does not run its scripts.
Availability depends on the application, account and organization settings.

Replace the three bracketed values, then paste:

```text
Use FSCR from https://github.com/YuvarajSK2498/Fusion-Setup-Configuration-Registry

Create an Excel configuration workbook, a configuration guide, and a draft
implementation run book for:
Offering / scope: [for example, Financials / Payables]
Country: [country]
Requirements: [describe the business needs, or use my attached requirements]

Read AGENTS.md, START-HERE.md and tools/configuration-workbook/AGENT-WORKFLOW.md.
Follow FSCR's implementation router and its required checks. Ask only for
missing information needed to proceed. This is draft-document preparation:
explicitly defer live Run Book creation with --no-create-runbook. Do not log
in to Fusion or change it. Do not invent approved values or task sequence.

Author the source-backed content pack, use the bundled workbook generator,
validate and dry-run it, generate all three files, and reopen the Excel file
to check it. Show unresolved gaps. Keep customer content private and provide
the actual files through this session's supported download/export mechanism.
If you cannot read the repository, execute Python, satisfy a routed workflow
step or deliver files, tell me the exact missing capability before proceeding;
do not claim that files were created.
```

The Excel workbook contains task, configuration-field, procedure, requirements,
validation, decision, source and quality-gap sheets. The guide and draft run
book are Markdown files. The AI authors the content; the bundled Python tool
validates its structure and renders the files. Missing source guidance remains
a recorded gap. Live Oracle Run Book creation is a separate authorized workflow.

This prompt does not enable tools in an account that lacks them. If your chat
cannot run the repository, switch to a repository-backed Codex/Claude Code cloud
session. An approved private initialized FSCR project and a valid routed task
mapping are required; failures in those prerequisites cannot be bypassed.

The generator is tested locally with synthetic content. This is not evidence
of an end-to-end test in every provider's browser or desktop application.
