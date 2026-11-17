# Generic FSCR configuration workbook generator

For a natural-language request, use [the copyable prompt](../../COPY-PASTE-PROMPT.md).
Agents should follow [AGENT-WORKFLOW.md](AGENT-WORKFLOW.md) to author the content
pack through FSCR's existing router before running this renderer.

A standalone, offline extension to FSCR. It is independent of any customer or
offering and reads the repository's effective setup-task catalog. It does not
modify the canonical skills, call Fusion, log in, execute configuration, or
replace FSCR's router and project workflow. Python 3.10+ is required.

## Install and discover

```powershell
python -m pip install -r tools/configuration-workbook/requirements.txt
python tools/configuration-workbook/workbook.py --help
python tools/configuration-workbook/workbook.py search "business unit"
python tools/configuration-workbook/workbook.py search "Financials" --limit 10
```

Search returns exact offering, functional-area and task codes. It uses the local
catalog snapshot, which is not evidence that the feature is enabled in a tenant.
Identical task placements are collapsed without using catalog display order as
execution order. Conflicting task content is rejected when selected.

## Prepare a content pack

Use `seed` with exact codes returned by search. This prints JSON to stdout. Save
it in the selected initialized project's blueprints directory using UTF-8.
Repeat `--task` for additional tasks in the same area; a pack can subsequently
contain tasks from any number of offerings/areas.

```powershell
python tools/configuration-workbook/workbook.py seed --offering ORA_SVC_HELP_DESK --area ORA_SVC_COMPANY_PROFILE --task FUN_MANAGE_BUSINESS_UNIT --release YOUR_TARGET_RELEASE
```

Populate the pack using reviewed requirements and the selected pillar skills.
Source-based content authoring may be performed by a human or an AI agent under
FSCR's workflow. **This first version does not perform AI authoring, requirement
document extraction, web research or automatic screenshot capture.** An empty
seed generates a planning shell with explicit quality gaps, not a complete guide.

Top-level fields are `title`, `target_release`, `sources`, and `tasks`.

Each source needs `id`, `title`, `kind`, and `locator`. Oracle documentation
sources use `kind: oracle-documentation`, an HTTPS docs.oracle.com URL, `release`,
and `latest_release_checked_on`. The latter records a researcher's check; the
generator does not verify the web page or infer the latest Fusion release.
Consult the latest available Oracle release documentation during authoring,
record target-release differences, and identify any older-reference fallback.

Each task needs `id`, `offering_code`, `functional_area_code`, and `task_code`.
Supported authoring fields:

| Field | Format |
| --- | --- |
| owner, privileges, context, prerequisites, navigation, save_action | Text |
| source_ids | Array of source IDs |
| steps | Objects with action, source_id, optional expected |
| fields | Objects with name, source_id, proposed_value, approved_value, required, rationale, approved_by |
| requirements | Objects with id, text, source_id |
| tests | Objects with action, expected |
| decisions | Objects with question, owner, due |
| depends_on | Other task IDs in this pack |
| sequence, sequence_source | Reviewed resolver metadata; never inferred from catalog order |
| screenshots | Objects described below |

## Screenshots

Place PNG/JPEG images inside the content pack directory or a child directory:

```json
{
  "path": "screenshots/task-01.png",
  "caption": "Describe the page and the action shown",
  "source_id": "SOURCE-01",
  "kind": "tenant-capture",
  "release": "YOUR_TARGET_RELEASE"
}
```

Kinds are `tenant-capture`, `documentation`, or `illustration`. Each image is
embedded in Excel with a caption, source, release, and SHA256. Illustrations and
release mismatches are flagged. Paths outside the pack folder, missing images,
and corrupt images fail validation. No images are fabricated or downloaded.
Screenshots supplied by the user are not independently authenticated. Remove
secrets and sensitive data before supplying images. Live capture must follow
the selected FSCR workflow; this tool has no browser adapter.

## Validate and generate

Select or initialize a separate project using FSCR's implementation router and
project initializer. Do not use another customer's project or `_template`.
The generator requires an existing `state/project-state.json` and never creates
a Fusion Run Book or substitutes a local sequence for the dependency resolver.

```powershell
python tools/configuration-workbook/workbook.py validate project/MY_PROJECT/blueprints/configuration.json
python tools/configuration-workbook/workbook.py generate project/MY_PROJECT/blueprints/configuration.json --project project/MY_PROJECT --dry-run
python tools/configuration-workbook/workbook.py generate project/MY_PROJECT/blueprints/configuration.json --project project/MY_PROJECT
```

Use `--strict` to reject any reported quality gaps. This checks completeness of
the supplied content, not product correctness, source authenticity, approvals,
or readiness to execute. Dry-run performs validation without writing files.

Each generation creates a unique timestamped directory under
`project/MY_PROJECT/exports/configuration-workbooks/` containing an XLSX and a
JSON generation report, `configuration-guide.md` and `draft-runbook.md` rendered
from the same supplied content. The draft run book preserves unresolved sequence
as pending; it does not create an Oracle Run Book. Existing outputs are never
overwritten. A run record is
also written under `state/runs`, and the project's token log records that the
deterministic generator itself invoked no model. AI authoring token usage must
be recorded separately by the authoring workflow. The generator does not change
project scope, active skills, artifact index or Run Book state; the routed
artifact-registry/state-manager skills remain responsible for registration.

The workbook contains Start Here, Task Index, Quality Gaps, Field Register,
Step Register, Requirements, Validation, Decisions, Sources, Screenshots and
one linked detail sheet per task. It includes filters, frozen headings, print
settings, validation-status dropdowns, and formula-injection protection for
supplied values. Tests start as Not run; approved values are never inferred.

## Tests

```powershell
python -m unittest discover -s tools/configuration-workbook -p "test_*.py" -v
```

Tests use synthetic source content and an explicitly labelled synthetic image,
never customer artifacts or invented Fusion screenshots.
