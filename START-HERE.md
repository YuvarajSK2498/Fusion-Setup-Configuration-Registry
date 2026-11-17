# Use FSCR from a desktop app or browser

For the shortest request, use [the copy-and-paste prompt](COPY-PASTE-PROMPT.md).
The bundled [workbook renderer](tools/configuration-workbook/README.md) creates
Excel plus matching Markdown guide and draft run-book files from agent-authored
content after the existing workflow prerequisites have passed.

FSCR is a public collection of Oracle Fusion implementation skills, technical
services, and reference material. An AI coding agent reads these files and runs
the selected workflow. GitHub hosts the files; it does not run FSCR by itself.
You do not need to type terminal commands when your agent provides a working
repository environment. Access to the agent service and its cloud features is
subject to your account plan and administrator settings.

Public distribution:
[YuvarajSK2498/Fusion-Setup-Configuration-Registry](https://github.com/YuvarajSK2498/Fusion-Setup-Configuration-Registry).
Select this repository (or your own fork of it) in your agent's repository picker.
Oracle's upstream source remains
[oracle/Fusion-Setup-Configuration-Registry](https://github.com/oracle/Fusion-Setup-Configuration-Registry).

This distribution adds desktop/browser instructions to Oracle's reference
repository. It does not claim Oracle endorsement or cloud execution certification.
The existing [license](LICENSE.txt) and [repository guidance](AGENTS.md) apply.

## Choose your application

| Application | How to start without CMD or VS Code |
| --- | --- |
| Codex in a browser | Open Codex through your OpenAI account, connect GitHub, and select your FSCR repository in a cloud environment. |
| Codex desktop interface | Start a Codex task, choose **Work in > Cloud**, and select an environment containing your FSCR repository. A local project instead runs on your computer. |
| Claude Code in a browser | Open Claude Code on the web, connect your GitHub account, and select your FSCR repository for a cloud session. |
| Claude Code desktop interface | Open the Code surface, select a cloud environment, and select your FSCR repository. Local sessions require a local folder. |

If the source repository is unavailable in the repository picker, use GitHub's
**Fork** button to make your own copy, then authorize the agent's GitHub
integration for that copy. Repository access and agent-service access are separate.
Each person connects their own accounts; publishing FSCR does not grant access
to someone else's subscription, cloud environment, or Fusion instance.

GitHub's repository page and github.dev are file-browsing/editing interfaces;
neither alone is a configured agent execution environment.

Product instructions, verified 17 November 2026:

- [Codex environments](https://learn.chatgpt.com/docs/environments/modes)
- [Codex Cloud](https://learn.chatgpt.com/docs/cloud)
- [Claude Code desktop](https://code.claude.com/docs/en/desktop)
- [Claude Code cloud](https://code.claude.com/docs/en/claude-code-on-the-web)

## First message: verify the workspace

Paste this into the agent's chat:

> Read AGENTS.md and START-HERE.md. Begin with core/getting-started/onboarding/SKILL.md.
> Verify you can read router, core, shared, pillars, knowledge, schemas and project.
> Explain the runtime and private artifact-persistence capabilities of this session.
> Check Python availability if scripts will be needed. Do not log in to Fusion,
> create a project or Run Book, or make tenant requests yet.

The agent should identify missing capabilities before attempting a workflow.
If it can only read a pasted URL and cannot access repository files or execute
required scripts, use a repository-backed coding session before continuing.

## Generate a draft run book and configuration guide

A draft run book is an implementation planning artifact. A live Oracle Fusion
Run Book is a record created in an authorized Fusion environment. Choose the
draft workflow when you want documents without connecting to Fusion.

Start with fictional or sanitized inputs. For real customer work, first confirm
your organization permits the chosen AI service and that workspace files,
attachments, session sharing, and exports remain private. Do not commit customer
outputs to this public repository or a public fork. Git ignore rules do not
protect files copied into a tracked path or included in chat or a pull request.

Paste this prompt, replacing the bracketed values:

> Use FSCR's implementation router to prepare a draft implementation run book
> and configuration guide for [pillar / offering / functional areas], in [country],
> for [business objective]. My approved requirements are [sanitized requirements
> or an approved private attachment]. Target Fusion release: [release or unknown].
> Ask for missing scope and design decisions; do not invent approved values.
> This request is for private draft documents only. Explicitly defer live Oracle
> Run Book creation using the initializer's --no-create-runbook option.
> Do not authenticate or call Fusion. Resolve the complete task mapping and
> dependency order through the routed skills before initializing the project.
> Use the selected private project workspace, or create draft_impl_project_<date>
> when no project exists, following AGENTS.md. Persist state, artifacts, run
> records, and the required token-usage log. Consult repository product guidance
> first and verify release-dependent setup guidance using the latest available
> official Oracle Fusion documentation; distinguish target-release differences.
> If official research is unavailable, mark the affected sections unverified.
> Report blockers rather than bypassing missing workflow steps.
> Give me the draft documents, their private workspace paths, outstanding
> decisions, source references, and available download or retrieval instructions.

Useful follow-up requests:

> In the draft run book, include task sequence, dependencies, responsible role,
> required inputs, approval gates, validation evidence, and completion criteria.
> Preserve all eligible mapped tasks and diagnose unresolved sequence entries.

> In the configuration guide, include business requirements, proposed values
> clearly separated from approved values, relevant setup tasks, prerequisites,
> documented navigation where available, validation steps, sources, and gaps.
> Mark unsupported automation as manual guidance. Do not claim configuration
> has been applied. Produce Markdown; provide DOCX/PDF only if a supported
> renderer is available and its output is verified.

FSCR uses multiple routed skills; it does not guarantee one universal guide
generator for every offering. Missing task guidance or ambiguous mappings can
block part of the deliverable and must be reported explicitly.

## Keep and retrieve the results

The canonical private locations are:

- `project/{project_id}/state/project-state.json`
- `project/{project_id}/state/runs/`
- `project/{project_id}/artifacts/artifact-index.json`
- `project/{project_id}/artifacts/shared/runbook/current/`
- `project/{project_id}/artifacts/shared/token-usage/current/token-usage-log.md`
- Additional guide and blueprint paths selected by the routed skills.

Ask the agent to show the artifact index and to provide the session's supported
private download/export mechanism. Before ending the session, retrieve or back
up the entire project workspace to an approved private store, including state,
decisions, blueprints and artifacts. Cloud session files and Git-ignored files
must not be assumed to survive into a new session or appear in a code diff.
If private persistence or file retrieval is unavailable, stop before customer
artifact generation and choose an approved persistent environment.

For a later session, restore the private project workspace and ask the agent to
resume from project-state.json. A fresh checkout contains the framework and
template, not your previous project's private state.

## Create a live Oracle Fusion Run Book later

After reviewing the persisted draft plan, request:

> Resume project [project_id] through the implementation router. I now want to
> create the Oracle Fusion Run Book from the project's canonical persisted plan
> in [authorized environment name]. Follow core/runbook/SKILL.md and its own
> preflight and approval workflow. Verify the selected runtime supports the
> declared authentication and callback flow before any live call. Return the
> complete sanitized Run Book dashboard and persist the creation outcome.

This requires your own supported Fusion release, environment enrollment,
authorized user, privileges and network access. Use the
[onboarding authentication guidance](core/getting-started/onboarding/SKILL.md).
Credentials, tokens, private keys, and OAuth trust files stay outside the
repository, including all project folders.

The current authentication workflow uses browser sign-in and a callback.
A cloud runtime does not automatically inherit your desktop browser sign-in,
localhost callback, VPN, or private token cache. Cloud login compatibility has
not been validated by this distribution. If the declared workflow cannot run
in that environment, report the blocker and use a supported authorized runtime;
do not improvise a token relay or direct REST fallback. Document-only work can
continue within the deferred workflow where its prerequisites are satisfied.

## What this setup verifies

The publication adds entry instructions, a tested document renderer, and privacy
ignore rules. Renderer tests use synthetic data, not a live Fusion environment
or provider-specific end-to-end cloud sessions. It does not
install an agent subscription, register a Fusion OAuth client, configure every
user's cloud environment, certify all pillar skills, or demonstrate a successful
live Fusion Run Book creation. Validate those capabilities per user and runtime.
