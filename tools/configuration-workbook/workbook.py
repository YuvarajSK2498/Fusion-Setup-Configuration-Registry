"""Offline FSCR catalog-backed configuration workbook generator. No tenant calls."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CATALOG = ROOT / 'knowledge/setup-task-catalog/effective/offering-functional-area-task-catalog.json'


class Invalid(ValueError):
    pass


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def catalog_rows(path):
    catalog = read(path)
    rows = {}
    for offering_code, offering in catalog['offerings'].items():
        for area_code, area in offering['functionalAreas'].items():
            for task in area.get('tasks', []):
                code = task['taskShortName']
                key = (offering_code, area_code, code)
                if key in rows:
                    semantic = lambda t: {k: v for k, v in t.items() if k not in ('displaySequence', 'taskListItemShortName')}
                    if semantic(rows[key]['task']) != semantic(task):
                        rows[key]['ambiguous'] = True
                    continue
                rows[key] = {'offering': offering['offeringName'],
                             'area': area['functionalAreaName'], 'task': task}
    return catalog, rows


def require(condition, message):
    if not condition:
        raise Invalid(message)


def validate(pack, base, rows):
    require(isinstance(pack, dict), 'Input must be a JSON object')
    for key in ('title', 'target_release', 'tasks'):
        require(pack.get(key), f'Missing {key}')
    require(isinstance(pack['tasks'], list), 'tasks must be an array')
    sources = {}
    for source in pack.get('sources', []):
        sid = source.get('id')
        require(sid and sid not in sources, 'Missing or duplicate source id')
        require(source.get('title') and source.get('locator'), f'{sid}: source title and locator required')
        if source.get('kind') == 'oracle-documentation':
            parsed = urlparse(source['locator'])
            require(parsed.scheme == 'https' and parsed.hostname == 'docs.oracle.com',
                    f'{sid}: Oracle documentation must use https://docs.oracle.com')
        sources[sid] = source
    ids = set()
    issues = []
    images = []
    for task in pack['tasks']:
        tid = task.get('id')
        require(isinstance(tid, str) and re.fullmatch(r'[A-Za-z0-9_-]+', tid), 'Task id must contain letters, digits, _ or -')
        require(tid not in ids, f'Duplicate task id: {tid}')
        ids.add(tid)
        identity = tuple(task.get(k) for k in ('offering_code', 'functional_area_code', 'task_code'))
        require(identity in rows, f'{tid}: catalog mismatch for {identity}')
        require(not rows[identity].get('ambiguous'), f'{tid}: ambiguous catalog content for {identity}')
        for sid in task.get('source_ids', []):
            require(sid in sources, f'{tid}: unknown source {sid}')
        for key in ('owner', 'privileges', 'navigation', 'save_action', 'steps', 'fields', 'tests', 'source_ids'):
            if not task.get(key):
                issues.append((tid, key, 'Missing content; needs authoring/review'))
        if not task.get('screenshots'):
            issues.append((tid, 'screenshots', 'No screenshot evidence supplied'))
        if not task.get('sequence_source'):
            issues.append((tid, 'sequence', 'Execution sequence unresolved; workbook order is not execution order'))
        for sid in task.get('source_ids', []):
            source = sources[sid]
            if source.get('kind') == 'oracle-documentation':
                if not source.get('latest_release_checked_on'):
                    issues.append((tid, 'source', f'{sid}: latest-release verification missing'))
                if source.get('release') != pack['target_release']:
                    issues.append((tid, 'release', f'{sid}: source release differs from target'))
        for field in task.get('fields', []):
            require(field.get('name'), f'{tid}: field name required')
            require(field.get('source_id') in sources, f'{tid}: field source_id required')
            if field.get('approved_value') in (None, ''):
                issues.append((tid, 'approved_value', f"{field['name']}: approved value pending"))
        for requirement in task.get('requirements', []):
            require(isinstance(requirement, dict) and requirement.get('id') and requirement.get('text')
                    and requirement.get('source_id') in sources,
                    f'{tid}: requirements need id, text and known source_id')
        for step in task.get('steps', []):
            require(step.get('action') and step.get('source_id') in sources,
                    f'{tid}: each step needs action and known source_id')
        for test in task.get('tests', []):
            require(test.get('action') and test.get('expected'), f'{tid}: test action and expected result required')
        for shot in task.get('screenshots', []):
            require(shot.get('source_id') in sources, f'{tid}: screenshot source_id required')
            require(shot.get('caption') and shot.get('release') and shot.get('kind') in
                    ('tenant-capture', 'documentation', 'illustration'), f'{tid}: screenshot caption/release/kind required')
            image_path = (base / shot.get('path', '')).resolve()
            require(image_path.is_relative_to(base.resolve()), f'{tid}: screenshot path escapes input folder')
            require(image_path.is_file() and image_path.suffix.lower() in ('.png', '.jpg', '.jpeg'),
                    f'{tid}: screenshot must be an existing PNG/JPEG')
            from PIL import Image
            with Image.open(image_path) as im:
                require(im.width * im.height <= 40_000_000, f'{tid}: image is too large')
                im.verify()
            if shot['release'] != pack['target_release'] or shot['kind'] == 'illustration':
                issues.append((tid, 'screenshot', 'Illustration or different release; not target tenant evidence'))
            images.append((tid, shot, image_path))
    for task in pack['tasks']:
        for dep in task.get('depends_on', []):
            require(dep in ids and dep != task['id'], f"{task['id']}: invalid dependency {dep}")
    graph = {t['id']: t.get('depends_on', []) for t in pack['tasks']}
    active, done = set(), set()
    def visit(tid):
        require(tid not in active, f'Dependency cycle at {tid}')
        if tid in done:
            return
        active.add(tid)
        for dep in graph[tid]:
            visit(dep)
        active.remove(tid)
        done.add(tid)
    for tid in graph:
        visit(tid)
    return sources, issues, images


def literal(value):
    if value is None:
        return ''
    if isinstance(value, (dict, list)):
        value = json.dumps(value, ensure_ascii=False)
    text = str(value)
    # All user-supplied values must remain text, including Excel formula prefixes.
    return "'" + text if text.startswith(('=', '+', '-', '@')) else text


def render(pack, rows, sources, issues, images, destination):
    from openpyxl import Workbook
    from openpyxl.drawing.image import Image as ExcelImage
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.worksheet.datavalidation import DataValidation
    from openpyxl.utils import get_column_letter
    wb = Workbook()
    wb.remove(wb.active)
    def sheet(name, headers, data):
        ws = wb.create_sheet(name)
        ws.append(headers)
        for row in data:
            ws.append([literal(value) for value in row])
        ws.freeze_panes = 'B2'
        ws.auto_filter.ref = ws.dimensions
        ws.sheet_view.showGridLines = False
        ws.sheet_properties.pageSetUpPr.fitToPage = True
        ws.page_setup.orientation = 'landscape'
        ws.page_setup.paperSize = ws.PAPERSIZE_A3
        ws.page_setup.fitToWidth = 1
        ws.page_setup.fitToHeight = 0
        ws.print_title_rows = '1:1'
        for cell in ws[1]:
            cell.fill = PatternFill('solid', fgColor='17324D')
            cell.font = Font(color='FFFFFF', bold=True)
        for row in ws.iter_rows(min_row=2):
            ws.row_dimensions[row[0].row].height = 56
            for cell in row:
                cell.alignment = Alignment(vertical='top', wrap_text=True)
                cell.font = Font(name='Calibri', size=11, color='17324D')
                if cell.row % 2 == 0:
                    cell.fill = PatternFill('solid', fgColor='EDF4F8')
        for i, heading in enumerate(headers, 1):
            ws.column_dimensions[get_column_letter(i)].width = 22 if i == 1 else 38
        return ws
    sheet('Start Here', ['Item', 'Value'], [
        ('Workbook', pack['title']), ('Target release', pack['target_release']),
        ('Mode', 'Offline planning draft; not approval or evidence of execution'),
        ('Tasks', len(pack['tasks'])), ('Open quality gaps', len(issues)),
        ('Screenshots supplied', len(images)),
        ('How to use', 'Review Quality Gaps, then Task Index. Author missing fields and approve values before execution.'),
        ('Ordering', 'Document order only. Execution order requires the routed FSCR dependency resolver.'),
        ('Evidence', 'Captions identify source/release. Illustrations are not tenant screenshots.'),
        ('Data', 'Keep workbook and images in the untracked project workspace; never supply credentials.')])
    index_data, field_data, step_data, test_data, trace_data, decision_data = [], [], [], [], [], []
    for number, task in enumerate(pack['tasks'], 1):
        tid = task['id']
        entry = rows[(task['offering_code'], task['functional_area_code'], task['task_code'])]
        raw = entry['task']
        name = f'T{number:03d}'
        index_data.append((tid, raw['taskName'], entry['offering'], entry['area'], task['task_code'],
                           task.get('owner'), name, 'Needs review', task.get('sequence'), task.get('sequence_source')))
        detail = [('Task ID', tid), ('Task', raw['taskName']), ('Offering', entry['offering']),
                  ('Functional area', entry['area']), ('Catalog description', raw.get('taskDescription')),
                  ('Owner', task.get('owner')), ('Roles / privileges', task.get('privileges')),
                  ('Scope / context', task.get('context')), ('Prerequisites', task.get('prerequisites')),
                  ('Dependencies', task.get('depends_on')), ('Navigation', task.get('navigation')),
                  ('Save / submit', task.get('save_action')), ('Source IDs', task.get('source_ids')),
                  ('Screenshots', 'See Screenshots sheet; absence is recorded in Quality Gaps')]
        for n, step in enumerate(task.get('steps', []), 1):
            detail.append((f'Step {n}', step['action']))
            step_data.append((tid, n, step['action'], step.get('expected'), step['source_id']))
        ws = sheet(name, ['Control', 'Instruction / value'], detail)
        ws.column_dimensions['B'].width = 110
        ws['D1'] = 'Back to Task Index'
        ws['D1'].hyperlink = "#'Task Index'!A1"
        for field in task.get('fields', []):
            field_data.append((tid, field['name'], field.get('proposed_value'), field.get('approved_value'),
                               field.get('required'), field.get('rationale'), field['source_id'], field.get('approved_by')))
        for n, test in enumerate(task.get('tests', []), 1):
            test_data.append((tid, f'{tid}-TEST-{n}', test['action'], test['expected'], '', 'Not run', ''))
        for requirement in task.get('requirements', []):
            require(isinstance(requirement, dict) and requirement.get('id') and requirement.get('text'),
                    f'{tid}: requirements require id and text')
            trace_data.append((requirement['id'], requirement['text'], requirement.get('source_id'), tid, name))
        for decision in task.get('decisions', []):
            decision_data.append((tid, decision.get('question'), decision.get('owner'), decision.get('due'), 'Open', ''))
    ws = sheet('Task Index', ['Task ID', 'Task', 'Offering', 'Functional area', 'Task code', 'Owner', 'Open procedure',
                              'Review status', 'Resolver sequence', 'Sequence source'], index_data)
    for row in range(2, ws.max_row + 1):
        ws.cell(row, 7).hyperlink = f"#'{ws.cell(row, 7).value}'!A1"
        ws.cell(row, 7).style = 'Hyperlink'
    sheet('Field Register', ['Task ID', 'Field', 'Proposed value', 'Approved value', 'Required', 'Rationale', 'Source ID', 'Approver'], field_data)
    sheet('Step Register', ['Task ID', 'Step', 'Action', 'Expected screen / result', 'Source ID'], step_data)
    tests = sheet('Validation', ['Task ID', 'Test ID', 'Action', 'Expected', 'Actual', 'Status', 'Evidence'], test_data)
    dropdown = DataValidation(type='list', formula1='"Not run,Passed,Failed,Blocked"')
    tests.add_data_validation(dropdown)
    dropdown.add(f'F2:F{max(2, tests.max_row)}')
    sheet('Requirements', ['Requirement ID', 'Requirement', 'Source ID', 'Task ID', 'Procedure'], trace_data)
    sheet('Decisions', ['Task ID', 'Question', 'Owner', 'Due date', 'Status', 'Resolution'], decision_data)
    sheet('Sources', ['Source ID', 'Title', 'Kind', 'Locator', 'Source release', 'Latest checked on'], [
        (sid, s['title'], s.get('kind'), s['locator'], s.get('release'), s.get('latest_release_checked_on'))
        for sid, s in sources.items()])
    sheet('Quality Gaps', ['Task ID', 'Area', 'Required action'], issues)
    shots = sheet('Screenshots', ['Task ID', 'Caption', 'Kind', 'Release', 'Source ID', 'SHA256'], [
        (tid, shot['caption'], shot['kind'], shot['release'], shot['source_id'], digest(path))
        for tid, shot, path in images])
    anchor = max(4, len(images) + 4)
    for tid, shot, path in images:
        shots.cell(anchor, 1, literal(f"{tid}: {shot['caption']} [{shot['kind']}; {shot['release']}]"))
        img = ExcelImage(str(path))
        scale = min(960 / img.width, 540 / img.height, 1)
        img.width, img.height = img.width * scale, img.height * scale
        shots.add_image(img, f'A{anchor + 1}')
        anchor += int(img.height / 20) + 5
    # Put orientation sheets first; task detail sheets follow the registers.
    names = ['Start Here', 'Task Index', 'Quality Gaps', 'Field Register', 'Step Register', 'Requirements',
             'Validation', 'Decisions', 'Sources', 'Screenshots']
    wb._sheets.sort(key=lambda ws: (names.index(ws.title) if ws.title in names else len(names), ws.title))
    wb.save(destination)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalog', type=Path, default=DEFAULT_CATALOG)
    commands = parser.add_subparsers(dest='command', required=True)
    search = commands.add_parser('search', help='Search local catalog; never contacts Fusion')
    search.add_argument('query', nargs='?', default='')
    search.add_argument('--limit', type=int, default=30)
    seed = commands.add_parser('seed', help='Print an unpopulated content pack for exact catalog task identities')
    seed.add_argument('--offering', required=True)
    seed.add_argument('--area', required=True)
    seed.add_argument('--task', required=True, action='append')
    seed.add_argument('--release', required=True)
    seed.add_argument('--title', default='Fusion Configuration Workbook')
    for name in ('validate', 'generate'):
        command = commands.add_parser(name)
        command.add_argument('input', type=Path)
        command.add_argument('--strict', action='store_true', help='Fail if any quality gaps exist')
        if name == 'generate':
            command.add_argument('--project', type=Path, required=True, help='Initialized FSCR project directory')
            command.add_argument('--dry-run', action='store_true')
    args = parser.parse_args(argv)
    try:
        catalog, rows = catalog_rows(args.catalog)
        if args.command == 'seed':
            tasks = []
            for number, code in enumerate(args.task, 1):
                require((args.offering, args.area, code) in rows, f'Unknown task context: {code}')
                tasks.append(dict(id=f'CFG-{number:03d}', offering_code=args.offering,
                                  functional_area_code=args.area, task_code=code,
                                  owner='', privileges='', context='', prerequisites='', navigation='',
                                  save_action='', source_ids=[], steps=[], fields=[], tests=[],
                                  requirements=[], decisions=[], screenshots=[], depends_on=[]))
            print(json.dumps(dict(title=args.title, target_release=args.release, sources=[], tasks=tasks), indent=2))
            return 0
        if args.command == 'search':
            found = [dict(offering_code=k[0], functional_area_code=k[1], task_code=k[2],
                          offering=v['offering'], functional_area=v['area'], task=v['task']['taskName'])
                     for k, v in rows.items() if args.query.casefold() in
                     ' '.join([*k, v['offering'], v['area'], v['task']['taskName']]).casefold()]
            print(json.dumps({'matches': len(found), 'items': found[:max(0, args.limit)]}, indent=2))
            return 0
        pack = read(args.input)
        sources, issues, images = validate(pack, args.input.resolve().parent, rows)
        summary = {'status': 'needs_review' if issues else 'ready_for_review', 'tasks': len(pack['tasks']),
                   'quality_gaps': len(issues), 'screenshots': len(images), 'external_operations': []}
        if args.strict:
            require(not issues, f'{len(issues)} quality gaps; use validate without --strict to inspect')
        if args.command == 'validate':
            print(json.dumps({**summary, 'issues': issues}, indent=2))
            return 0
        project = args.project.resolve()
        require(project.parent == (ROOT / 'project').resolve() and project.name != '_template',
                'Project must be a direct child of repository project/ and cannot be _template')
        require((project / 'state/project-state.json').is_file(), 'Use the FSCR project initializer before generating')
        if args.dry_run:
            print(json.dumps({**summary, 'dry_run': True, 'destination': str(project / 'exports/configuration-workbooks')}, indent=2))
            return 0
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        destination = project / 'exports/configuration-workbooks' / stamp
        destination.mkdir(parents=True, exist_ok=False)
        workbook = destination / 'configuration-workbook.xlsx'
        try:
            render(pack, rows, sources, issues, images, workbook)
            write_documents(pack, rows, sources, issues, destination)
        except Exception:
            if workbook.exists():
                workbook.unlink()
            raise
        audit = {**summary, 'run_id': stamp, 'stage': 'artifact_persistence', 'environment': 'offline',
                 'catalog_sha256': digest(args.catalog), 'input_sha256': digest(args.input),
                 'workbook_sha256': digest(workbook),
                 'artifact_refs': [str((destination / name).relative_to(project)) for name in
                                   ('configuration-workbook.xlsx', 'configuration-guide.md', 'draft-runbook.md')],
                 'catalog_generated_at': catalog.get('generatedAt'), 'issues': issues,
                 'recommended_action': 'Review Quality Gaps and approve client values before any execution',
                 'token_usage': {'model_tokens': 0, 'method': 'No model/API invoked by this deterministic generator'}}
        (destination / 'generation-report.json').write_text(json.dumps(audit, indent=2), encoding='utf-8')
        runs = project / 'state/runs'
        runs.mkdir(parents=True, exist_ok=True)
        (runs / f'configuration-workbook-{stamp}.json').write_text(json.dumps(audit, indent=2), encoding='utf-8')
        usage = project / 'artifacts/shared/token-usage/current/token-usage-log.md'
        usage.parent.mkdir(parents=True, exist_ok=True)
        with usage.open('a', encoding='utf-8') as stream:
            stream.write(f'\n- {stamp}: standalone configuration-workbook generator; '
                         f'input={args.input.name}; artifact={workbook.relative_to(project)}; '
                         'model input/output/total tokens=0; no model invoked.\n')
        print(json.dumps({**summary, 'workbook': str(workbook),
                          'configuration_guide': str(destination / 'configuration-guide.md'),
                          'draft_runbook': str(destination / 'draft-runbook.md')}, indent=2))
        return 0
    except (Invalid, KeyError, TypeError, OSError, ValueError) as exc:
        print(json.dumps({'status': 'failed', 'failure_class': 'input validation', 'message': str(exc),
                          'recommended_action': 'Correct the input or source paths; no Fusion operation was performed'}), file=sys.stderr)
        return 2


def write_documents(pack, rows, sources, issues, destination):
    """Render the same reviewed content as private, portable Markdown drafts."""
    import html

    def safe(value):
        if value is None or value == '' or value == []:
            return 'Pending'
        if isinstance(value, (dict, list)):
            value = json.dumps(value, ensure_ascii=False)
        return html.escape(str(value)).replace('|', '&#124;').replace('\r', '').replace('\n', '<br>')

    intro = [f'# {safe(pack["title"])}', '',
             'Draft for review. No Fusion configuration or live Run Book has been created.', '',
             f'Target release: {safe(pack["target_release"])}. Open quality gaps: {len(issues)}.', '',
             'Document order is not execution order. Only reviewed resolver metadata establishes sequence.', '']
    guide = intro.copy()
    runbook = intro + ['| Task | Name | Owner | Resolver sequence | Sequence source | Dependencies | Status |',
                       '| --- | --- | --- | --- | --- | --- | --- |']
    for task in pack['tasks']:
        entry = rows[(task['offering_code'], task['functional_area_code'], task['task_code'])]
        name = entry['task']['taskName']
        guide += [f'## {safe(task["id"])}: {safe(name)}', '',
                  f'Offering: {safe(entry["offering"])}. Functional area: {safe(entry["area"])}.', '']
        for key in ('owner', 'privileges', 'context', 'prerequisites', 'navigation', 'save_action', 'source_ids'):
            guide += [f'**{key.replace("_", " ").title()}:** {safe(task.get(key))}', '']
        guide += ['### Steps', '']
        for number, step in enumerate(task.get('steps', []), 1):
            guide += [f'{number}. {safe(step["action"])} — Expected: {safe(step.get("expected"))}; source: {safe(step["source_id"])}']
        if not task.get('steps'):
            guide += ['Pending source-based authoring.']
        guide += ['', '### Configuration values', '',
                  '| Field | Proposed value | Approved value | Source |', '| --- | --- | --- | --- |']
        for field in task.get('fields', []):
            guide += ['| ' + ' | '.join(safe(field.get(k)) for k in
                                      ('name', 'proposed_value', 'approved_value', 'source_id')) + ' |']
        guide += ['', '### Requirements', '']
        guide += [f'- {safe(req["id"])}: {safe(req["text"])}; source: {safe(req["source_id"])}'
                  for req in task.get('requirements', [])] or ['Pending.']
        guide += ['', '### Validation (not run)', '']
        guide += [f'- {safe(test["action"])} — Expected: {safe(test["expected"])}'
                  for test in task.get('tests', [])] or ['Pending.']
        guide += ['', '### Open decisions', '']
        guide += [f'- {safe(d.get("question"))}; owner: {safe(d.get("owner"))}; due: {safe(d.get("due"))}'
                  for d in task.get('decisions', [])] or ['None supplied; requires review.']
        guide += ['']
        runbook += ['| ' + ' | '.join(safe(v) for v in
                    (task['id'], name, task.get('owner'), task.get('sequence'),
                     task.get('sequence_source'), task.get('depends_on'), 'Not started; needs review')) + ' |']
    appendix = ['', '## Sources', '']
    appendix += [f'- {safe(sid)}: {safe(source["title"])} — {safe(source["locator"])}; '
                 f'release: {safe(source.get("release"))}; latest checked: {safe(source.get("latest_release_checked_on"))}'
                 for sid, source in sources.items()]
    appendix += ['', '## Quality gaps', '']
    appendix += [f'- {safe(tid)} / {safe(area)}: {safe(message)}' for tid, area, message in issues] or ['None detected by structural checks; human review remains required.']
    for name, content in [('configuration-guide.md', guide), ('draft-runbook.md', runbook)]:
        (destination / name).write_text('\n'.join(content + appendix) + '\n', encoding='utf-8')


if __name__ == '__main__':
    sys.exit(main())
