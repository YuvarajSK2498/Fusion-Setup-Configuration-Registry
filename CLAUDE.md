# FSCR agent entry point

Read and follow [AGENTS.md](AGENTS.md) as the repository's canonical directives.
Read any applicable nested directives before changing files.

For introductions and authentication guidance, begin with
`core/getting-started/onboarding/SKILL.md`. For implementation work, begin with
`router/implementation-router/SKILL.md` and follow its selected skills and gates.

For desktop and browser onboarding, see [START-HERE.md](START-HERE.md).
For workbook requests, also read `tools/configuration-workbook/AGENT-WORKFLOW.md`.
When users request draft documents without Fusion access, defer live Run Book
creation explicitly through the initializer's supported `--no-create-runbook`
option. Never substitute a direct API call or browser operation for a routed step.

Keep customer artifacts in their private project workspace, never in a public
commit or pull request. Keep all secrets outside the repository. A cloud session
must confirm private persistence and artifact retrieval before accepting customer
inputs; a public repository does not provide a private artifact store.
