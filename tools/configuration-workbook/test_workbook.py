"""Contract and output tests using synthetic data; no tenant or customer data."""
import copy
import json
import tempfile
import unittest
import contextlib
import io
from unittest.mock import patch
from pathlib import Path

from openpyxl import load_workbook
from PIL import Image
from workbook import DEFAULT_CATALOG, Invalid, catalog_rows, literal, render, validate
import workbook as generator


class WorkbookTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _, cls.rows = catalog_rows(DEFAULT_CATALOG)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.pack = dict(title='Synthetic contract fixture', target_release='TEST',
                         sources=[dict(id='S1', title='Synthetic fixture', kind='test', locator='test fixture')],
                         tasks=[dict(id='CFG-01', offering_code='ORA_SVC_HELP_DESK',
                                     functional_area_code='ORA_SVC_COMPANY_PROFILE',
                                     task_code='FUN_MANAGE_BUSINESS_UNIT', source_ids=['S1'],
                                     fields=[dict(name='Synthetic field', proposed_value='=1+1', source_id='S1')],
                                     steps=[dict(action='Synthetic test action', source_id='S1')],
                                     tests=[dict(action='Synthetic test', expected='Synthetic result')])])

    def test_workbook_and_image_roundtrip(self):
        Image.new('RGB', (120, 80), 'navy').save(self.base / 'fixture.png')
        self.pack['tasks'][0]['screenshots'] = [dict(path='fixture.png', caption='Synthetic image; not a Fusion screen',
                                                  source_id='S1', kind='illustration', release='TEST')]
        sources, issues, images = validate(self.pack, self.base, self.rows)
        out = self.base / 'fixture.xlsx'
        render(self.pack, self.rows, sources, issues, images, out)
        wb = load_workbook(out)
        self.assertEqual(wb['Task Index']['E2'].value, 'FUN_MANAGE_BUSINESS_UNIT')
        self.assertEqual(wb['Validation']['F2'].value, 'Not run')
        self.assertEqual(wb['Field Register']['C2'].data_type, 's')
        self.assertTrue(wb['Field Register']['C2'].value.startswith("'="))
        self.assertEqual(len(wb['Screenshots']._images), 1)
        self.assertEqual(wb['Task Index']['G2'].hyperlink.target, "#'T001'!A1")
        self.assertTrue(any(issue[1] == 'approved_value' for issue in issues))
        wb.close()

    def test_bad_identity_and_duplicate_ids(self):
        self.pack['tasks'][0]['task_code'] = 'NONEXISTENT'
        with self.assertRaisesRegex(Invalid, 'catalog mismatch'):
            validate(self.pack, self.base, self.rows)
        self.pack['tasks'][0]['task_code'] = 'FUN_MANAGE_BUSINESS_UNIT'
        self.pack['tasks'].append(copy.deepcopy(self.pack['tasks'][0]))
        with self.assertRaisesRegex(Invalid, 'Duplicate'):
            validate(self.pack, self.base, self.rows)

    def test_path_escape_and_missing_image(self):
        task = self.pack['tasks'][0]
        task['screenshots'] = [dict(path='../outside.png', caption='Fixture', source_id='S1', kind='illustration', release='TEST')]
        with self.assertRaisesRegex(Invalid, 'escapes'):
            validate(self.pack, self.base, self.rows)
        task['screenshots'][0]['path'] = 'missing.png'
        with self.assertRaisesRegex(Invalid, 'existing PNG'):
            validate(self.pack, self.base, self.rows)

    def test_dependency_cycle(self):
        second = copy.deepcopy(self.pack['tasks'][0])
        second['id'] = 'CFG-02'
        second['depends_on'] = ['CFG-01']
        self.pack['tasks'][0]['depends_on'] = ['CFG-02']
        self.pack['tasks'].append(second)
        with self.assertRaisesRegex(Invalid, 'cycle'):
            validate(self.pack, self.base, self.rows)

    def test_source_reference_validation(self):
        self.pack['tasks'][0]['steps'][0]['source_id'] = 'UNKNOWN'
        with self.assertRaisesRegex(Invalid, 'source_id'):
            validate(self.pack, self.base, self.rows)

    def test_no_invented_content(self):
        _, issues, images = validate(self.pack, self.base, self.rows)
        self.assertIn(('CFG-01', 'navigation', 'Missing content; needs authoring/review'), issues)
        self.assertEqual(images, [])
        for prefix in ('=', '+', '-', '@'):
            self.assertTrue(literal(prefix + 'test').startswith("'"))

    def test_dry_run_and_generation_audit(self):
        project = self.base / 'project/generic-test'
        (project / 'state').mkdir(parents=True)
        (project / 'state/project-state.json').write_text('{}')
        pack_path = project / 'blueprints/input.json'
        pack_path.parent.mkdir()
        pack_path.write_text(json.dumps(self.pack))
        args = ['--catalog', str(DEFAULT_CATALOG), 'generate', str(pack_path), '--project', str(project)]
        with patch.object(generator, 'ROOT', self.base), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(generator.main(args + ['--dry-run']), 0)
            self.assertFalse((project / 'exports').exists())
            self.assertEqual(generator.main(args), 0)
            self.assertEqual(generator.main(args), 0)
        outputs = list((project / 'exports/configuration-workbooks').glob('*/configuration-workbook.xlsx'))
        self.assertEqual(len(outputs), 2)
        self.assertEqual(len(list((project / 'state/runs').glob('*.json'))), 2)
        report = json.loads(outputs[0].with_name('generation-report.json').read_text())
        self.assertEqual(report['external_operations'], [])
        self.assertEqual(report['token_usage']['model_tokens'], 0)
        self.assertEqual(len(report['artifact_refs']), 3)
        guide = outputs[0].with_name('configuration-guide.md').read_text(encoding='utf-8')
        plan = outputs[0].with_name('draft-runbook.md').read_text(encoding='utf-8')
        self.assertIn('Synthetic field', guide)
        self.assertIn('Approved value', guide)
        self.assertIn('Pending', guide)
        self.assertIn('not run', guide)
        self.assertIn('CFG-01', plan)
        self.assertIn('not execution order', plan)
        self.assertIn('No Fusion configuration', plan)
        self.assertTrue((project / 'artifacts/shared/token-usage/current/token-usage-log.md').exists())

    def test_strict_rejects_incomplete_pack(self):
        pack_path = self.base / 'input.json'
        pack_path.write_text(json.dumps(self.pack))
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(generator.main(['--catalog', str(DEFAULT_CATALOG), 'validate', str(pack_path), '--strict']), 2)


if __name__ == '__main__':
    unittest.main()
