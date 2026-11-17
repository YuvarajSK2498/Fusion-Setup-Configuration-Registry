# Agent workflow: turn a request into private draft files

This is a rendering extension, not a replacement implementation route or a new
Fusion execution adapter. Follow root AGENTS.md and the canonical router and
selected skills. Do not alter protected skills to make this extension run.

1. Read `core/getting-started/onboarding/SKILL.md` for orientation, then begin
   implementation work with `router/implementation-router/SKILL.md`. Confirm
   scope, country, requirements and release; collect only material missing inputs.
2. Verify repository access, Python 3.10+ (3.11+ recommended), and approved private
   workspace persistence and file delivery. A URL-reading tool is not Python
   execution. Never promise downloads when the host has no artifact mechanism.
3. Use the selected shared/pillar skills and repository product guidance to
   author requirements and the complete task scope. Research product specifics
   using the latest available official Oracle Fusion documentation, record
   source release/check date and target-release differences. Do not fabricate
   fields, navigation, screenshots, approvals or source verification.
4. Follow the offering-task-map builder and dependency resolver gates before
   project initialization. Reuse an eligible existing private initialized project
   when selected. Otherwise use the canonical project initializer with the
   required complete task mapping and explicitly requested `--no-create-runbook`.
   Preserve the pending Run Book state. The repository's routed sequence steps
   may have external prerequisites. An offline document request does not grant
   permission to call Fusion. If the required sequence or another prerequisite
   is unavailable, record and report the blocker under the selected workflow;
   do not create fake project-state files, invent order, or skip a gate.
5. Read this directory's README.md and use `workbook.py search` to confirm exact
   catalog identities. Create the authored JSON pack under the selected project's
   `blueprints/` directory. `seed` is a shell only. Author the actual steps,
   fields, sources, requirements, tests and decisions from the selected guidance.
   Copy reviewed sequence metadata; never treat catalog display order as sequence.
6. Install only the dependencies in this directory's requirements.txt if absent,
   using the host's supported permission flow. From the repository root run:

   ```text
   python tools/configuration-workbook/workbook.py --help
   python tools/configuration-workbook/workbook.py validate project/PROJECT/blueprints/configuration.json
   python tools/configuration-workbook/workbook.py generate project/PROJECT/blueprints/configuration.json --project project/PROJECT --dry-run
   python tools/configuration-workbook/workbook.py generate project/PROJECT/blueprints/configuration.json --project project/PROJECT
   ```

7. Reopen the returned XLSX with openpyxl. Verify the task count against the
   selected mapping, expected sheets, source entries and Quality Gaps. Verify
   `configuration-guide.md`, `draft-runbook.md` and `generation-report.json`
   exist in the same timestamped exports directory. Do not label a seed shell
   a populated guide. Do not report `--dry-run` as completed file creation.
8. Register the outputs using the routed artifact-registry/state-manager skills;
   record the authoring run and token usage separately from the deterministic
   generator's zero-model-token record. Follow project versioning rules.
9. Deliver the three files using the host's private artifact mechanism, summarize
   actual coverage and gaps, and give the private project resume/backup path.
   Never publish customer outputs in GitHub commits, releases, issues or PRs.

The deterministic tool validates and renders supplied content; it does not call
an AI, verify external documentation, extract arbitrary requirement attachments,
run Fusion, or certify product correctness. Those are the selected agent and
workflow's responsibilities. Report missing capabilities plainly.
