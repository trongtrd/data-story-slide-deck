"""Regression tests for the independent P7 review; all writes stay in temporary folders."""
import contextlib
import copy
from datetime import date
import importlib.util
import io
import re
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / '40_plugin/scripts'))
import yaml
from pptx.enum.dml import MSO_FILL
from pptx.oxml.ns import qn
import chart_marks
import deckctl
import html_renderer
import pptx_renderer
import validate_spec
from spec_digest import file_sha256

loader = importlib.util.spec_from_file_location('pai_installer', ROOT / '40_plugin/install.py')
installer = importlib.util.module_from_spec(loader)
loader.loader.exec_module(installer)

def content_slides(deck):
    """D-075: the deck's slides after the unnumbered title slide, so position i is spec slide i."""
    from pptx import Presentation
    prs = deck if hasattr(deck, 'slides') else Presentation(str(deck))
    return [sl for sl in prs.slides if not any(sh.name == 'pai:deck_title' for sh in sl.shapes)]


class ReviewRegressions(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='pai_review_test_')
        self.addCleanup(self.tmp.cleanup)
        self.work = Path(self.tmp.name) / 'workspace'
        self.work.mkdir()
        self.output = contextlib.redirect_stdout(io.StringIO())
        self.output.__enter__()
        self.addCleanup(self.output.__exit__, None, None, None)

    def fixture(self):
        shutil.copytree(ROOT / '50_evals/runs/bench_en_coffee_two_tier', self.work, dirs_exist_ok=True)
        return self.work / 'artifacts/slide_spec.yaml'

    def text_source(self, content):
        (self.work / 'inputs').mkdir()
        (self.work / 'inputs/report.md').write_text(content, encoding='utf-8')
        return validate_spec.SourceResolver(self.work / 'inputs')

    def test_text_scope_and_sign(self):
        r = self.text_source('# Revenue\nRevenue is 100.\n# Costs\nCosts are 50.\n')
        self.assertEqual(r.check('report.md!Revenue', 100, '', None)[0], 'ok')
        self.assertEqual(r.check('report.md!Costs', 100, '', None)[0], 'error')
        self.assertEqual(r.check('report.md!Revenue', -100, '', None)[0], 'error')
        self.assertEqual(r.check('report.md!Missing', 100, '', None)[0], 'error')

    def test_duplicate_heading_is_not_evidence(self):
        r = self.text_source('# Costs\n50\n# Costs\n100\n')
        self.assertEqual(r.check('report.md!Costs', 50, '', None)[0], 'error')

    def test_subsection_and_signed_value(self):
        r = self.text_source('# Results\n## Change\nChange is -50.\n# Other\n100\n')
        self.assertEqual(r.check('report.md!Results', -50, '', None)[0], 'ok')
        self.assertEqual(r.check('report.md!Results', 100, '', None)[0], 'error')

    def test_exact_line_and_unit_factor(self):
        r = self.text_source('Revenue is 1000.\nCosts are 50.\n')
        self.assertEqual(r.check('report.md!Revenue is 1000.', 1, '', None, .001)[0], 'ok')

    def test_build_missing_upstream_preserves_existing_output(self):
        self.fixture()
        (self.work / 'artifacts/context_brief.md').unlink()
        output = self.work / 'output/presentation.pptx'
        digest = file_sha256(output)
        self.assertEqual(deckctl.cmd_build(self.work, False, skip_qa=True), 1)
        self.assertEqual(file_sha256(output), digest)

    def pending_g4_fixture(self):
        path = self.fixture()
        spec = yaml.safe_load(path.read_text(encoding='utf-8'))
        spec['g4_review_audit']['status'] = 'pending'
        path.write_text(yaml.safe_dump(spec), encoding='utf-8')

    def test_rebuild_keeps_deck_edited_after_last_build(self):
        # D-062 R1: a .pptx changed in PowerPoint since the last build is copied aside, never silently overwritten
        self.pending_g4_fixture()
        out = self.work / 'output'
        self.assertEqual(deckctl.cmd_build(self.work, False, skip_qa=True), 0)
        self.assertIn('presentation.pptx', deckctl.recorded_outputs(out))
        self.assertEqual(deckctl.cmd_build(self.work, False, skip_qa=True), 0)
        self.assertEqual(list(out.glob('*.edited-*')), [])
        deck = out / 'presentation.pptx'
        deck.write_bytes(deck.read_bytes() + b'user edit')
        edited = file_sha256(deck)
        self.assertEqual(deckctl.cmd_build(self.work, False, skip_qa=True), 0)
        kept = list(out.glob('presentation.edited-*.pptx'))
        self.assertEqual(len(kept), 1)
        self.assertEqual(file_sha256(kept[0]), edited)
        self.assertEqual(deckctl.recorded_outputs(out)['presentation.pptx'], file_sha256(deck))

    def test_first_build_without_manifest_keeps_nothing(self):
        self.pending_g4_fixture()
        out = self.work / 'output'
        (out / deckctl.BUILD_MANIFEST).unlink(missing_ok=True)
        self.assertEqual(deckctl.keep_hand_edits(out), [])
        deckctl.record_outputs(out, [out / 'presentation.pptx'])
        (out / 'presentation_live_reveal.pptx').write_bytes(b'not rebuilt')
        deckctl.record_outputs(out, [out / 'presentation_live_reveal.pptx'])
        self.assertEqual(set(deckctl.recorded_outputs(out)), {'presentation.pptx', 'presentation_live_reveal.pptx'})

    def test_word_wider_than_box_warns(self):
        # D-062 R2: PowerPoint breaks a word wider than its box mid-word; the fix is a wider box, never smaller type
        import pptx_qa
        from pptx import Presentation
        from pptx.util import Inches, Pt
        prs = Presentation()
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        for name, width in (('pai:step', 1.2), ('pai:callout', 6.0)):
            box = slide.shapes.add_textbox(Inches(0.5), Inches(1), Inches(width), Inches(1))
            box.name = name
            box.text_frame.word_wrap = True
            run = box.text_frame.paragraphs[0].add_run()
            run.text, run.font.size = 'Internationalisation plan', Pt(18)
        deck = self.work / 'fit.pptx'
        prs.save(deck)
        warns = pptx_qa.word_fit_warnings(deck)
        self.assertEqual(len(warns), 1)
        self.assertIn("'pai:step'", warns[0])
        self.assertIn('Internationalisation', warns[0])

    def spec_warnings(self, edit):
        path = self.fixture()
        spec = yaml.safe_load(path.read_text(encoding='utf-8'))
        edit(spec)
        return validate_spec.validate_slide_spec_dict(spec, 't', self.work)['warnings']

    def test_formula_drama_title_warns(self):
        # D-062 R3: reframe formulas warn; plain negation and additive "không chỉ … mà còn" do not
        def set_title(text):
            return lambda spec: spec['slides'][0]['word_jobs']['takeaway_title'].update(text=text)
        drama = [w for w in self.spec_warnings(set_title("It’s not a price problem, it’s a timing problem.")) if 'ANTI-TTL-003' in w]
        self.assertEqual(len(drama), 1)
        for plain in ("Price is not enough to explain the drop in evening sales.", "Doanh thu không chỉ tăng mà còn ổn định suốt quý bốn."):
            self.assertFalse(any('ANTI-TTL-003' in w for w in self.spec_warnings(set_title(plain))), plain)
        self.assertTrue(validate_spec.FORMULA_DRAMA_RE.search('Không phải thiếu người mà là xếp ca sai giờ'))

    def test_straight_quotes_warn_once_per_slide(self):
        # D-062 R4: straight quotes in audience text or notes warn, one line per slide; abbreviated years are exempt
        def edit(spec):
            wj = spec['slides'][0]['word_jobs']
            wj['chart_title'] = "Sales by café's region, '24"
            wj['source_footnote'] = 'Source: "Menu review" survey.'
        quotes = [w for w in self.spec_warnings(edit) if 'straight quotes' in w]
        self.assertEqual(len(quotes), 1)
        self.assertIn('2 string(s)', quotes[0])
        self.assertIsNone(validate_spec.STRAIGHT_QUOTE_RE.search("Revenue in ’24 and '25, a 6'2\" screen"))
        self.assertFalse(any('straight quotes' in w for w in self.spec_warnings(lambda spec: None)))

    def test_build_rejects_bad_source_before_renderer(self):
        path = self.fixture()
        spec = yaml.safe_load(path.read_text(encoding='utf-8'))
        spec['slides'][0]['visual_spec']['panels'][0]['series'][0]['data_points'][0]['source_cell_ref'] = 'missing.csv!R2C2'
        path.write_text(yaml.safe_dump(spec), encoding='utf-8')
        with patch('pptx_renderer.compile_pptx') as compile_mock:
            self.assertEqual(deckctl.cmd_build(self.work, False, skip_qa=True), 1)
            compile_mock.assert_not_called()

    def test_missing_inputs_is_build_error(self):
        self.fixture()
        with patch.object(Path, 'is_dir', return_value=False):
            errors = deckctl.prebuild_errors(self.work)
        self.assertTrue(any('Missing inputs/' in e for e in errors))

    def test_unapproved_and_edited_upstream_rejected(self):
        self.fixture()
        path = self.work / 'artifacts/storyline.md'
        text = path.read_text(encoding='utf-8')
        path.write_text(text.replace('checkpoint_g3_status: approved', 'checkpoint_g3_status: pending'), encoding='utf-8')
        self.assertTrue(any('must be approved' in e for e in deckctl.prebuild_errors(self.work)))
        path.write_text(text + '\nChanged after approval.\n', encoding='utf-8')
        self.assertTrue(any('hash mismatch' in e for e in deckctl.prebuild_errors(self.work)))

    def test_valid_pre_g4_build_is_allowed(self):
        path = self.fixture()
        spec = yaml.safe_load(path.read_text(encoding='utf-8'))
        spec['g4_review_audit']['status'] = 'pending'
        path.write_text(yaml.safe_dump(spec), encoding='utf-8')
        self.assertEqual(deckctl.prebuild_errors(self.work), [])

    def test_smoke_keep_never_removes_existing_files(self):
        sentinel = self.work / 'keep.txt'
        sentinel.write_text('user data', encoding='utf-8')
        self.assertEqual(deckctl.cmd_smoke(self.work), 2)
        self.assertEqual(sentinel.read_text(encoding='utf-8'), 'user data')

    def test_stale_qa_stops_before_render(self):
        path = self.fixture()
        spec = yaml.safe_load(path.read_text(encoding='utf-8'))
        spec['deck_meta']['deck_title'] = 'Edited after rendering'
        path.write_text(yaml.safe_dump(spec), encoding='utf-8')
        with patch('render_qa_pngs.render_qa_pngs') as render:
            self.assertEqual(deckctl.cmd_qa(self.work), 2)
            render.assert_not_called()

    def test_current_qa_can_render(self):
        self.fixture()
        manifest = self.work / 'renders/render_manifest.json'
        manifest.write_text('{"render_source": "pptx_powerpoint"}', encoding='utf-8')
        with patch('render_qa_pngs.render_qa_pngs', return_value=manifest) as render:
            self.assertEqual(deckctl.cmd_qa(self.work), 0)
            render.assert_called_once()

    def test_no_renderer_still_builds_with_labelled_previews(self):
        # D-044: without PowerPoint or LibreOffice the deck stands and renders/ holds previews that are not G4 evidence
        import render_qa_pngs
        self.fixture()
        with patch.dict('os.environ', {'DATA_STORY_SLIDE_DECK_RENDERER': 'none'}):
            self.assertEqual(render_qa_pngs.choose_renderers(), [])
            self.assertEqual(deckctl.cmd_qa(self.work), 0)
        manifest = yaml.safe_load((self.work / 'renders/render_manifest.json').read_text(encoding='utf-8'))
        self.assertEqual(manifest['render_source'], 'pillow_preview')
        spec = yaml.safe_load((self.work / 'artifacts/slide_spec.yaml').read_text(encoding='utf-8'))
        warns = validate_spec.validate_slide_spec_dict(spec, 't', self.work)['warnings']
        self.assertTrue(any('D-044' in w and 'presentation.pptx' in w for w in warns))

    def test_renderer_order_and_forced_choice(self):
        import render_qa_pngs
        with patch.object(render_qa_pngs, 'find_powerpoint', return_value=True), patch.object(render_qa_pngs, 'find_soffice', return_value='soffice'):
            self.assertEqual([n for n, _ in render_qa_pngs.choose_renderers('auto')], ['powerpoint', 'libreoffice'])
            self.assertEqual([n for n, _ in render_qa_pngs.choose_renderers('libreoffice')], ['libreoffice'])
        with patch.object(render_qa_pngs, 'find_powerpoint', return_value=False), patch.object(render_qa_pngs, 'find_soffice', return_value=None):
            with self.assertRaises(render_qa_pngs.RendererUnavailable):
                render_qa_pngs.render_qa_pngs(self.work / 'x.pptx', self.work / 'r', renderer='auto')

    def test_claude_failure_is_propagated(self):
        with patch.object(installer.shutil, 'which', return_value='fake-claude'), patch.object(installer.subprocess, 'call', return_value=7):
            with self.assertRaises(SystemExit):
                installer.claude_code('user', False, False)

    def test_missing_claude_is_not_success(self):
        with patch.object(installer.shutil, 'which', return_value=None):
            with self.assertRaises(SystemExit):
                installer.claude_code('user', False, False)

    def test_install_uninstall_preserves_unmanaged_skills(self):
        skills = self.work / 'skills'
        unmanaged = skills / 'deck-builder'
        unmanaged.mkdir(parents=True)
        (unmanaged / 'keep.txt').write_text('user data', encoding='utf-8')
        installer.install_skill_copies(ROOT / '40_plugin', skills, False, False)
        self.assertEqual(len(list(skills.glob('*/.data-story-slide-deck-managed'))), 6)
        installer.remove_skill_copies(skills, False)
        self.assertTrue((unmanaged / 'keep.txt').exists())
        self.assertEqual(len(list(skills.glob('*/.data-story-slide-deck-managed'))), 0)

    def bars(self, family, values, lo=-100, hi=0):
        panel = {'chart_family': family, 'x_axis': {'categories': ['A']}, 'y_axis': {'min': lo, 'max': hi},
                 'series': [{'color_hex': '#D95F02', 'data_points': [{'category': 'A', 'value': v}]} for v in values]}
        svg = html_renderer.render_svg_chart_panel(panel, {}, {})
        return [{k: float(el.attrib[k]) for k in ('x','y','width','height')}
                for el in ET.fromstring(svg).iter() if el.tag.endswith('rect') and el.get('fill') == '#D95F02']

    def test_negative_vertical_bar_uses_zero_endpoint(self):
        full = self.bars('vertical_bar_chart', [-100], -200)[0]
        half = self.bars('vertical_bar_chart', [-50], -200)[0]
        zero = self.bars('vertical_bar_chart', [0], -200)[0]
        self.assertAlmostEqual(full['height'], 2 * half['height'], delta=.2)
        self.assertEqual(zero['height'], 0)

    def test_negative_horizontal_bar_uses_zero_endpoint(self):
        full = self.bars('horizontal_bar_chart', [-100], -200)[0]
        half = self.bars('horizontal_bar_chart', [-50], -200)[0]
        zero = self.bars('horizontal_bar_chart', [0], -200)[0]
        self.assertAlmostEqual(full['width'], 2 * half['width'], delta=.2)
        self.assertEqual(zero['width'], 0)

    def test_mixed_stack_separates_signs(self):
        positive, negative = self.bars('stacked_bar_chart', [50, -50], -100, 100)
        self.assertAlmostEqual(positive['height'], negative['height'], delta=.2)
        self.assertAlmostEqual(positive['y'] + positive['height'], negative['y'], delta=.2)

class EditorialRegressions(unittest.TestCase):
    """D-035: title weight, reading notes, implication callouts and resistance mapping."""
    RUN = ROOT / '50_evals/runs/bench_vi_briefing_no_ask'

    def deck(self):
        from pptx import Presentation
        return Presentation(str(self.RUN / 'output/presentation.pptx'))

    def test_title_spans_keep_title_weight(self):
        for slide in content_slides(self.deck()):
            title = next(sh for sh in slide.shapes if sh.name == 'pai:takeaway_title')
            weights = {r.font.bold for p in title.text_frame.paragraphs for r in p.runs if r.text.strip()}
            self.assertEqual(weights, {True})

    def test_html_span_inherits_weight(self):
        html = html_renderer.apply_color_tie_html('Costs rose fast', [{'substring': 'rose', 'color_hex': '#123456'}])
        self.assertIn('font-weight:inherit', html)
        html = html_renderer.apply_color_tie_html('Costs rose fast', [{'substring': 'rose', 'color_hex': '#123456', 'bold': False}])
        self.assertIn('font-weight:400', html)

    def test_reading_note_sits_quietly_above_source(self):
        for slide in content_slides(self.deck()):
            shapes = {sh.name: sh for sh in slide.shapes}
            note = shapes.get('pai:reading_note')
            if note is None:
                continue
            source = shapes['pai:source_footnote']
            self.assertTrue(note.text_frame.text.startswith('Lưu ý: '))
            self.assertLessEqual(note.top + note.height, source.top)
            self.assertEqual(note.text_frame.paragraphs[0].font.size, source.text_frame.paragraphs[0].font.size)
            self.assertIn(note.fill.type, (None, MSO_FILL.BACKGROUND))  # unfilled text box
            for sh in slide.shapes:
                if sh.has_chart or sh.name in ('pai:callout', 'pai:annotation'):
                    self.assertLessEqual(sh.top + sh.height, note.top, sh.name)

    def test_implication_callout_is_neutral(self):
        slide = content_slides(self.deck())[1]
        card = next(sh for sh in slide.shapes if sh.name == 'pai:callout')
        self.assertEqual(card.text_frame.paragraphs[0].text, 'Ý nghĩa')
        self.assertEqual(str(card.fill.fore_color.rgb), 'F3F4F6')  # annotation grey, not the accent tint

    def test_html_statement_hero_uses_implication_label(self):
        text = (self.RUN / 'output/presentation.html').read_text(encoding='utf-8')
        self.assertNotIn('Quyết định cần phê duyệt hôm nay', text)
        for css in ('1px solid #D1D5DB', '1.5px solid var(--accent)', '2px solid var(--accent)'):
            self.assertNotIn(css, text)  # cards: fill only, no outline (ANTI-DSN-002)

    def test_html_type_follows_delivery_mode_and_notes_start_hidden(self):
        """B-8: slide-relative type at the PRIN-DSN-005 scale; presenter notes are not shown to the audience by default."""
        import re
        text = (self.RUN / 'output/presentation.html').read_text(encoding='utf-8')
        self.assertIn('container-type: inline-size', text)
        self.assertIn('font-size: calc(var(--pt) * 24);', text)       # hybrid deck: projected title size
        self.assertIn('id="speaker-notes" hidden', text)
        chart_pts = [float(v) for v in re.findall(r'data-pt="([0-9.]+)"', text)]
        self.assertTrue(chart_pts)
        self.assertGreaterEqual(min(chart_pts), 12.0)                  # label floor for projected decks
        self.assertNotIn('[:18]', (ROOT / '40_plugin/scripts/html_renderer.py').read_text(encoding='utf-8'))

    def test_note_like_callout_warns(self):
        spec = yaml.safe_load((self.RUN / 'artifacts/slide_spec.yaml').read_text(encoding='utf-8'))
        spec['slides'][1]['word_jobs']['recommendation_callout']['text'] = 'Lưu ý: các tỷ lệ không cộng thành 100%.'
        res = validate_spec.validate_slide_spec_dict(spec, 'mutated')
        self.assertTrue(any('reads as a reading note' in w for w in res['warnings']))

    def test_resistance_assessment_needs_reason(self):
        text = (self.RUN / 'artifacts/context_brief.md').read_text(encoding='utf-8')
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'context_brief.md'
            p.write_text(text, encoding='utf-8')
            self.assertFalse([e for e in validate_spec.validate_context_brief(p)['errors'] if 'G1.2' in e])
            p.write_text(text.replace('resistance_reason:', 'old_reason:'), encoding='utf-8')
            self.assertTrue([e for e in validate_spec.validate_context_brief(p)['errors'] if 'resistance_reason' in e])

class MilestoneARegressions(unittest.TestCase):
    """P7-A4 pilot findings: percentage-point axes, first-render cycle, statement layout."""
    RUN = ROOT / '50_evals/runs/bench_vi_briefing_no_ask'

    def test_percent_points_format_quotes_once(self):
        import pptx_renderer
        self.assertEqual(pptx_renderer.percent_points_format('0%', 60), '0"%"')
        self.assertEqual(pptx_renderer.percent_points_format('0"%"', 60), '0"%"')  # pilot case: was 0""%"" -> 100x labels
        self.assertEqual(pptx_renderer.percent_points_format('0%', 1.0), '0%')    # true fractions keep Excel's percent

    def spec(self):
        return yaml.safe_load((self.RUN / 'artifacts/slide_spec.yaml').read_text(encoding='utf-8'))

    def unrendered(self, spec):
        for s in spec['slides']:
            q = s['claim_evidence_contract']['rendered_png_qa']
            q['zero_text_overlap_or_clipping'] = q['compound_word_linebreak_safe'] = False
        return spec

    def test_first_render_allows_uninspected_flags(self):
        spec = self.unrendered(self.spec())
        spec['g4_review_audit']['status'] = 'pending'
        res = validate_spec.validate_slide_spec_dict(spec, 'pre-render', self.RUN)
        self.assertEqual(res['errors'], [])

    def test_completed_review_requires_inspected_flags(self):
        spec = self.unrendered(self.spec())
        res = validate_spec.validate_slide_spec_dict(spec, 'reviewed', self.RUN)
        self.assertTrue(any('render inspection flags' in e for e in res['errors']))

    def test_statement_content_does_not_hug_the_top(self):
        from pptx import Presentation

        def gaps(run):
            slide = next(sl for sl in Presentation(str(ROOT / '50_evals/runs' / run / 'output/presentation.pptx')).slides
                         if any(sh.name == 'pai:statement_hero' for sh in sl.shapes))  # the closing slide, before the appendix
            hero = next(sh for sh in slide.shapes if sh.name == 'pai:statement_hero')
            steps = [sh for sh in slide.shapes if sh.name == 'pai:step']
            return hero.top / 914400 - 1.4, 6.75 - max(sh.top + sh.height for sh in steps) / 914400

        top_gap, bottom_gap = gaps('bench_vi_bep_giao_do_an')  # short step cards: the block sits one third down
        self.assertGreater(top_gap, 0.2)
        self.assertGreater(bottom_gap, top_gap)  # more air below than above
        top_gap, bottom_gap = gaps('bench_vi_briefing_no_ask')  # D-064 tiles fill the body: clear of the header and the source
        self.assertGreater(top_gap, 0.2)
        self.assertGreater(bottom_gap, 0.2)

    def test_powerpoint_reads_label_format_and_size(self):
        """PowerPoint ignores paragraph-level label formatting and wraps labels at its own width (P7-B1 finding)."""
        import zipfile
        c = '{http://schemas.openxmlformats.org/drawingml/2006/chart}'
        a = '{http://schemas.openxmlformats.org/drawingml/2006/main}'
        deck = ROOT / '50_evals/runs/bench_en_nurse_staffing/output/presentation.pptx'
        with zipfile.ZipFile(deck) as z:
            charts = [ET.fromstring(z.read(n)) for n in z.namelist() if n.startswith('ppt/charts/chart')]
            slides = [z.read(n).decode('utf-8') for n in z.namelist() if n.startswith('ppt/slides/slide')]
        labels = [d for ch in charts for d in ch.iter(c + 'dLbl') if list(d.iter(a + 't'))]
        self.assertTrue(labels)
        for d in labels:
            for r in d.iter(a + 'r'):
                self.assertIsNotNone(r.find(f'{a}rPr/{a}solidFill'))
            self.assertIn('CE6537A1-D6FC-4f65-9D91-7224C49458BB', ET.tostring(d, encoding='unicode'))
        self.assertFalse(any('<p:cxnSp' in s and '<p:style>' in s.split('<p:cxnSp', 1)[1].split('</p:cxnSp>', 1)[0] for s in slides))

class CoffeeWorkspace:
    """A temporary copy of the coffee benchmark with brief and spec helpers (D-040, D-043 tests)."""
    RUN = ROOT / '50_evals/runs/bench_en_coffee_two_tier'

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='pai_d040_')
        self.addCleanup(self.tmp.cleanup)
        self.work = Path(self.tmp.name) / 'ws'
        shutil.copytree(self.RUN, self.work)
        self.output = contextlib.redirect_stdout(io.StringIO())
        self.output.__enter__()
        self.addCleanup(self.output.__exit__, None, None, None)

    def spec(self):
        return yaml.safe_load((self.work / 'artifacts/slide_spec.yaml').read_text(encoding='utf-8'))

    def set_brief(self, **fields):
        path = self.work / 'artifacts/context_brief.md'
        fm, body, _ = validate_spec.parse_markdown_frontmatter(path)
        fm.update(fields)
        fm['status'] = 'draft'
        fm.pop('approvals', None)
        path.write_text('---\n' + yaml.safe_dump(fm, allow_unicode=True, sort_keys=False) + '---' + body, encoding='utf-8')

    def stars_table(self):
        (self.work / 'inputs/model.csv').write_text('term,m1\nrenter,"0.06"\nincome_q1,"1.022***"\nowner,"-0.36**"\n', encoding='utf-8')

class AntigravityRemediation(CoffeeWorkspace, unittest.TestCase):
    """D-040: fixes P1–P8 from the Antigravity test on ANU Poll 58."""

    def test_p1_negative_bars_keep_their_colour_in_powerpoint(self):
        import pptx_qa
        from pptx_renderer import compile_pptx
        out = compile_pptx(self.spec(), self.work / 'out.pptx')
        from pptx import Presentation
        charts = [sh.chart._chartSpace for s in Presentation(str(out)).slides for sh in s.shapes if getattr(sh, 'has_chart', False)]
        self.assertTrue(any(ch.findall('.//c:barChart', pptx_qa.NS) for ch in charts))
        self.assertEqual(sum(pptx_qa.inverted_negative_bars(ch) for ch in charts), 0)
        self.assertGreater(pptx_qa.inverted_negative_bars(ET.fromstring(
            '<c:chartSpace xmlns:c="http://schemas.openxmlformats.org/drawingml/2006/chart"><c:barChart><c:ser><c:idx val="0"/>'
            '<c:val><c:numRef><c:numCache><c:pt idx="0"><c:v>-0.4</c:v></c:pt></c:numCache></c:numRef></c:val></c:ser></c:barChart></c:chartSpace>')), 0)

    def test_p2_g2_stamp_survives_the_g3_section(self):
        path = self.work / 'artifacts/storyline.md'
        fm, body, _ = validate_spec.parse_markdown_frontmatter(path)
        fm['checkpoint_g3_status'] = 'pending'
        fm.pop('approvals', None)
        path.write_text('---\n' + yaml.safe_dump(fm, allow_unicode=True, sort_keys=False) + '---' + body, encoding='utf-8')
        validate_spec.stamp_approval(path, 'G2', 'Owner')
        text = path.read_text(encoding='utf-8')
        path.write_text(text.replace('## 6. `CHK-REV-001`', 'Extra G3 row written after G2.\n\n## 6. `CHK-REV-001`'), encoding='utf-8')
        self.assertFalse([e for e in validate_spec.validate_storyline(path)['errors'] if 'hash mismatch' in e])
        path.write_text(path.read_text(encoding='utf-8').replace('## 1. Analyst-Process', 'Edited G2 text.\n\n## 1. Analyst-Process'), encoding='utf-8')
        self.assertTrue([e for e in validate_spec.validate_storyline(path)['errors'] if 'hash mismatch' in e])

    def test_p2_inputs_prefix_and_missing_source_input(self):
        resolver = validate_spec.SourceResolver(self.work / 'inputs')
        self.assertEqual(resolver.check('inputs/menu_yoy.csv!R2C3', 15, '', None)[0], 'ok')
        self.set_brief(source_inputs=[{'path': 'inputs/missing.csv', 'type': 'dataset', 'verified': True}])
        res = validate_spec.validate_context_brief(self.work / 'artifacts/context_brief.md')
        self.assertTrue(any('missing.csv' in e for e in res['errors']))

    def test_p2_g4_10_pending_only_while_review_pending(self):
        spec = self.spec()
        spec['g4_review_audit']['checklist_results']['G4_10_rendered_png_geometry_inspection'] = 'pending'
        spec['g4_review_audit']['status'] = 'pending'
        self.assertFalse([e for e in validate_spec.validate_slide_spec_dict(spec, 't', self.work)['errors'] if 'G4_10' in e or 'G4.10' in e])
        spec['g4_review_audit']['status'] = 'agent_review_complete'
        self.assertTrue([e for e in validate_spec.validate_slide_spec_dict(spec, 't', self.work)['errors'] if 'G4_10' in e])

    def test_p3_unknown_key_is_named(self):
        spec = self.spec()
        spec['slides'][0]['word_jobs']['callout_box'] = {'box_text': 'x'}
        warns = validate_spec.validate_slide_spec_dict(spec, 't', self.work)['warnings']
        self.assertTrue(any('callout_box' in w and 'annotations' in w for w in warns))

    def test_p4_dot_whisker_with_traced_intervals(self):
        from pptx_renderer import compile_pptx
        spec = self.spec()
        panel = next(p for s in spec['slides'] for p in (s.get('visual_spec') or {}).get('panels', []) if p['chart_family'] == 'horizontal_bar_chart')
        panel.update(chart_family='dot_whisker_chart', metric_kind='model_estimate')
        lo, hi = panel['y_axis']['min'], panel['y_axis']['max']
        for dp in panel['series'][0]['data_points']:
            dp['ci_low'], dp['ci_high'] = max(dp['value'] - 1, lo), min(dp['value'] + 1, hi)
        errs = validate_spec.validate_slide_spec_dict(spec, 't', self.work)['errors']
        self.assertFalse([e for e in errs if 'interval' in e or 'dot_whisker' in e], errs)
        out = compile_pptx(spec, self.work / 'dw.pptx')
        import zipfile
        with zipfile.ZipFile(out) as z:
            self.assertTrue(any(b'<c:errBars>' in z.read(n) for n in z.namelist() if n.startswith('ppt/charts/')))
        self.assertIn('ci-whisker', html_renderer.render_svg_chart_panel(panel, {}, {}))
        panel['series'][0]['data_points'][0]['ci_low'] = panel['series'][0]['data_points'][0]['value'] + 0.5
        self.assertTrue(any('does not contain' in e for e in validate_spec.validate_slide_spec_dict(spec, 't', self.work)['errors']))
        for dp in panel['series'][0]['data_points']:
            dp.pop('ci_low'); dp.pop('ci_high')
        self.assertTrue(any('dot_whisker_chart' in e for e in validate_spec.validate_slide_spec_dict(spec, 't', self.work)['errors']))

    def test_p5_causal_wording_warns_for_observational_designs(self):
        spec = self.spec()
        spec['slides'][0]['word_jobs']['takeaway_title']['text'] = 'Staff shortages drive the sales decline this year.'
        spec['slides'][0]['word_jobs']['takeaway_title']['color_tie_spans'] = []
        self.assertFalse([w for w in validate_spec.validate_slide_spec_dict(spec, 't', self.work)['warnings'] if 'causal' in w])
        self.set_brief(study_design='observational_cross_section', analysed_population='Cafe staff, 2025')
        warns = validate_spec.validate_slide_spec_dict(spec, 't', self.work)['warnings']
        self.assertTrue(any("causal wording 'drive'" in w for w in warns))
        self.assertTrue(any('record `population`' in w for w in warns))

    def test_p6_evidence_ledger_checks_null_results_and_stars(self):
        self.stars_table()
        self.set_brief(study_design='observational_cross_section', analysed_population='Adults')
        path = self.work / 'artifacts/storyline.md'
        fm, body, _ = validate_spec.parse_markdown_frontmatter(path)
        fm['checkpoint_g2_status'] = fm['checkpoint_g3_status'] = 'pending'
        fm.pop('approvals', None)
        fm['evidence_ledger'] = [
            {'question': 'RQ1', 'variable': 'renter', 'direction': 'none', 'significance': 'not_significant', 'source_cell_ref': 'model.csv!R2C2'},
            {'question': 'RQ1', 'variable': 'income', 'direction': 'negative', 'significance': 'significant', 'source_cell_ref': 'model.csv!R3C2', 'reported_on': [1]},
            {'question': 'RQ2', 'variable': 'owner', 'direction': 'negative', 'significance': 'significant', 'source_cell_ref': 'model.csv!R4C2', 'reported_on': [2]},
        ]
        path.write_text('---\n' + yaml.safe_dump(fm, allow_unicode=True, sort_keys=False) + '---' + body, encoding='utf-8')
        errs = validate_spec.validate_storyline(path)['errors']
        self.assertTrue(any("'renter'" in e and 'null result' in e for e in errs))
        self.assertTrue(any("'income'" in e and 'direction' in e for e in errs))
        self.assertFalse(any("'owner'" in e for e in errs))

    def test_p7_shared_understanding_needs_no_ask(self):
        self.set_brief(action_contract={'objective': 'shared_understanding'})
        errs = validate_spec.validate_context_brief(self.work / 'artifacts/context_brief.md')['errors']
        self.assertFalse([e for e in errs if 'G1.3' in e])
        self.set_brief(action_contract={'objective': 'decision'})
        errs = validate_spec.validate_context_brief(self.work / 'artifacts/context_brief.md')['errors']
        self.assertTrue([e for e in errs if 'primary_action' in e])


class Run2Remediation(CoffeeWorkspace, unittest.TestCase):
    """D-043: fixes Q1–Q5 from the second ANU Poll 58 run."""

    def warns(self, spec):
        return validate_spec.validate_slide_spec_dict(spec, 't', self.work)['warnings']

    def set_storyline(self, **fields):
        path = self.work / 'artifacts/storyline.md'
        fm, body, _ = validate_spec.parse_markdown_frontmatter(path)
        fm.update(fields)
        path.write_text('---\n' + yaml.safe_dump(fm, allow_unicode=True, sort_keys=False) + '---' + body, encoding='utf-8')

    def estimate_panel(self, spec):
        panel = spec['slides'][1]['visual_spec']['panels'][0]
        panel['metric_kind'] = 'model_estimate'
        return panel

    def test_q1_stated_quantities_parse_shares_not_ordinals(self):
        q = validate_spec.stated_quantities
        self.assertEqual([v for _, v, _ in q('Stress affects two-fifths of renters.', 'en')], [40.0])
        self.assertEqual([v for _, v, _ in q('Nearly three in ten mortgagors fell behind.', 'en')], [30.0])
        self.assertEqual(q('Sales rose for a third consecutive year in the first half of 2024.', 'en'), [])
        self.assertEqual(q('Renter estimate, 95% CI [-0.35, 0.33].', 'en'), [])
        self.assertEqual([v for _, v, _ in q('Gần một phần ba hộ gặp khó khăn.', 'vi')], [100 / 3])
        self.assertIsNotNone(validate_spec.quantity_mismatch('two-fifths', 40.0, 'share', [71.4, 28.6], []))
        self.assertIsNone(validate_spec.quantity_mismatch('three in ten', 30.0, 'share', [71.4, 28.6], []))

    def test_q1_title_quantity_warns_against_the_chart(self):
        spec = self.spec()
        spec['slides'][1]['word_jobs']['annotations'][0]['text'] = 'Mint Chill lost two-fifths of its sales.'
        spec['slides'][1]['word_jobs']['annotations'][0]['color_tie_spans'] = []
        self.assertTrue(any("'two-fifths of'" in w and 'slide_02' in w for w in self.warns(spec)))
        self.assertFalse([w for w in self.warns(self.spec()) if 'D-043' in w and 'states about' in w])
        self.set_brief(study_design='descriptive', analysed_population='Cafe customers, 2025')
        spec = self.spec()
        spec['slides'][1]['word_jobs']['takeaway_title']['text'] = 'Mint Chill sales fell 18% while Hazelnut Cloud fell 14%.'
        spec['slides'][1]['word_jobs']['takeaway_title']['color_tie_spans'] = []
        spec['g4_review_audit']['status'] = 'agent_review_complete'
        spec['g4_review_audit']['source_reread'] = [{'slide_number': 2, 'title_claim': 'x', 'source_checked': 'menu_yoy.csv', 'sign_ok': True, 'significance_ok': True, 'population_ok': True}]
        self.assertTrue(any('title_quantity' in w for w in self.warns(spec)))
        spec['g4_review_audit']['source_reread'][0]['title_quantity'] = '18% vs -18 plotted: pass'
        self.assertFalse(any('title_quantity' in w for w in self.warns(spec)))

    def test_q2_ledger_covers_plotted_estimates_and_appendix_is_kept(self):
        spec = self.spec()
        self.estimate_panel(spec)
        self.set_storyline(evidence_ledger=[{'question': 'RQ1', 'variable': 'Espresso Tonic', 'direction': 'positive', 'significance': 'not_tested', 'source_cell_ref': 'menu_yoy.csv!R2C3', 'reported_on': [2]}])
        warns = [w for w in self.warns(spec) if 'evidence_ledger' in w and 'slide_02' in w]
        self.assertTrue(warns and 'Iced Matcha' in warns[0] and 'Espresso Tonic' not in warns[0])
        self.set_storyline(pruned_analyst_artifacts=[{'item': 'Cost sheet', 'disposition': 'moved_to_appendix', 'reason': 'r', 'audience_need': 'n'}])
        no_appendix = self.spec()
        no_appendix.pop('appendix_slides', None)  # the coffee benchmark carries an appendix table (D-055)
        self.assertTrue(any('appendix' in w and 'Cost sheet' in w for w in self.warns(no_appendix)))

    def test_q3_intervals_in_source_and_mixed_units(self):
        (self.work / 'inputs/est.csv').write_text('term,coef,ci_low,ci_high\nrenter,0.62,0.32,0.93\ntrust_std,0.28,0.15,0.41\n', encoding='utf-8')
        (self.work / 'inputs/tab.csv').write_text('term,m1\nrenter,"0.625***"\n,"(0.155)"\n', encoding='utf-8')
        r = validate_spec.SourceResolver(self.work / 'inputs')
        self.assertIn('ci_low', validate_spec.source_interval_hint(r, 'est.csv!R2C2'))
        self.assertIn('standard errors', validate_spec.source_interval_hint(r, 'tab.csv!R2C2'))
        self.assertIsNone(validate_spec.source_interval_hint(r, 'menu_yoy.csv!R2C3'))
        panel = {'panel_id': 'p', 'chart_family': 'horizontal_bar_chart', 'metric_kind': 'model_estimate', 'uncertainty_omitted_reason': 'Bars show magnitudes.',
                 'series': [{'series_name': 's', 'data_points': [{'category': 'Renter', 'value': 0.62, 'source_cell_ref': 'est.csv!R2C2'},
                                                                  {'category': 'Political trust', 'value': 0.28, 'source_cell_ref': 'est.csv!R3C2'}]}]}
        _, warns = validate_spec.research_panel_issues('s1', {'visual_spec': {'panels': [panel]}}, r, True)
        self.assertTrue(any('source holds the intervals' in w for w in warns))
        self.assertTrue(any('mixes units' in w for w in warns))
        panel['series'][0]['data_points'] = panel['series'][0]['data_points'][:1]
        _, warns = validate_spec.research_panel_issues('s1', {'visual_spec': {'panels': [panel]}}, r, True)
        self.assertFalse(any('mixes units' in w for w in warns))

    def test_q3_log_odds_while_margins_exist(self):
        spec = self.spec()
        self.estimate_panel(spec)
        spec['slides'][1]['word_jobs']['chart_title'] = 'Log-odds of a sales decline by drink'
        self.assertFalse(any('log-odds/logit' in w for w in self.warns(spec)))
        (self.work / 'inputs/RQ1_margins.csv').write_text('x\n1\n', encoding='utf-8')
        self.assertTrue(any('log-odds/logit' in w and 'RQ1_margins.csv' in w for w in self.warns(spec)))
        spec['slides'][1]['visual_spec']['panels'][0]['estimate_scale_reason'] = 'Assessors asked for coefficients.'
        self.assertFalse(any('log-odds/logit' in w for w in self.warns(spec)))

    def test_q4_effect_oppose_and_prescriptive_wording(self):
        self.set_brief(study_design='observational_cross_section', analysed_population='Cafe customers', action_contract={'objective': 'shared_understanding'})
        spec = self.spec()
        self.estimate_panel(spec)
        wj = spec['slides'][1]['word_jobs']
        spec['slides'][1]['visual_spec']['panels'][0]['panel_chart_title'] = 'Menu effect on sales'
        wj['annotations'][0].update(text='Mint Chill buyers oppose the change (-0.36).', color_tie_spans=[])
        wj['recommendation_callout'].update(text='The menu team must replace Mint Chill.', kind='implication', color_tie_spans=[])
        warns = self.warns(spec)
        self.assertTrue(any("'effect' reads as causal" in w for w in warns))
        self.assertTrue(any("'oppose'" in w for w in warns))
        self.assertTrue(any("prescriptive 'must'" in w for w in warns))
        spec['slides'][1]['visual_spec']['panels'][0]['panel_chart_title'] = 'Average marginal effects on sales'
        self.assertFalse(any("reads as causal" in w and 'panel_chart_title' in w for w in self.warns(spec)))
        self.assertFalse(validate_spec.PRESCRIPTIVE_RE['vi'].search('Vì chi phí tăng nên doanh thu giảm; nhãn nằm bên phải.'))

    def test_q5_negative_bar_label_gets_room_and_dot_whisker_labels_all(self):
        from pptx_renderer import compile_pptx
        import zipfile
        spec = self.spec()
        out = compile_pptx(spec, self.work / 'b10.pptx')
        with zipfile.ZipFile(out) as z:
            mins = [float(m) for n in z.namelist() if n.startswith('ppt/charts/chart') for m in __import__('re').findall(r'<c:min val="([-\d.]+)"', z.read(n).decode('utf-8'))]
        self.assertTrue(any(m < -20 for m in mins), mins)  # slide 2: -18% bar on a [-20, 20] axis gets room for its label
        # HTML: the "-18%" label (anchored at its right end) starts inside the plot, clear of the category labels
        svg = html_renderer.render_svg_chart_panel(spec['slides'][1]['visual_spec']['panels'][0], spec['slides'][1], spec['deck_meta'])
        import re as _re
        cat_x = float(_re.search(r'<text x="([\d.]+)"[^>]*text-anchor="end"[^>]*>Mint Chill Cold Brew<', svg).group(1))
        lbl_x = float(_re.search(r'<text x="([\d.]+)"[^>]*text-anchor="end"[^>]*>-18%<', svg).group(1))
        self.assertGreater(lbl_x - 4 * 9, cat_x + 10)  # label width ~4 characters
        css = html_renderer.compile_html(spec, self.work / 'deck.html').read_text(encoding='utf-8')
        self.assertIn('.layout-two_sided_paired_views .panels-count-2 + .side-zone > div', css)
        panel = self.estimate_panel(spec)
        panel['chart_family'] = 'dot_whisker_chart'
        for dp in panel['series'][0]['data_points']:
            dp['ci_low'], dp['ci_high'] = dp['value'] - 1, dp['value'] + 1
        panel['series'][0]['direct_label_placement'] = 'right_endpoint'
        self.assertTrue(any('bar_end' in w and 'dot-whisker' in w for w in self.warns(spec)))


def estimate_slide(s_id, title, panels, note='', population='adults'):
    return {'slide_id': s_id, 'word_jobs': {'takeaway_title': {'text': title}, 'reading_note': note},
            'claim_evidence_contract': {'population': population}, 'visual_spec': {'panels': panels}}


def estimate_panel(p_id, title, points, family='horizontal_bar_chart', role='context_greyscale', **extra):
    return dict({'panel_id': p_id, 'panel_chart_title': title, 'chart_family': family, 'metric_kind': 'model_estimate',
                 'series': [{'series_name': 'Estimate', 'visual_role': role, 'data_points': points}]}, **extra)


class Run3Remediation(CoffeeWorkspace, unittest.TestCase):
    """D-046: fixes Z1–Z6 from the third ANU Poll 58 run."""

    def scope(self, slides):
        return validate_spec.claim_scope_issues(slides, None, 'en')

    def test_z4_frontmatter_ends_only_on_a_whole_line(self):
        path = self.work / 'artifacts/fm.md'
        path.write_text('---\na: 1\n# --- RQ1 ---\nb: 2\n---\nbody --- text\n', encoding='utf-8')
        fm, body, errs = validate_spec.parse_markdown_frontmatter(path)
        self.assertEqual((fm, errs), ({'a': 1, 'b': 2}, []))
        self.assertIn('body --- text', body)
        old = '---\nx: 1\n---\nbody\n'
        self.assertEqual(validate_spec.split_frontmatter(old), old.split('---', 2))

    def test_z1_absence_claim_over_borderline_estimate(self):
        point = {'category': 'Renter · Greens − Coalition · +12.5', 'value': 12.5, 'ci_low': -0.88, 'ci_high': 25.93}
        slide = estimate_slide('s9', 'Party divides only owners and mortgagors.', [estimate_panel('p', 'Party gap', [point])])
        self.assertTrue(any("'only' claims an absence" in w for w in self.scope([slide])))
        point.update(ci_low=-10.0)
        self.assertFalse(any('claims an absence' in w for w in self.scope([slide])))
        point.update(ci_low=-0.88)
        slide['word_jobs']['takeaway_title']['text'] = 'The renter gap is not significant at 5%.'
        self.assertFalse(any('claims an absence' in w for w in self.scope([slide])))
        (self.work / 'inputs/gaps.csv').write_text('contrast,diff,p\nG-C,12.5,0.067\nG-L,8.6,0.16\n', encoding='utf-8')
        r = validate_spec.SourceResolver(self.work / 'inputs')
        self.assertEqual(validate_spec.borderline_null({'source_cell_ref': 'gaps.csv!R2C2'}, r), 'p = 0.067')
        self.assertIsNone(validate_spec.borderline_null({'source_cell_ref': 'gaps.csv!R3C2'}, r))

    def test_z1_gap_contradicted_by_another_slides_levels(self):
        levels = [estimate_panel(f'p{party}', party, [{'category': f'Renter · {v}%', 'value': v}], family='vertical_bar_chart')
                  for party, v in (('Coalition', 48.4), ('Greens', 74.2))]
        other = [estimate_panel('q', 'Coalition', [{'category': 'Renter · 67.7%', 'value': 67.7}], family='vertical_bar_chart')]
        gap = {'category': 'Renter · Greens − Coalition · +12.5', 'value': 12.5}
        diff = estimate_slide('s9', 'Gaps', [estimate_panel('g', 'Party gap within each tenure', [gap])])
        slides = [estimate_slide('s7', 'Build', other, population='rq2a sample'), estimate_slide('s8', 'Levels', levels), diff]
        self.assertTrue(any('imply 25.8' in w and 's8' in w for w in self.scope(slides)))
        gap['value'] = 25.0
        self.assertFalse(any('imply' in w for w in self.scope(slides)))
        gap['value'] = 12.5
        diff['visual_spec']['panels'][0]['estimand'] = 'cell contrasts at average covariates'
        diff['word_jobs']['reading_note'] = 'Gaps are cell contrasts at average covariates, not the observed-group levels of slide 8.'
        self.assertFalse(any('imply' in w for w in self.scope(slides)))

    def test_z2_title_span_and_superlative(self):
        pts = [{'category': 'Renter Q1', 'value': 57.4, 'ci_low': 50.5, 'ci_high': 64.3}, {'category': 'Renter Q2', 'value': 55.1, 'ci_low': 48.0, 'ci_high': 62.0}]
        slide = estimate_slide('s5', 'Lowest-income renters face the highest risk.', [estimate_panel('p', 'Risk by profile', pts, role='focal_primary_tier1')])
        slide['word_jobs']['takeaway_title']['color_tie_spans'] = [{'substring': 'the poorest', 'linked_series_or_category': 'Income Q1 annotation'}]
        warns = self.scope([slide])
        self.assertTrue(any("'highest' ranks Renter Q1" in w for w in warns))
        self.assertTrue(any("'the poorest' is tied to 'Income Q1 annotation'" in w for w in warns))
        pts[1].update(ci_high=49.0)
        slide['word_jobs']['takeaway_title']['color_tie_spans'] = [{'substring': 'renters', 'linked_series_or_category': 'Renter bars'}]
        self.assertEqual(self.scope([slide]), [])

    def test_z3_unlabelled_bar_series_and_stacked_intervals(self):
        panel = estimate_panel('p', 'RQ1', [{'category': 'Renter', 'value': 0.1}])
        panel['series'].append({'series_name': 'Unweighted', 'visual_role': 'context_greyscale', 'data_points': [{'category': 'Renter', 'value': 0.2}]})
        slide = estimate_slide('s11', 'Signs hold.', [panel])
        self.assertTrue(any("tie ['Estimate', 'Unweighted']" in w for w in self.scope([slide])))
        slide['word_jobs']['takeaway_title']['color_tie_spans'] = [{'substring': 'a', 'linked_series_or_category': 'Estimate'}, {'substring': 'b', 'linked_series_or_category': 'Unweighted bars'}]
        self.assertFalse(any('no legend' in w for w in self.scope([slide])))
        stack = {'panel_id': 's', 'chart_family': 'stacked_bar_chart', 'series': [
            {'series_name': n, 'data_points': [{'category': 'All', 'value': v, 'ci_low': v - 2, 'ci_high': v + 2}]} for n, v in (('Stress', 28.6), ('No stress', 71.4))]}
        self.assertTrue(any('several stacked segments' in w for w in self.scope([estimate_slide('s2', 'x', [stack])])))

    def test_z3_renderer_threshold_colours_labels_and_axis_title(self):
        from pptx_renderer import compile_pptx, wrap_words_into_lines, RENDER_WARNINGS
        from pptx import Presentation
        spec = self.spec()
        panel = spec['slides'][1]['visual_spec']['panels'][0]
        panel['threshold_lines'] = [{'value': 0, 'label': 'No change'}]
        dps = panel['series'][0]['data_points']
        dps[0].pop('point_color_override_hex', None)
        dps[0]['point_visual_role_override'] = 'focal_primary_tier1'
        dps[1].update(ci_low=dps[1]['value'] - 3, ci_high=dps[1]['value'] + 3)
        panel['series'][0]['direct_label_placement'] = 'bar_end'
        prs = Presentation(compile_pptx(spec, self.work / 'z3.pptx'))
        shapes = list(content_slides(prs)[1].shapes)
        conn = [s for s in shapes if s.__class__.__name__ == 'Connector']
        self.assertTrue(any(c.begin_x == c.end_x and c.end_y > c.begin_y for c in conn))  # vertical threshold on horizontal bars
        chart = next(s for s in shapes if s.has_chart).chart
        accent = spec['deck_meta']['theme_palette']['two_tier_accent']['primary_focal_hex'].lstrip('#').upper()
        self.assertEqual(str(chart.plots[0].series[0].points[0].format.fill.fore_color.rgb), accent)
        dlbl = chart.plots[0].series[0].points[1].data_label._dLbl
        self.assertTrue(dlbl is not None and dlbl.xpath('./c:layout/c:manualLayout/c:x'))  # label moved past the whisker
        self.assertEqual(wrap_words_into_lines('Predicted Pr(support) (%)', 2), 'Predicted\nPr(support) (%)')
        RENDER_WARNINGS.clear()
        spec = self.spec()
        spec['slides'][1]['visual_spec']['panels'][0]['chart_family'] = 'vertical_bar_chart'
        with patch('pptx_renderer.fit_category_labels', lambda cats, *a: ([c if i % 2 == 0 else '' for i, c in enumerate(cats)], 1)):
            compile_pptx(spec, self.work / 'z3b.pptx')
        self.assertTrue(any('are hidden' in w for w in RENDER_WARNINGS))

    def test_z5_methods_audience_and_evaluative_verdicts(self):
        self.set_brief(study_design='observational_cross_section', analysed_population='Cafe customers',
                       action_contract={'objective': 'shared_understanding'})
        path = self.work / 'artifacts/storyline.md'
        self.assertFalse(any('D-046' in w for w in validate_spec.validate_storyline(path)['warnings']))
        self.set_brief(audience_assesses_method=True)
        self.assertTrue(any('G2.1 [D-046]' in w and 'limitations' in w for w in validate_spec.validate_storyline(path)['warnings']))
        fm, body, _ = validate_spec.parse_markdown_frontmatter(path)
        fm['methods_omitted_reason'] = 'Method was assessed in the written report.'
        path.write_text('---\n' + yaml.safe_dump(fm, allow_unicode=True, sort_keys=False) + '---' + body, encoding='utf-8')
        self.assertFalse(any('D-046' in w for w in validate_spec.validate_storyline(path)['warnings']))
        spec = self.spec()
        spec['slides'][1]['word_jobs']['takeaway_title'].update(text='Sales track the menu — the debate misdirects.', color_tie_spans=[])
        warns = validate_spec.validate_slide_spec_dict(spec, 't', self.work)['warnings']
        self.assertTrue(any("'misdirects' judges" in w for w in warns))

    def test_html_bars_series_whiskers_axis_titles_and_labels(self):
        import re as _re
        spec = self.spec()
        slide = spec['slides'][1]
        panel = slide['visual_spec']['panels'][0]
        dps = panel['series'][0]['data_points']
        dps[0].update(ci_low=dps[0]['value'] - 3, ci_high=dps[0]['value'] + 3)
        panel['series'].append({'series_name': 'Last year', 'visual_role': 'context_greyscale', 'color_hex': '#9E9E9E',
                                'data_points': [dict(dp, value=dp['value'] / 2, formatted_label='LY') for dp in dps[:2]]})
        svg = html_renderer.render_svg_chart_panel(panel, slide, spec['deck_meta'])
        self.assertEqual(svg.count('>LY<'), 2)  # second series drawn
        self.assertIn('class="ci-whisker"', svg)
        line = {'chart_family': 'line_chart', 'x_axis': {'categories': ['A', 'B'], 'title': 'Year'}, 'y_axis': {'min': 0, 'max': 200, 'title': 'Staff'},
                'threshold_lines': [{'value': 100, 'label': 'Target staffing level'}],
                'series': [{'series_name': n, 'visual_role': 'context_greyscale', 'color_hex': '#9E9E9E', 'direct_label_placement': 'right_endpoint',
                            'data_points': [{'category': 'A', 'value': v}, {'category': 'B', 'value': v, 'formatted_label': f'{v} · {n}'}]}
                           for n, v in (('Managers', 138), ('Supervisors', 134))]}
        svg = html_renderer.render_svg_chart_panel(line, {}, {})
        self.assertIn('class="axis-title"', svg)
        ys = sorted(float(_re.search(r'y="([\d.]+)"', m.group(0)).group(1)) for m in _re.finditer(r'<text[^>]*>13[48] · \w+<', svg))
        self.assertGreater(ys[1] - ys[0], 12 * 1.15)  # endpoint labels no longer overlap
        self.assertIn("hashArgs.has('full')", html_renderer.compile_html(self.spec(), self.work / 'd.html').read_text(encoding='utf-8'))  # #slide=N&full

    def test_runtime_home_follows_installed_plugin_copy(self):
        home = Path(self.tmp.name) / 'custom_home'
        (home / 'venv').mkdir(parents=True)
        (home / 'plugin').mkdir()
        with patch.object(deckctl, 'PLUGIN_ROOT', home / 'plugin'), patch.dict('os.environ', {}, clear=False) as env:
            env.pop('DATA_STORY_SLIDE_DECK_HOME', None)
            self.assertEqual(deckctl.data_story_slide_deck_home(), home)

    def test_z6_zcode_target(self):
        home = Path(self.tmp.name) / 'home'
        self.assertEqual(installer.skill_dirs_for('zcode', 'user', None, home), [home / '.zcode' / 'skills'])
        self.assertEqual(installer.skill_dirs_for('zcode', 'project', home / 'p', home), [home / 'p' / '.agents' / 'skills'])
        self.assertIn('zcode', installer.TARGETS)


class ExplorableReviewRemediation(CoffeeWorkspace, unittest.TestCase):
    """D-048: X2 HTML counter and print view, X4 quantity check on notes."""

    def test_x2_counter_skips_appendix_and_print_view(self):
        import copy
        spec = self.spec()
        extra = copy.deepcopy(spec['slides'][0])
        extra['slide_id'] = 'appendix_01'
        spec['appendix_slides'] = [extra]
        page = html_renderer.compile_html(spec, self.work / 'd.html').read_text(encoding='utf-8')
        main = len(spec['slides'])
        # the HUD keeps the talk's count (D-048 X2); the footer prints the slide number (D-075)
        self.assertIn(f'data-counter="Slide 1 / {main}"', page)
        self.assertNotIn(f'/ {main + 1}"', page)
        self.assertIn('>Appendix 1<', page)
        self.assertIn('@media print', page)
        self.assertIn("addEventListener('beforeprint'", page)

    def test_x4_notes_and_reading_note_quantities(self):
        spec = self.spec()
        slide = spec['slides'][1]
        slide['word_jobs']['reading_note'] = 'Two-fifths of orders include it.'
        slide['progressive_reveal'] = {'enabled': True, 'reveal_steps': [{'step_number': 1, 'speaker_notes': 'About two-fifths of orders include it.'}]}
        warns = validate_spec.validate_slide_spec_dict(spec, 't', self.work)['warnings']
        self.assertTrue(any('reading_note [G4.8 / G4.9 / D-043]' in w for w in warns))
        self.assertTrue(any('speaker_notes[0] [G4.8 / G4.9 / D-043]' in w for w in warns))
        # confidence levels and totals are not plotted shares (VCCI v2 pilot notes)
        self.assertEqual(validate_spec.stated_quantities('Khoảng tin cậy 95% không chồng lên nhau; không cộng thành 100%.', 'vi'), [])
        self.assertEqual(validate_spec.stated_quantities('A confidence level of 95%; shares do not add up to 100%.', 'en'), [])

    def test_x1_html_qa_reports_overflow(self):
        import html_qa
        with patch.dict('os.environ', {'DATA_STORY_SLIDE_DECK_BROWSER': str(self.work / 'none.exe')}),              patch.object(html_qa, 'BROWSER_CANDIDATES', []), patch.object(html_qa.shutil, 'which', return_value=None):
            with self.assertRaises(html_qa.BrowserUnavailable):
                html_qa.html_qa(self.work / 'd.html', self.work / 'qa')
        if not html_qa.find_browser():
            self.skipTest('no Edge, Chrome or Chromium on this computer')
        spec = self.spec()
        good = html_renderer.compile_html(spec, self.work / 'good.html')
        spec['slides'][1]['word_jobs']['annotations'] = [{'text': 'Mint Chill and Hazelnut Cloud lost the most sales in every region and quarter.'}] * 9
        bad = html_renderer.compile_html(spec, self.work / 'bad.html')
        report = html_qa.html_qa(good, self.work / 'qa_good')
        self.assertEqual(html_qa.findings(report), [])
        lead = 1 if pptx_renderer.has_title_slide(spec['deck_meta']) else 0  # D-075: the title slide is slide_00
        self.assertEqual(len(list((self.work / 'qa_good').glob('slide_*.png'))), lead + len(spec['slides']) + len(spec.get('appendix_slides') or []))
        issues = html_qa.findings(html_qa.html_qa(bad, self.work / 'qa_bad'))
        self.assertTrue(issues and all(i.startswith('HTML slide 02') for i in issues))

class SurveyChecks(CoffeeWorkspace, unittest.TestCase):
    """D-049: G1 placeholders, G2 duplicate titles, G3 untraced numbers, G5 ledger support, G6 accessibility."""

    def warns(self, spec):
        return validate_spec.validate_slide_spec_dict(spec, 't', self.work)['warnings']

    def test_g1_placeholder_text(self):
        spec = self.spec()
        spec['slides'][1]['word_jobs']['annotations'][0]['text'] = '<Annotation: what the reader should see>'
        self.assertTrue(any('placeholder text' in w and 'D-049' in w for w in self.warns(spec)))
        self.assertIsNone(validate_spec.PLACEHOLDER_RE.search('p < 0.05 and q > 1'))
        import pptx_qa
        spec['slides'][1]['word_jobs']['annotations'][0]['text'] = 'Margin: TBD'
        deck = pptx_renderer.compile_pptx(spec, self.work / 'p.pptx')
        self.assertTrue(any('TBD' in w for w in pptx_qa.placeholder_warnings(deck)))

    def test_g2_duplicate_titles(self):
        spec = self.spec()
        spec['slides'][2]['word_jobs']['takeaway_title']['text'] = spec['slides'][1]['word_jobs']['takeaway_title']['text']
        self.assertTrue(any('repeats' in w and 'D-049' in w for w in self.warns(spec)))

    def test_g3_untraced_numbers(self):
        spec = self.spec()
        self.assertFalse([w for w in self.warns(spec) if 'D-049' in w])
        spec['slides'][1]['word_jobs']['annotations'][0]['text'] = 'Mint Chill sold 4,730 cups in 37 stores.'
        hits = [w for w in self.warns(spec) if 'match no plotted value' in w]
        self.assertTrue(hits and '4,730' in hits[0] and '37' in hits[0])
        self.assertEqual(validate_spec.untraced_numbers('more than 2.5 times', 'en', [2.585], False), [])

    def test_g5_ledger_support(self):
        path = self.work / 'artifacts/storyline.md'
        fm, body, _ = validate_spec.parse_markdown_frontmatter(path)
        entry = {'question': 'RQ1', 'variable': 'Mint Chill', 'direction': 'negative', 'significance': 'not_tested',
                 'source_cell_ref': 'menu_yoy.csv!R2C2'}
        fm['evidence_ledger'] = [dict(entry, support='excluded', reported_on=[2]),
                                 dict(entry, variable='Hazelnut', support='conflicted', reported_on=[2]),
                                 dict(entry, variable='Cocoa', support='descriptive_only', reported_on=[2])]
        path.write_text('---\n' + yaml.safe_dump(fm, allow_unicode=True, sort_keys=False) + '---' + body, encoding='utf-8')
        spec = self.spec()
        spec.pop('appendix_slides', None)  # an appendix would answer the `conflicted` claim (D-049 G5)
        spec['slides'][1]['word_jobs'].pop('reading_note', None)
        spec['slides'][1]['word_jobs']['annotations'][0]['text'] = 'Cocoa Crunch fell because of the price rise.'
        warns = ' '.join(self.warns(spec))
        self.assertIn('an `excluded` claim is reported on main slide 2', warns)
        self.assertIn('a `conflicted` claim on slide 2 needs a `reading_note`', warns)
        self.assertIn('`descriptive_only` claim causally', warns)

    def test_g6_title_placeholder_alt_text_and_mixed_weight_mark(self):
        import pptx_qa
        from pptx import Presentation
        spec = self.spec()
        tt = spec['slides'][0]['word_jobs']['takeaway_title']
        tt['color_tie_spans'][0]['bold'] = False
        tt['mixed_weight_reason'] = 'test'
        deck = pptx_renderer.compile_pptx(spec, self.work / 'a.pptx')
        self.assertEqual(pptx_qa.accessibility_warnings(deck), [])
        slide = content_slides(deck)[0]
        self.assertEqual(slide.shapes.title.name, 'pai:takeaway_title~mixed_weight')
        self.assertFalse(slide.shapes.title._element.find('.//{*}cNvPr').get('descr'))  # no internal mark in alt text
        self.assertFalse(any('mixes bold' in i for i in pptx_qa.inspect_pptx_typography(deck, 'standalone')))

class TableSlide(CoffeeWorkspace, unittest.TestCase):
    """D-055 / PAT-VIS-006: the data_table layout in the contract, validator and three renderers."""

    def result(self, spec):
        return validate_spec.validate_slide_spec_dict(spec, 't', self.work)

    def table_slide(self, spec):
        return spec['appendix_slides'][0]

    def test_benchmark_table_is_clean(self):
        res = self.result(self.spec())
        self.assertEqual(res['errors'], [])
        self.assertFalse([w for w in res['warnings'] if 'D-055' in w or 'PAT-VIS-006' in w])

    def test_structure_and_traceability_errors(self):
        spec = self.spec()
        rows = self.table_slide(spec)['table_spec']['rows']
        rows[0]['cells']['short'].pop('source_cell_ref')
        rows[1]['cells']['wait']['value'] = 9.9
        rows[2]['cells']['nope'] = {'text': 'x'}
        errs = ' '.join(self.result(spec)['errors'])
        self.assertIn('Table cell is missing `source_cell_ref`', errs)
        self.assertIn('rows[r_union].wait [G4.9]', errs)
        self.assertIn("no column has `col_id` 'nope'", errs)
        spec = self.spec()
        spec['slides'][0]['table_spec'] = self.table_slide(spec)['table_spec']
        self.table_slide(spec).pop('table_spec')
        errs = ' '.join(self.result(spec)['errors'])
        self.assertIn('`table_spec` belongs only on `data_table` slides', errs)
        self.assertIn('layout `data_table` requires `table_spec`', errs)

    def test_live_size_emphasis_and_decimal_warnings(self):
        spec = self.spec()
        spec['deck_meta']['delivery_mode'] = 'live'
        table_slide = spec.pop('appendix_slides')[0]
        table_slide['arc_stage'] = 'falling_action'
        table = table_slide['table_spec']
        table.pop('focal')
        table['rows'][3]['cells']['wait']['formatted_label'] = '4.90'
        spec['slides'].append(table_slide)
        warns = ' '.join(self.result(spec)['warnings'])
        self.assertIn('a live audience reads a table instead of listening', warns)
        self.assertIn('decimal places', warns)
        spec = self.spec()
        rows = self.table_slide(spec)['table_spec']['rows']
        rows[0], rows[1] = rows[1], rows[0]
        self.assertIn('not in the stated order', ' '.join(self.result(spec)['warnings']))
        spec = self.spec()
        table = self.table_slide(spec)['table_spec']
        table['rows'] = table['rows'] + [dict(r, row_id=r['row_id'] + '_b') for r in table['rows']]
        self.assertIn('keep a slide table to', ' '.join(self.result(spec)['warnings']))
        self.assertEqual([w for w in self.result(self.spec())['warnings'] if 'live audience' in w], [])  # appendix is exempt

    def test_chart_in_disguise_and_table_numbers_count_as_shown(self):
        spec = self.spec()
        slide = self.table_slide(spec)
        slide['table_spec']['columns'] = slide['table_spec']['columns'][:1] + slide['table_spec']['columns'][3:]
        slide['table_spec']['column_groups'] = []
        for row in slide['table_spec']['rows'] + [slide['table_spec']['summary_row']]:
            row['cells'] = {k: v for k, v in row['cells'].items() if k in ('store', 'short')}
        slide['word_jobs']['takeaway_title']['text'] = 'Harbor Street has the highest barista gap.'
        self.assertIn('a bar or line chart shows that faster', ' '.join(self.result(spec)['warnings']))
        spec = self.spec()
        self.table_slide(spec)['word_jobs']['takeaway_title']['text'] = 'Harbor Street is short 3 baristas and waits 6.8 minutes.'
        self.assertFalse([w for w in self.result(spec)['warnings'] if 'match no plotted value' in w])

    def test_pptx_html_and_preview_agree(self):
        from pptx import Presentation
        import pptx_qa
        spec = self.spec()
        deck = pptx_renderer.compile_pptx(spec, self.work / 't.pptx')
        frame = next(sh for sl in Presentation(str(deck)).slides for sh in sl.shapes if sh.name == 'pai:data_table')
        tbl = frame.table
        self.assertTrue(tbl.first_row)
        self.assertFalse(tbl.horz_banding)
        model = pptx_renderer.table_model(self.table_slide(spec))
        body = [[c.text for c in row.cells] for row in list(tbl.rows)[2:]]
        self.assertEqual(body, [r['texts'] for r in model['rows']])
        self.assertEqual(frame._element.find('.//{*}cNvPr').get('descr'), 'Flagship store scorecard, FY2025')
        self.assertEqual([i for i in pptx_qa.inspect_pptx_typography(deck, 'standalone') if 'D-055' in i or 'table text' in i], [])
        out = html_renderer.compile_html(spec, self.work / 't.html').read_text(encoding='utf-8')
        self.assertIn('<caption>Flagship store scorecard, FY2025</caption>', out)
        self.assertIn('<th scope="colgroup" colspan="2" class="group">Customers</th>', out)
        for text in model['rows'][0]['texts'][1:]:
            self.assertIn(f'>{text}</td>', out)
        pngs = html_renderer.export_slide_pngs(spec, self.work / 'png')
        self.assertTrue(pngs[-1].exists())

    def test_overflow_and_vietnamese_headers(self):
        import pptx_qa
        spec = self.spec()
        spec['deck_meta']['deck_language'] = 'vi'
        table = self.table_slide(spec)['table_spec']
        table['columns'][2]['header'] = 'Thời gian chờ trung bình của khách hàng tại quầy (phút)'
        deck = pptx_renderer.compile_pptx(spec, self.work / 'vi.pptx')
        self.assertEqual([i for i in pptx_qa.inspect_pptx_typography(deck, 'standalone', deck_language='vi') if 'D-055' in i], [])
        table['rows'][0]['cells']['store']['text'] = 'Supercalifragilisticexpialidocious' * 4
        deck = pptx_renderer.compile_pptx(spec, self.work / 'long.pptx')
        self.assertTrue(any('does not fit its column' in i for i in pptx_qa.inspect_pptx_typography(deck, 'standalone')))


class HeatmapTable(CoffeeWorkspace, unittest.TestCase):
    """D-068 / PAT-VIS-006: heatmap fills on the table slide in the validator and the three renderers."""

    def result(self, spec):
        return validate_spec.validate_slide_spec_dict(spec, 't', self.work)

    def table(self, spec):
        return spec['appendix_slides'][0]['table_spec']

    def model(self, spec):
        return pptx_renderer.table_model(spec['appendix_slides'][0], spec['deck_meta'])

    def test_benchmark_heatmap_is_clean_and_fills_follow_dark_end(self):
        spec = self.spec()
        res = self.result(spec)
        self.assertEqual(res['errors'], [])
        self.assertFalse([w for w in res['warnings'] if 'D-068' in w])
        model = self.model(spec)
        self.assertTrue(model['has_heat'])
        self.assertIsNone(model['key'])  # per-column scales carry no key
        harbor, hillcrest = model['rows'][0], model['rows'][7]
        self.assertEqual(harbor['fills'][1], harbor['fills'][2])  # sales (dark low) and wait (dark high): Harbor is darkest in both
        self.assertNotEqual(harbor['fills'][1], hillcrest['fills'][1])
        self.assertIsNone(harbor['fills'][0])  # the key column is never shaded
        summary = model['rows'][-1]
        self.assertTrue(summary['summary'] and set(summary['fills']) == {None})
        self.assertFalse(any(r['focal'][j] for r in model['rows'] for j in range(1, 4)))  # shaded cells keep the heat ink
        self.table(spec)['heatmap']['columns'][0]['dark_end'] = 'high'
        flipped = self.model(spec)
        self.assertNotEqual(flipped['rows'][0]['fills'][1], harbor['fills'][1])

    def test_ink_reaches_contrast(self):
        import table_heatmap
        from color_contrast import contrast_ratio
        spec = self.spec()
        cells = table_heatmap.heatmap_cells(self.table(spec), spec['deck_meta'])
        for fill, ink in cells['fills'].values():
            self.assertGreaterEqual(contrast_ratio(ink, fill), 4.5)
        self.assertEqual(cells['notes'], [])

    def test_shared_scale_draws_a_key_and_validates_units(self):
        from pptx import Presentation
        spec = self.spec()
        table = self.table(spec)
        table['heatmap'] = {'scale': 'shared', 'steps': 5, 'columns': [{'col_id': 'wait', 'dark_end': 'high', 'unit': 'min'}, {'col_id': 'short', 'dark_end': 'high', 'unit': 'min'}]}
        self.assertEqual(self.result(spec)['errors'], [])
        model = self.model(spec)
        self.assertEqual(len(model['key']['colours']), 5)
        self.assertEqual(model['key']['edge_labels'][0], '0.0')
        self.assertEqual(model['key']['unit'], 'min')
        deck = pptx_renderer.compile_pptx(spec, self.work / 'k.pptx')
        shapes = [sh for sl in Presentation(str(deck)).slides for sh in sl.shapes]
        self.assertEqual(len([sh for sh in shapes if sh.name == 'pai:heat_key']), 5)
        out = html_renderer.compile_html(spec, self.work / 'k.html').read_text(encoding='utf-8')
        self.assertIn('class="heat-key"', out)
        self.assertTrue(html_renderer.export_slide_pngs(spec, self.work / 'kpng')[-1].exists())
        table['heatmap']['columns'][1]['unit'] = 'people'
        self.assertIn('needs the same `unit`', ' '.join(self.result(spec)['errors']))
        table['heatmap']['columns'][1].update({'unit': 'min', 'dark_end': 'low'})
        self.assertIn('one `dark_end`', ' '.join(self.result(spec)['errors']))

    def test_diverging_column_and_steps(self):
        spec = self.spec()
        table = self.table(spec)
        table['heatmap']['columns'][0].update({'scale_type': 'diverging', 'midpoint': 0})
        self.assertEqual(self.result(spec)['errors'], [])
        fills = [r['fills'][1] for r in self.model(spec)['rows'][:8]]
        self.assertGreaterEqual(len(set(fills)), 4)
        table['heatmap']['columns'][0]['midpoint'] = 50
        self.assertIn('lies outside the data', ' '.join(self.result(spec)['errors']))
        table['heatmap']['columns'][0]['midpoint'] = 0
        table['heatmap']['steps'] = 4
        self.assertIn('odd number of steps', ' '.join(self.result(spec)['errors']))
        table['heatmap']['steps'] = 9
        self.assertIn('`steps` must be 0', ' '.join(self.result(spec)['errors']))

    def test_renderers_agree_on_the_fills(self):
        from pptx import Presentation
        spec = self.spec()
        model = self.model(spec)
        deck = pptx_renderer.compile_pptx(spec, self.work / 'h.pptx')
        frame = next(sh for sl in Presentation(str(deck)).slides for sh in sl.shapes if sh.name == 'pai:data_table')
        row = list(frame.table.rows)[2]  # group row, header row, then the first data row
        self.assertEqual(str(row.cells[1].fill.fore_color.rgb), model['rows'][0]['fills'][1].lstrip('#'))
        out = html_renderer.compile_html(spec, self.work / 'h.html').read_text(encoding='utf-8')
        self.assertIn(f'style="background: {model["rows"][0]["fills"][1]}; color: {model["rows"][0]["inks"][1]}"', out)
        self.assertIn('class="data-table heat"', out)

    def test_grey_ramp_without_a_comparison_colour(self):
        import table_heatmap
        spec = self.spec()
        spec['deck_meta']['colour_kit'] = 'brand'
        cells = table_heatmap.heatmap_cells(self.table(spec), spec['deck_meta'])
        self.assertIn('grey ramp', ' '.join(cells['notes']))


class ProcessFlow(CoffeeWorkspace, unittest.TestCase):
    """D-069 / PAT-VIS-009: the diagram layout, the process flow type, the geometry check and the three renderers."""

    def result(self, spec):
        return validate_spec.validate_slide_spec_dict(spec, 't', self.work)

    def slide(self, spec):
        return next(s for s in spec['appendix_slides'] if (s.get('layout_spec') or {}).get('layout_type') == 'diagram')

    def block(self, spec):
        return self.slide(spec)['diagram_spec']['process_flow']

    def test_benchmark_diagram_is_clean(self):
        res = self.result(self.spec())
        self.assertEqual(res['errors'], [])
        self.assertFalse([w for w in res['warnings'] if 'D-069' in w])

    def test_structure_and_traceability_errors(self):
        spec = self.spec()
        block = self.block(spec)
        block['steps'][0].pop('source_cell_ref')
        block['steps'][1]['source_cell_ref'] = 'missing_file.md!Heading'
        for st in block['steps']:
            st.pop('focal', None)
        self.slide(spec)['diagram_spec'].pop('alt_text')
        errs = ' '.join(self.result(spec)['errors'])
        self.assertIn('needs its `source_cell_ref`', errs)
        self.assertIn("source file 'missing_file.md' not found", errs)
        self.assertIn('mark one or two focal steps', errs)
        self.assertIn('needs `alt_text`', errs)
        spec = self.spec()
        spec['slides'][0]['diagram_spec'] = self.slide(spec)['diagram_spec']
        self.slide(spec).pop('diagram_spec')
        errs = ' '.join(self.result(spec)['errors'])
        self.assertIn('`diagram_spec` belongs only on `diagram` slides', errs)
        self.assertIn('layout `diagram` requires `diagram_spec`', errs)

    def test_budget_and_live_warnings(self):
        spec = self.spec()
        block = self.block(spec)
        block['steps'] = block['steps'] + [{'step_id': f'extra_{i}', 'label': f'Extra {i}'} for i in range(3)]
        self.assertIn('a slide holds 3-6', ' '.join(self.result(spec)['warnings']))
        spec = self.spec()
        spec['deck_meta']['delivery_mode'] = 'live'
        slide = spec['appendix_slides'].pop(spec['appendix_slides'].index(self.slide(spec)))
        slide['arc_stage'] = 'falling_action'
        spec['slides'].append(slide)
        self.assertIn('reads a diagram before it hears it', ' '.join(self.result(spec)['warnings']))

    def test_geometry_check_catches_adversarial_layouts(self):
        import diagrams
        box = (0.6, 1.5, 12.0, 5.0)
        a = {'kind': 'rect', 'id': 'a', 'x': 1.0, 'y': 2.0, 'w': 2.0, 'h': 1.0}
        b = {'kind': 'rect', 'id': 'b', 'x': 6.0, 'y': 2.0, 'w': 2.0, 'h': 1.0}
        wall = {'kind': 'rect', 'id': 'wall', 'x': 4.0, 'y': 1.6, 'w': 0.5, 'h': 2.5}
        link = {'kind': 'connector', 'id': 'a__b', 'from': 'a', 'to': 'b', 'from_site': 3, 'to_site': 1}
        self.assertEqual(diagrams.geometry_issues([a, b, link], box), [])
        self.assertIn('connector passes through wall', ' '.join(diagrams.geometry_issues([a, b, wall, link], box)))
        self.assertIn('a and c: overlap', ' '.join(diagrams.geometry_issues([a, dict(b, id='c', x=2.5), link], box)))
        self.assertIn('lies outside the slide body', ' '.join(diagrams.geometry_issues([dict(a, x=-1.0)], box)))
        self.assertIn('connector end is missing', ' '.join(diagrams.geometry_issues([a, link], box)))

    def test_long_text_is_flagged(self):
        spec = self.spec()
        self.block(spec)['steps'][0]['label'] = 'Approve the budget for the barista hiring programme across all flagship stores this year ' * 4
        self.assertIn('its text needs', ' '.join(self.result(spec)['errors']))

    def test_pptx_connectors_are_glued_and_outputs_agree(self):
        from pptx import Presentation
        import pptx_qa
        spec = self.spec()
        deck = pptx_renderer.compile_pptx(spec, self.work / 'p.pptx')
        self.assertEqual(pptx_qa.inspect_pptx_diagrams(deck), [])
        group = next(sh for sl in Presentation(str(deck)).slides for sh in sl.shapes if sh.name == 'pai:diagram')
        self.assertTrue(group._element.find('.//{*}cNvPr').get('descr'))
        names = [c.name for c in group.shapes]
        self.assertEqual(len([n for n in names if n.startswith('pai:dg_connector_')]), 4)
        broken = self.work / 'broken.pptx'
        # a deck whose connector lost its end glue is reported
        prs = Presentation(str(deck))
        g = next(sh for sl in prs.slides for sh in sl.shapes if sh.name == 'pai:diagram')
        c = next(ch for ch in g.shapes if ch.name.startswith('pai:dg_connector_'))
        cx = c._element.find('.//{*}cNvCxnSpPr')
        cx.remove(cx.find('{*}endCxn'))
        prs.save(str(broken))
        self.assertIn('not glued to a shape at both ends', ' '.join(pptx_qa.inspect_pptx_diagrams(broken)))
        out = html_renderer.compile_html(spec, self.work / 'p.html').read_text(encoding='utf-8')
        self.assertIn('class="diagram-svg"', out)
        self.assertIn('role="img"', out)
        for label in ('Approve budget', 'Open the roles', 'Train on shift'):
            self.assertIn(f'>{label}</text>', out)
        self.assertTrue(html_renderer.export_slide_pngs(spec, self.work / 'ppng')[-1].exists())

    def test_numbered_style_has_no_arrows_and_reveal_filters(self):
        import diagrams
        spec = self.spec()
        self.block(spec)['style'] = 'numbered'
        slide = self.slide(spec)
        model = diagrams.diagram_model(slide, spec['deck_meta'], (0.6, 1.5, 12.13, 5.0))
        self.assertEqual([it for it in model['items'] if it['kind'] == 'connector'], [])
        self.assertEqual(len([it for it in model['items'] if it.get('role') == 'badge']), 5)
        self.assertEqual(self.result(spec)['errors'], [])
        spec = self.spec()
        slide = self.slide(spec)
        part = diagrams.diagram_model(slide, spec['deck_meta'], (0.6, 1.5, 12.13, 5.0), ['budget', 'open_roles'])
        self.assertEqual(sorted(it['id'] for it in part['items'] if it.get('role') == 'step'), ['budget', 'open_roles'])
        self.assertEqual(len([it for it in part['items'] if it['kind'] == 'connector']), 1)


class TimelineDiagram(CoffeeWorkspace, unittest.TestCase):
    """D-069 / PAT-VIS-009 / ANTI-VIS-004: the timeline type, dated positions, both forms, today marker and checks."""
    REF = 'source_report.md!Recruiting plan for the 22 open barista roles'

    def result(self, spec):
        return validate_spec.validate_slide_spec_dict(spec, 't', self.work)

    def slide(self, spec):
        return next(s for s in spec['appendix_slides'] if (s['diagram_spec']['diagram_type'] if s.get('diagram_spec') else '') == 'timeline')

    def block(self, spec):
        return self.slide(spec)['diagram_spec']['timeline']

    def model(self, spec, visible=None):
        import diagrams
        return diagrams.diagram_model(self.slide(spec), spec['deck_meta'], (0.6, 1.5, 12.13, 5.0), visible)

    def bars(self, spec):
        block = self.block(spec)
        block['form'] = 'bars'
        block['today'] = '2026-04-10'
        block['items'] = [
            {'item_id': 'screen', 'label': 'Post and screen roles', 'start': '2026-02-01', 'end': '2026-03-15', 'source_cell_ref': self.REF},
            {'item_id': 'wave1', 'label': 'Wave 1: hire and onboard', 'start': '2026-03-15', 'end': '2026-04-30', 'source_cell_ref': self.REF},
            {'item_id': 'wave2', 'label': 'Wave 2: hire and onboard', 'start': '2026-04-30', 'end': '2026-06-30', 'focal': True, 'source_cell_ref': self.REF},
            {'item_id': 'review', 'label': '90-day review', 'date': '2026-09-15', 'source_cell_ref': self.REF},
        ]

    def test_benchmark_timeline_is_clean(self):
        res = self.result(self.spec())
        self.assertEqual(res['errors'], [])
        self.assertFalse([w for w in res['warnings'] if 'D-069' in w])

    def test_positions_follow_the_dates(self):
        spec = self.spec()
        dots = {it['id']: it for it in self.model(spec)['items'] if it.get('role') == 'milestone'}
        centre = lambda it: it['x'] + it['w'] / 2  # noqa: E731
        span = centre(dots['review']) - centre(dots['budget'])
        days = (date(2026, 9, 15) - date(2026, 1, 15)).days
        for key, d in (('open_roles', date(2026, 2, 1)), ('wave1', date(2026, 3, 15)), ('trained', date(2026, 3, 31)), ('filled', date(2026, 6, 30))):
            want = centre(dots['budget']) + span * (d - date(2026, 1, 15)).days / days
            self.assertAlmostEqual(centre(dots[key]), want, places=3)
        self.assertEqual(self.model(spec)['issues'], [])

    def test_errors_for_dates_kinds_and_sources(self):
        spec = self.spec()
        block = self.block(spec)
        block['items'][0]['date'] = '2025-12-01'
        block['items'][1]['source_cell_ref'] = ''
        block['items'][2].pop('date')
        block['items'][2].update({'start': '2026-03-01', 'end': '2026-04-01'})
        for it in block['items']:
            it.pop('focal', None)
        errs = ' '.join(self.result(spec)['errors'])
        self.assertIn('lies outside the axis', errs)
        self.assertIn('needs its `source_cell_ref`', errs)
        self.assertIn('milestones form takes dated milestones', errs)
        self.assertIn('mark one or two focal items', errs)
        spec = self.spec()
        self.block(spec)['end'] = '2025-12-31'
        self.assertIn('`end` must be after `start`', ' '.join(self.result(spec)['errors']))

    def test_budget_ticks_and_today_warnings(self):
        spec = self.spec()
        block = self.block(spec)
        block['unit'] = 'week'
        block['today'] = '2027-01-01'
        block['items'] += [{'item_id': f'm{i}', 'label': f'Extra {i}', 'date': '2026-05-01', 'source_cell_ref': self.REF} for i in range(3)]
        warns = ' '.join(self.result(spec)['warnings'])
        self.assertIn('choose a coarser `unit`', warns)
        self.assertIn('`today` lies outside the axis', warns)
        self.assertIn('a slide holds up to 8', warns)

    def test_bars_form_today_marker_and_renderers(self):
        from pptx import Presentation
        spec = self.spec()
        self.bars(spec)
        self.assertEqual(self.result(spec)['errors'], [])
        items = self.model(spec)['items']
        self.assertEqual(len([it for it in items if it.get('role') == 'bar']), 3)
        self.assertEqual(len([it for it in items if it['kind'] == 'diamond']), 1)
        self.assertTrue(any(it['id'] == 'today' and it.get('dash') for it in items))
        self.assertEqual(self.model(spec)['issues'], [])
        deck = pptx_renderer.compile_pptx(spec, self.work / 'b.pptx')
        groups = [sh for sl in Presentation(str(deck)).slides for sh in sl.shapes if sh.name == 'pai:diagram']
        self.assertTrue(any(ch.name.startswith('pai:dg_line_today') for g in groups for ch in g.shapes))
        out = html_renderer.compile_html(spec, self.work / 'b.html').read_text(encoding='utf-8')
        self.assertIn('stroke-dasharray', out)
        self.assertTrue(html_renderer.export_slide_pngs(spec, self.work / 'bpng')[-1].exists())

    def test_reveal_filters_the_milestones(self):
        spec = self.spec()
        part = self.model(spec, ['budget', 'open_roles'])
        self.assertEqual(sorted(it['id'] for it in part['items'] if it.get('role') == 'milestone'), ['budget', 'open_roles'])
        self.assertTrue(all(it['id'].split('__')[0] in ('budget', 'open_roles') for it in part['items'] if it.get('reveal')))


class MatrixDiagram(CoffeeWorkspace, unittest.TestCase):
    """D-069 / SRC-SWD-011 §15: the 2×2 matrix, both variants, the axis band, labels clear of the axes and the checks."""

    def result(self, spec):
        return validate_spec.validate_slide_spec_dict(spec, 't', self.work)

    def slide(self, spec):
        return next(s for s in spec['appendix_slides'] if s.get('diagram_spec') and s['diagram_spec']['diagram_type'] == 'matrix_2x2')

    def block(self, spec):
        return self.slide(spec)['diagram_spec']['matrix_2x2']

    def model(self, spec, visible=None):
        import diagrams
        return diagrams.diagram_model(self.slide(spec), spec['deck_meta'], (0.6, 1.5, 12.13, 5.0), visible)

    def scenario(self, spec):
        block = self.block(spec)
        block['variant'] = 'scenario'
        block.pop('items')
        block['x_axis'] = {'title': 'Hiring pace', 'low_label': 'Slow', 'high_label': 'Fast'}
        block['y_axis'] = {'title': 'Demand', 'low_label': 'Weak', 'high_label': 'Strong'}
        block['cells'] = [
            {'cell_id': 'tl', 'name': 'Missed upside', 'description': 'Demand is strong; hiring lags'},
            {'cell_id': 'tr', 'name': 'Recover fast', 'description': 'Demand is strong; hiring keeps pace', 'focal': True},
            {'cell_id': 'bl', 'name': 'Slow drift', 'description': 'Demand is weak; hiring lags'},
            {'cell_id': 'br', 'name': 'Overstaffed', 'description': 'Demand is weak; hiring keeps pace'},
        ]

    def test_benchmark_matrix_is_clean_and_labels_avoid_the_axes(self):
        spec = self.spec()
        res = self.result(spec)
        self.assertEqual(res['errors'], [])
        self.assertFalse([w for w in res['warnings'] if 'D-069' in w])
        model = self.model(spec)
        self.assertEqual(model['issues'], [])
        px = 0.6 + 2.0
        pw = 12.13 - 2.0 - 0.4
        py = 1.5 + 0.1
        ph = 5.0 - 0.75
        for it in model['items']:
            if it.get('role') == 'item_label':
                self.assertFalse(it['x'] < px + pw / 2 < it['x'] + it['w'], it['id'])
                self.assertFalse(it['y'] < py + ph / 2 < it['y'] + it['h'], it['id'])

    def test_errors_for_axes_focal_and_sources(self):
        spec = self.spec()
        block = self.block(spec)
        block['items'][0]['y'] = 0.52
        block['items'][1].pop('source_cell_ref')
        for it in block['items']:
            it.pop('focal', None)
        errs = ' '.join(self.result(spec)['errors'])
        self.assertIn('sits on the axis', errs)
        self.assertIn('needs its `source_cell_ref`', errs)
        self.assertIn('mark one or two focal items', errs)
        spec = self.spec()
        self.block(spec)['items'] = self.block(spec)['items'][:2]
        self.assertIn('at least three items', ' '.join(self.result(spec)['errors']))
        spec = self.spec()
        self.block(spec)['cells'] = [{'cell_id': 'tl', 'name': 'Scenario 1'}]
        self.assertIn('has `items`, not `cells`', ' '.join(self.result(spec)['errors']))

    def test_judgement_placements_and_budget_warn(self):
        spec = self.spec()
        block = self.block(spec)
        for it in block['items']:
            it['placement_basis'] = 'judgement'
        block['items'] += [{'item_id': f'x{i}', 'label': f'Extra {i}', 'x': 0.1 + 0.05 * i, 'y': 0.9, 'placement_basis': 'judgement'} for i in range(5)]
        block['x_axis']['low_label'] = 'Quick and cheap to do'
        warns = ' '.join(self.result(spec)['warnings'])
        self.assertIn('some placements are judgements', warns)
        self.assertIn('a slide holds up to 10', warns)
        self.assertIn('one word at each axis tip', warns)

    def test_scenario_variant(self):
        from pptx import Presentation
        spec = self.spec()
        self.scenario(spec)
        self.assertEqual(self.result(spec)['errors'], [])
        cells = [it for it in self.model(spec)['items'] if it.get('role') == 'cell']
        self.assertEqual(sorted(c['id'] for c in cells), ['bl', 'br', 'tl', 'tr'])
        self.assertEqual([c['id'] for c in cells if c.get('focal')], ['tr'])
        self.assertEqual(self.model(spec)['issues'], [])
        deck = pptx_renderer.compile_pptx(spec, self.work / 's.pptx')
        group = next(sh for sl in Presentation(str(deck)).slides for sh in sl.shapes if sh.name == 'pai:diagram' and any(ch.name == 'pai:dg_tl' for ch in sh.shapes))
        self.assertEqual(len([ch for ch in group.shapes if ch.name in ('pai:dg_tl', 'pai:dg_tr', 'pai:dg_bl', 'pai:dg_br')]), 4)
        self.assertTrue(html_renderer.export_slide_pngs(spec, self.work / 'spng')[-1].exists())
        block = self.block(spec)
        block['cells'][0]['focal'] = True
        self.assertIn('exactly one cell is focal', ' '.join(self.result(spec)['errors']))
        block['cells'][0].pop('focal')
        block['cells'][1]['name'] = 'Missed upside'
        self.assertIn('every cell needs its own name', ' '.join(self.result(spec)['errors']))
        block['cells'][1]['name'] = 'Recover fast'
        block['cells'].pop()
        self.assertIn('exactly four cells', ' '.join(self.result(spec)['errors']))

    def test_renderers_and_reveal(self):
        spec = self.spec()
        out = html_renderer.compile_html(spec, self.work / 'm.html').read_text(encoding='utf-8')
        self.assertIn('>Fill 22 barista roles</text>', out)
        part = self.model(spec, ['fill_roles'])
        self.assertEqual(sorted(it['id'] for it in part['items'] if it.get('role') == 'item'), ['fill_roles'])
        self.assertTrue(any(it['id'] == 'plot' for it in part['items']))  # the frame and axes stay


class DecisionFlow(CoffeeWorkspace, unittest.TestCase):
    """D-071 / PAT-VIS-009 / PAT-DSN-006: the decision flowchart, elbow routes, answers at the exit and the elbow-aware geometry check."""

    def result(self, spec):
        return validate_spec.validate_slide_spec_dict(spec, 't', self.work)

    def slide(self, spec):
        return next(s for s in spec['appendix_slides'] if (s.get('diagram_spec') or {}).get('diagram_type') == 'decision_flow')

    def block(self, spec):
        return self.slide(spec)['diagram_spec']['decision_flow']

    def test_benchmark_flow_is_clean(self):
        import diagrams
        spec = self.spec()
        res = self.result(spec)
        self.assertEqual(res['errors'], [])
        self.assertFalse([w for w in res['warnings'] if 'D-071' in w])
        main, place, problems = diagrams.flow_paths(self.block(spec))
        self.assertEqual(main, ['applied', 'experienced', 'trial', 'passed', 'offer'])
        self.assertEqual(place['cohort'], (2, 1))
        self.assertEqual(problems, [])

    def test_structure_errors(self):
        spec = self.spec()
        block = self.block(spec)
        block['edges'][1].pop('answer')
        block['edges'].append({'from': 'trial', 'to': 'reapply'})
        block['edges'].append({'from': 'passed', 'to': 'ghost', 'answer': 'Maybe'})
        for n in block['nodes']:
            n.pop('focal', None)
        errs = ' '.join(self.result(spec)['errors'])
        self.assertIn('label the exit to `trial` with its answer', errs)
        self.assertIn('only a decision branches', errs)
        self.assertIn('`to: ghost`, which is not a node', errs)
        self.assertIn('mark one or two focal nodes', errs)
        spec = self.spec()
        block = self.block(spec)
        block['edges'].append({'from': 'passed', 'to': 'applied', 'answer': 'Retry'})
        errs = ' '.join(self.result(spec)['errors'])
        self.assertIn('loops back cannot be drawn', errs)
        spec = self.spec()
        block = self.block(spec)
        block['edges'] = [e for e in block['edges'] if e['to'] != 'cohort']
        self.assertIn('not reached from the main path', ' '.join(self.result(spec)['errors']))

    def test_budget_and_long_answer_warnings(self):
        spec = self.spec()
        block = self.block(spec)
        block['edges'][1]['answer'] = 'Yes, two years or more'
        block['nodes'] += [{'node_id': f'extra_{i}', 'kind': 'step', 'label': f'Extra {i}'} for i in range(3)]
        block['edges'] = [e for e in block['edges'] if e['from'] != 'passed'] + [{'from': 'passed', 'to': 'extra_0', 'answer': 'Yes'}, {'from': 'passed', 'to': 'reapply', 'answer': 'No'},
                                                                                {'from': 'extra_0', 'to': 'extra_1'}, {'from': 'extra_1', 'to': 'extra_2'}, {'from': 'extra_2', 'to': 'offer'}]
        warns = ' '.join(self.result(spec)['warnings'])
        self.assertIn('longer than 14 characters', warns)
        self.assertIn('a slide holds up to 9', warns)
        self.assertIn('the main path has 8 nodes', warns)

    def test_geometry_check_catches_adversarial_routes(self):
        import diagrams
        box = (0.6, 1.5, 12.0, 5.0)
        a = {'kind': 'rect', 'id': 'a', 'x': 1.0, 'y': 2.0, 'w': 2.0, 'h': 1.0}
        b = {'kind': 'rect', 'id': 'b', 'x': 6.0, 'y': 4.5, 'w': 2.0, 'h': 1.0}
        ell = {'kind': 'connector', 'id': 'a__b', 'from': 'a', 'to': 'b', 'from_site': 3, 'to_site': 0, 'route': 'hv'}
        self.assertEqual(diagrams.connector_points(ell, {'a': a, 'b': b}), [(3.0, 2.5), (7.0, 2.5), (7.0, 4.5)])
        self.assertEqual(diagrams.geometry_issues([a, b, ell], box), [])
        wall = {'kind': 'rect', 'id': 'wall', 'x': 6.5, 'y': 3.2, 'w': 1.0, 'h': 0.8}
        self.assertIn('connector passes through wall', ' '.join(diagrams.geometry_issues([a, b, wall, ell], box)))
        diag = dict(ell, id='diag', route='straight')
        self.assertIn('diag: connector runs diagonally', ' '.join(diagrams.geometry_issues([a, b, diag], box)))
        c = {'kind': 'rect', 'id': 'c', 'x': 9.0, 'y': 2.0, 'w': 2.0, 'h': 1.0}
        twin = {'kind': 'connector', 'id': 'a__c', 'from': 'a', 'to': 'c', 'from_site': 3, 'to_site': 1}
        issues = ' '.join(diagrams.geometry_issues([a, b, c, ell, twin], box))
        self.assertIn('connectors share a route', issues)
        self.assertIn('connectors meet at one point', issues)
        bus = [dict(ell, bus='a'), dict(twin, bus='a')]
        self.assertNotIn('share a route', ' '.join(diagrams.geometry_issues([a, b, c] + bus, box)))
        label = {'kind': 'text', 'id': 'ans', 'role': 'answer', 'x': 4.0, 'y': 2.4, 'w': 0.5, 'h': 0.3}
        self.assertIn('ans: the label touches connector a__b', ' '.join(diagrams.geometry_issues([a, b, ell, label], box)))

    def test_pptx_routes_html_and_png(self):
        from pptx import Presentation
        import pptx_qa
        spec = self.spec()
        deck = pptx_renderer.compile_pptx(spec, self.work / 'f.pptx')
        self.assertEqual(pptx_qa.inspect_pptx_diagrams(deck), [])
        group = next(sh for sl in Presentation(str(deck)).slides for sh in sl.shapes
                     if sh.name == 'pai:diagram' and any(c.name == 'pai:dg_connector_cohort__trial' for c in sh.shapes))
        conns = {c.name.replace('pai:dg_connector_', ''): c._element for c in group.shapes if c.name.startswith('pai:dg_connector_')}
        self.assertEqual(len(conns), 7)
        prst = lambda el: el.find('.//{*}prstGeom').get('prst')  # noqa: E731
        self.assertEqual(prst(conns['cohort__trial']), 'bentConnector2')
        self.assertEqual(prst(conns['applied__experienced']), 'bentConnector3')  # aligned ends: a zero-height elbow, so hand moves stay square
        self.assertEqual(conns['experienced__cohort'].find('.//{*}xfrm').get('rot'), '5400000')
        names = [c.name for c in group.shapes]
        self.assertIn('pai:dg_experienced__cohort__answer', names)
        self.assertTrue(any(c.name == 'pai:dg_applied' and c.auto_shape_type is not None for c in group.shapes))
        out = html_renderer.compile_html(spec, self.work / 'f.html').read_text(encoding='utf-8')
        self.assertIn('<polyline', out)
        ids = re.findall(r'<marker id="([^"]+)"', out)
        self.assertEqual(len(ids), len(set(ids)))  # page-wide ids: a shared id would borrow a hidden slide's marker
        for label in ('Barista experience?', 'Training cohort', 'Yes', 'No'):
            self.assertIn(f'>{label}</text>', out)
        self.assertTrue(html_renderer.export_slide_pngs(spec, self.work / 'fpng')[-1].exists())

    def test_reveal_filters_nodes_connectors_and_answers(self):
        import diagrams
        spec = self.spec()
        part = diagrams.diagram_model(self.slide(spec), spec['deck_meta'], (0.6, 1.5, 12.13, 5.0), ['applied', 'experienced', 'trial'])
        self.assertEqual(sorted(it['id'] for it in part['items'] if it.get('role') == 'node'), ['applied', 'experienced', 'trial'])
        self.assertEqual(len([it for it in part['items'] if it['kind'] == 'connector']), 2)
        self.assertEqual([it['id'] for it in part['items'] if it.get('role') == 'answer'], ['experienced__trial__answer'])


class SwimlaneDiagram(CoffeeWorkspace, unittest.TestCase):
    """D-071 3A / PAT-VIS-009: owner lanes, hand-offs kept in their column, the focal hand-off and its checks."""

    def result(self, spec):
        return validate_spec.validate_slide_spec_dict(spec, 't', self.work)

    def slide(self, spec):
        return next(s for s in spec['appendix_slides'] if (s.get('diagram_spec') or {}).get('diagram_type') == 'swimlane')

    def block(self, spec):
        return self.slide(spec)['diagram_spec']['swimlane']

    def model(self, spec):
        import diagrams
        return diagrams.diagram_model(self.slide(spec), spec['deck_meta'], (0.6, 1.5, 12.13, 5.0))

    def test_benchmark_swimlane_is_clean_and_keeps_hand_offs_in_their_column(self):
        import diagrams
        spec = self.spec()
        res = self.result(spec)
        self.assertEqual(res['errors'], [])
        self.assertFalse([w for w in res['warnings'] if 'D-071' in w])
        self.assertEqual(diagrams.swim_columns(self.block(spec)), {'request': 0, 'post': 0, 'screen': 1, 'trial': 1, 'decide': 2, 'offer': 2})
        conns = {it['id']: it for it in self.model(spec)['items'] if it['kind'] == 'connector'}
        self.assertEqual(conns['screen__trial']['route'], 'straight')
        self.assertEqual(conns['trial__decide']['route'], 'hvh')
        self.assertNotEqual(conns['screen__trial']['colour'], conns['post__screen']['colour'])
        self.assertEqual(self.model(spec)['issues'], [])

    def test_editorial_boxes_fill_their_column(self):
        import diagrams
        spec = self.spec()
        spec['deck_meta']['design_system'] = 'editorial'
        steps = [it for it in self.model(spec)['items'] if it.get('role') == 'step']
        xs = sorted({round(it['x'], 3) for it in steps})
        pitch = xs[1] - xs[0]
        self.assertGreaterEqual(steps[0]['w'], diagrams.SWIM_BOX_SHARE * pitch - 0.01)
        self.assertGreaterEqual(pitch - steps[0]['w'], diagrams.FLOW_GAP_MIN - 0.01)
        self.assertEqual(self.model(spec)['issues'], [])

    def test_a_blocked_column_moves_the_hand_off_on(self):
        import diagrams
        block = {'lanes': [{'lane_id': 'a'}, {'lane_id': 'b'}, {'lane_id': 'c'}],
                 'steps': [{'step_id': 's1', 'lane_id': 'b'}, {'step_id': 's2', 'lane_id': 'a'}, {'step_id': 's3', 'lane_id': 'c'}]}
        # s2 keeps column 0 above s1; s3 cannot pass through s1 in lane b, so it moves to column 1
        self.assertEqual(diagrams.swim_columns(block), {'s1': 0, 's2': 0, 's3': 1})

    def test_structure_errors_and_budget_warnings(self):
        spec = self.spec()
        block = self.block(spec)
        block['steps'][1]['lane_id'] = 'finance'
        block['focal_handoff'] = {'from': 'request', 'to': 'screen', 'label': '5-day wait'}
        errs = ' '.join(self.result(spec)['errors'])
        self.assertIn('`finance` is not a lane', errs)
        self.assertIn('two consecutive steps in different lanes', errs)
        spec = self.spec()
        block = self.block(spec)
        block.pop('focal_handoff')
        self.assertIn('mark one or two focal elements', ' '.join(self.result(spec)['errors']))
        spec = self.spec()
        block = self.block(spec)
        block['focal_handoff']['label'] = 'Five working days'
        block['lanes'] += [{'lane_id': f'x{i}', 'name': f'Extra {i}'} for i in range(2)]
        block['steps'] += [{'step_id': 'extra', 'lane_id': 'x0', 'label': 'Extra step'}]
        warns = ' '.join(self.result(spec)['warnings'])
        self.assertIn('longer than 14 characters', warns)
        self.assertIn('5 lanes; a slide holds up to 4', warns)
        self.assertIn('7 steps; a slide holds up to 6', warns)
        self.assertIn('a lane without steps', warns)

    def test_renderers(self):
        from pptx import Presentation
        import pptx_qa
        spec = self.spec()
        deck = pptx_renderer.compile_pptx(spec, self.work / 'w.pptx')
        self.assertEqual(pptx_qa.inspect_pptx_diagrams(deck), [])
        group = next(sh for sl in Presentation(str(deck)).slides for sh in sl.shapes
                     if sh.name == 'pai:diagram' and any(c.name == 'pai:dg_lane_trainer' for c in sh.shapes))
        conns = [c for c in group.shapes if c.name.startswith('pai:dg_connector_')]
        self.assertEqual(len(conns), 5)
        self.assertIn('pai:dg_screen__trial__label', [c.name for c in group.shapes])
        out = html_renderer.compile_html(spec, self.work / 'w.html').read_text(encoding='utf-8')
        for label in ('Regional trainer', 'Send offer', '5-day wait'):
            self.assertIn(f'>{label}</text>', out)
        self.assertTrue(html_renderer.export_slide_pngs(spec, self.work / 'wpng')[-1].exists())


class TreeDiagram(CoffeeWorkspace, unittest.TestCase):
    """D-071 4A/4B / PAT-VIS-009: bus trees in both directions, the additive check, focal rule and budgets."""

    def result(self, spec):
        return validate_spec.validate_slide_spec_dict(spec, 't', self.work)

    def slide(self, spec):
        return next(s for s in spec['appendix_slides'] if (s.get('diagram_spec') or {}).get('diagram_type') == 'tree')

    def block(self, spec):
        return self.slide(spec)['diagram_spec']['tree']

    def model(self, spec):
        import diagrams
        return diagrams.diagram_model(self.slide(spec), spec['deck_meta'], (0.6, 1.5, 12.13, 5.0))

    def deepen(self, block):
        block['nodes'] += [{'node_id': 'quit', 'parent': 'baristas', 'label': 'Resignations', 'value': 14, 'value_label': '14 roles', 'source_cell_ref': 'roles.csv!R2C2:R2C3'},
                           {'node_id': 'slow', 'parent': 'baristas', 'label': 'Slow hiring', 'value': 8, 'value_label': '8 roles', 'source_cell_ref': 'roles.csv!R2C2:R2C3'}]

    def test_benchmark_tree_is_clean_with_one_bus(self):
        spec = self.spec()
        res = self.result(spec)
        self.assertEqual(res['errors'], [])
        self.assertFalse([w for w in res['warnings'] if 'D-071' in w])
        model = self.model(spec)
        self.assertEqual(model['issues'], [])
        conns = [it for it in model['items'] if it['kind'] == 'connector']
        self.assertEqual({c['bus'] for c in conns}, {'gap'})
        self.assertTrue(all(not c['arrow'] for c in conns))
        self.assertEqual({c['route'] for c in conns}, {'hvh'})

    def test_down_direction_uses_rotated_elbows(self):
        from pptx import Presentation
        spec = self.spec()
        block = self.block(spec)
        block['direction'] = 'down'
        self.deepen(block)
        self.assertEqual(self.result(spec)['errors'], [])
        model = self.model(spec)
        self.assertEqual(model['issues'], [])
        routes = {it['id']: it['route'] for it in model['items'] if it['kind'] == 'connector'}
        self.assertEqual(routes['gap__baristas'], 'vhv')
        deck = pptx_renderer.compile_pptx(spec, self.work / 'td.pptx')
        group = next(sh for sl in Presentation(str(deck)).slides for sh in sl.shapes
                     if sh.name == 'pai:diagram' and any(c.name == 'pai:dg_quit' for c in sh.shapes))
        conn = next(c for c in group.shapes if c.name == 'pai:dg_connector_baristas__quit')
        self.assertEqual(conn._element.find('.//{*}xfrm').get('rot'), '5400000')

    def test_structure_additive_and_focal_errors(self):
        spec = self.spec()
        block = self.block(spec)
        block['nodes'][2]['value'] = 7
        block['nodes'][0]['focal'] = True
        block['nodes'].append({'node_id': 'orphan', 'parent': 'nobody', 'label': 'Orphan'})
        errs = ' '.join(self.result(spec)['errors'])
        self.assertIn('the children add up to 31, not 30', errs)
        self.assertIn('not both', errs)
        self.assertIn('its parent `nobody` is not a node', errs)
        spec = self.spec()
        self.block(spec)['nodes'][1].pop('parent')
        self.assertIn('exactly one root', ' '.join(self.result(spec)['errors']))

    def test_html_and_png(self):
        spec = self.spec()
        out = html_renderer.compile_html(spec, self.work / 't.html').read_text(encoding='utf-8')
        for label in ('Baristas', '22 roles', 'Bakers'):
            self.assertIn(f'>{label}</text>', out)
        self.assertTrue(html_renderer.export_slide_pngs(spec, self.work / 'tpng')[-1].exists())


class DotPlots(CoffeeWorkspace, unittest.TestCase):
    """D-056 / PAT-VIS-005: horizontal and connected dot plots, connectors, arrows and lighter gridlines."""
    RUN = ROOT / '50_evals/runs/bench_en_software_1plus4'

    def result(self, spec):
        return validate_spec.validate_slide_spec_dict(spec, 't', self.work)

    def panel(self, spec):
        return spec['appendix_slides'][0]['visual_spec']['panels'][0]

    def chart_xml(self, deck, slide_no):
        from pptx import Presentation
        slide = content_slides(deck)[slide_no]
        return [sh.chart._chartSpace for sh in slide.shapes if getattr(sh, 'has_chart', False) and sh.has_chart]

    def test_benchmark_is_clean_and_checks_fire(self):
        res = self.result(self.spec())
        self.assertEqual(res['errors'], [])
        self.assertFalse([w for w in res['warnings'] if 'D-056' in w or 'PAT-VIS-005' in w])
        spec = self.spec()
        self.panel(spec)['x_axis']['categories'] = list(reversed(self.panel(spec)['x_axis']['categories']))
        self.assertIn('not in the stated order', ' '.join(self.result(spec)['warnings']))
        spec = self.spec()
        spec['appendix_slides'][0].pop('progressive_reveal')  # D-059: the reading aid lives in the speaker notes
        self.assertIn('less familiar than bars', ' '.join(self.result(spec)['warnings']))
        spec = self.spec()
        line = next(p for s in spec['slides'] for p in (s.get('visual_spec') or {}).get('panels', []) if p['chart_family'] == 'line_chart')
        line['series'] = [dict(line['series'][0], visual_role='context_greyscale', series_name=f's{i}') for i in range(6)]
        self.assertIn('lines and none in the focal tier', ' '.join(self.result(spec)['warnings']))

    def test_pptx_horizontal_vertical_and_arrow(self):
        spec = self.spec()
        deck = pptx_renderer.compile_pptx(spec, self.work / 'h.pptx')
        cs = self.chart_xml(deck, -1)[0]
        self.assertIsNotNone(cs.find('.//{*}scatterChart'))
        err = cs.find('.//{*}errBars')
        self.assertEqual(err.find('{*}errDir').get('val'), 'x')
        from pptx import Presentation
        names = [sh.name for sh in content_slides(deck)[-1].shapes]
        self.assertEqual(names.count('pai:label'), 4)
        self.assertIn('E5E7EB', ''.join(el.get('val', '') for el in self.chart_xml(deck, 0)[0].iter('{*}srgbClr')))  # P10 gridlines
        p = self.panel(spec)
        p['orientation'] = 'vertical'
        deck = pptx_renderer.compile_pptx(spec, self.work / 'v.pptx')
        self.assertIsNotNone(self.chart_xml(deck, -1)[0].find('.//{*}hiLowLines'))
        p['connector'] = 'arrow'
        deck = pptx_renderer.compile_pptx(spec, self.work / 'a.pptx')
        err = self.chart_xml(deck, -1)[0].find('.//{*}errBars')
        self.assertEqual(err.find('.//{*}tailEnd').get('w'), 'lg')
        plus = [float(v.text) for v in err.find('{*}plus').iter('{*}v')]
        gaps = [b['value'] - a['value'] for a, b in zip(p['series'][0]['data_points'], p['series'][1]['data_points'])]
        for length, gap in zip(plus, gaps):
            if gap > 0:
                self.assertLess(length, gap)  # the tip stops at the end dot's edge
        import pptx_qa
        self.assertEqual([i for i in pptx_qa.inspect_pptx_typography(deck, 'live') if 'floor' in i], [])

    def test_html_and_preview(self):
        spec = self.spec()
        out = html_renderer.compile_html(spec, self.work / 'd.html').read_text(encoding='utf-8')
        self.assertIn('class="dot-connector"', out)
        self.panel(spec)['connector'] = 'arrow'
        out = html_renderer.compile_html(spec, self.work / 'a.html').read_text(encoding='utf-8')
        self.assertIn('dot-connector arrow', out)
        self.assertTrue(html_renderer.export_slide_pngs(spec, self.work / 'png')[-1].exists())

    def test_vietnamese_single_horizontal(self):
        import pptx_qa
        spec = self.spec()
        spec['deck_meta']['deck_language'] = 'vi'
        p = self.panel(spec)
        p['dot_style'] = 'single'
        p.pop('connector'); p['category_order'] = 'natural'
        p['series'] = p['series'][1:]
        p['x_axis']['categories'] = ['Châu Mỹ', 'Châu Âu', 'Châu Á – Thái Bình Dương', 'Trung Đông và châu Phi']
        for dp, cat in zip(p['series'][0]['data_points'], p['x_axis']['categories']):
            dp['category'] = cat
        deck = pptx_renderer.compile_pptx(spec, self.work / 'vi.pptx')
        self.assertEqual([i for i in pptx_qa.inspect_pptx_typography(deck, 'live', deck_language='vi') if 'floor' in i], [])


class BarForms(CoffeeWorkspace, unittest.TestCase):
    """D-057 / PAT-VIS-004: horizontal, 100 % and diverging stacks, separators, clustered cap and bar order."""
    RUN = ROOT / '50_evals/runs/bench_vi_briefing_no_ask'

    def result(self, spec):
        return validate_spec.validate_slide_spec_dict(spec, 't', self.work)

    def panel(self, spec):
        return spec['appendix_slides'][0]['visual_spec']['panels'][0]

    def chart(self, deck):
        from pptx import Presentation
        slide = content_slides(deck)[-1]
        return next(sh.chart for sh in slide.shapes if getattr(sh, 'has_chart', False) and sh.has_chart), slide

    def test_benchmark_is_clean_and_checks_fire(self):
        res = self.result(self.spec())
        self.assertEqual(res['errors'], [])
        self.assertFalse([w for w in res['warnings'] if 'D-057' in w or 'PAT-VIS-004' in w])
        spec = self.spec()
        p = self.panel(spec)
        p['stack_mode'] = 'percent'
        for ser in p['series']:
            ser.pop('diverging_side')
        p['series'][0]['data_points'][0]['value'] = 40.0
        p['series'][0]['visual_role'] = 'context_greyscale'  # the focal series ('Tốt hơn nhiều') is now last
        warns = ' '.join(self.result(spec)['warnings'])
        self.assertIn('do not sum to 100', warns)
        self.assertIn('is not first, so it has no baseline', warns)
        spec = self.spec()
        p = self.panel(spec)
        p['series'][0]['diverging_side'] = 'positive'
        self.assertIn('from the most negative answer', ' '.join(self.result(spec)['errors']))
        p['series'][0]['diverging_side'] = 'negative'
        p.pop('colour_scale')
        errors = ' '.join(self.result(spec)['errors'])
        self.assertIn('needs `colour_scale: diverging`', errors)
        spec = self.spec()
        bars = spec['slides'][1]['visual_spec']['panels'][0]
        bars['series'] = [dict(bars['series'][0], series_name=f's{i}') for i in range(4)]
        bars['category_order'] = 'by_value'
        bars['x_axis']['categories'] = list(reversed(bars['x_axis']['categories']))
        for ser in bars['series']:
            ser['data_points'] = list(reversed(ser['data_points']))
        res = self.result(spec)
        warns = ' '.join(res['warnings'])
        self.assertIn('4 clustered bar series', warns)
        self.assertIn('not sorted largest first', warns)
        self.assertNotIn('apply only to `dot_plot`', ' '.join(res['errors']))  # B7: category_order is legal on bars
        bars['stack_mode'], bars['category_order'] = 'count', 'by_gap'
        errors = ' '.join(self.result(spec)['errors'])
        self.assertIn('`stack_mode` applies only to `stacked_bar_chart`', errors)
        self.assertIn('`by_gap` is for connected dot plots', errors)

    def test_pptx_diverging_emission_axis_and_separators(self):
        chart, slide = self.chart(pptx_renderer.compile_pptx(self.spec(), self.work / 'd.pptx'))
        cs = chart._chartSpace
        self.assertEqual(cs.find('.//{*}barDir').get('val'), 'bar')
        self.assertEqual(cs.find('.//{*}grouping').get('val'), 'stacked')
        series = list(chart.plots[0].series)[:6]
        self.assertEqual([s.name for s in series], ['Như năm nay', 'Xấu hơn', 'Xấu hơn nhiều', 'Như năm nay', 'Tốt hơn', 'Tốt hơn nhiều'])
        self.assertTrue(all(v < 0 for s in series[:3] for v in s.values))  # neutral half, then outward from zero
        self.assertTrue(all(v > 0 for s in series[3:] for v in s.values))
        self.assertAlmostEqual(-series[0].values[0], series[3].values[0])
        fmt = cs.find('.//{*}valAx/{*}numFmt').get('formatCode')
        self.assertEqual(fmt.split(';')[0], fmt.split(';')[1])  # B3: no minus signs on the axis
        self.assertEqual(cs.find('.//{*}valAx/{*}crosses').get('val'), 'max')
        self.assertEqual(chart.value_axis.minimum_scale, -chart.value_axis.maximum_scale)
        labels = [t.text for t in cs.iter('{*}t')]
        self.assertTrue(labels and not any(t.startswith('-') for t in labels))
        self.assertEqual(sum(t == '31%' for t in labels), 1)  # the split neutral answer is labelled once
        ln = series[1].format.line
        self.assertEqual((str(ln.color.rgb), ln.width.pt), ('FFFFFF', pptx_renderer.SEPARATOR_PT))
        names = [s['series_name'] for s in self.panel(self.spec())['series']]
        self.assertTrue(chart.has_legend)  # D-060: a native legend in answer order; drawn series are hidden from it
        self.assertEqual([s.name for s in chart.plots[0].series][6:], names)
        self.assertEqual(len(cs.findall('.//{*}legendEntry')), 6)
        self.assertEqual(ln.color.rgb, series[5].format.line.color.rgb)
        from color_contrast import inside_label_hex
        self.assertEqual((inside_label_hex('#D95F02'), inside_label_hex('#8C8C8C'), inside_label_hex('#86B0DA')), ('#FFFFFF', '#1F2937', '#1F2937'))

    def test_pptx_horizontal_count_and_percent(self):
        spec = self.spec()
        p = self.panel(spec)
        p['stack_mode'] = 'percent'
        chart, _ = self.chart(pptx_renderer.compile_pptx(spec, self.work / 'p.pptx'))
        cs = chart._chartSpace
        self.assertEqual((cs.find('.//{*}barDir').get('val'), cs.find('.//{*}grouping').get('val')), ('bar', 'percentStacked'))
        self.assertEqual((chart.value_axis.minimum_scale, chart.value_axis.maximum_scale), (0, 1))
        self.assertEqual(cs.find('.//{*}valAx/{*}numFmt').get('formatCode'), '0%')
        self.assertEqual([s.name for s in chart.plots[0].series], [s['series_name'] for s in p['series']])  # spec order
        p['stack_mode'], p['orientation'] = 'count', 'vertical'
        chart, _ = self.chart(pptx_renderer.compile_pptx(spec, self.work / 'c.pptx'))
        cs = chart._chartSpace
        self.assertEqual((cs.find('.//{*}barDir').get('val'), cs.find('.//{*}grouping').get('val')), ('col', 'stacked'))

    def test_html_and_preview_agree(self):
        spec = self.spec()
        out = html_renderer.compile_html(spec, self.work / 'd.html').read_text(encoding='utf-8')
        svg = out[out.index('data-panel-id="panel_outlook"'):]
        svg = svg[:svg.index('</svg>')]
        self.assertEqual(svg.count('class="stack-segment'), 3 * 6)  # three rows, neutral drawn in two halves
        self.assertEqual(svg.count('class="stack-legend"'), 5)
        self.assertNotIn('>-', svg)
        self.assertIn(f'stroke-width="{pptx_renderer.SEPARATOR_PT:.2f}"'[:-6], svg)
        model = html_renderer.stack_model(self.panel(spec))
        self.assertEqual(model['axis'], (-80.0, 80.0, 40.0))
        self.assertEqual([lbl[2] for lbl in model['rows'][0]['labels'] if abs(lbl[0]) < 1e-9], ['31%'])  # neutral centred on zero
        self.panel(spec)['orientation'] = 'vertical'
        out = html_renderer.compile_html(spec, self.work / 'v.html').read_text(encoding='utf-8')
        self.assertIn('class="stack-segment', out)
        self.assertTrue(html_renderer.export_slide_pngs(spec, self.work / 'png')[-1].exists())

    def test_vietnamese_labels_meet_floors(self):
        import pptx_qa
        deck = pptx_renderer.compile_pptx(self.spec(), self.work / 'vi.pptx')
        self.assertEqual([i for i in pptx_qa.inspect_pptx_typography(deck, 'live', deck_language='vi') if 'floor' in i], [])


class NoDefensiveCaveats(CoffeeWorkspace, unittest.TestCase):
    """D-058: cards carry insights, never method caveats; no slide text tells the audience how to read it."""
    RUN = ROOT / '50_evals/runs/bench_vi_briefing_no_ask'

    def errors(self, spec):
        return ' '.join(validate_spec.validate_slide_spec_dict(spec, 't', self.work)['errors'])

    def test_caveat_cards_and_reader_instructions_fail(self):
        self.assertNotIn('D-058', self.errors(self.spec()))
        for text in ('Nhóm trên 50 thành viên chỉ có 18 hợp tác xã trả lời.', 'Mức 27,8% chưa đủ chắc để so sánh.',
                     'Only 18 respondents in this group.', 'Interpret the 27.8% with caution.'):
            spec = self.spec()
            spec['slides'][2]['word_jobs']['annotations'] = [{'text': text, 'target_panel_id': 'panel_size', 'anchor_data_point': '-', 'color_tie_spans': []}]
            self.assertIn('defensive method caveat', self.errors(spec), text)
        for loc, text in (('reading_note', 'Biểu đồ này cần đọc theo hàng ngang.'), ('chart_title', 'Revenue (should be read as an index)')):
            spec = self.spec()
            spec['slides'][2]['word_jobs'][loc] = text
            self.assertIn('tells the audience how to read', self.errors(spec), text)
        spec = self.spec()
        spec['slides'][4]['word_jobs']['implementation_steps'][2]['title'] = 'Kế hoạch thận trọng'
        self.assertNotIn('D-058', self.errors(spec))  # an insight about caution is not a caveat

    def test_d059_repeat_cards_and_reading_guidance_warn(self):
        warns = lambda spec: ' '.join(validate_spec.validate_slide_spec_dict(spec, 't', self.work)['warnings'])  # noqa: E731
        self.assertNotIn('D-059', warns(self.spec()))
        spec = self.spec()
        wj = spec['slides'][2]['word_jobs']
        wj['recommendation_callout']['text'] = 'Hợp tác xã nhỏ báo giảm doanh thu nhiều hơn nhóm lớn.'
        self.assertIn('mostly restates the title', warns(spec))
        spec = self.spec()
        spec['slides'][2]['word_jobs']['reading_note'] = 'Mỗi thanh là một nhóm quy mô.'
        self.assertIn('explains how to read the chart', warns(spec))


class KeySlides(CoffeeWorkspace, unittest.TestCase):
    """D-063: dark key slides (non-chart only, capped) and the section divider in contract, validator and renderers."""
    RUN = ROOT / '50_evals/runs/bench_vi_bep_giao_do_an'

    def result(self, spec):
        return validate_spec.validate_slide_spec_dict(spec, 't', self.work)

    def with_divider(self, spec):
        closing = spec['slides'][-1]
        div = {k: v for k, v in closing.items() if k != 'progressive_reveal'}
        div = yaml.safe_load(yaml.safe_dump(div))
        div['slide_id'] = 'divider_02'
        div['layout_spec'].update(layout_type='section_divider', section_number=2)
        wj = div['word_jobs']
        wj['takeaway_title'].update(text='Đơn trễ dồn vào hai khung giờ cao điểm.', color_tie_spans=[])
        wj['section_question'] = 'Đơn trễ tập trung vào lúc nào, và bếp thiếu gì ở những giờ đó?'
        for k in ('recommendation_callout', 'implementation_steps', 'annotations', 'chart_title'):
            wj.pop(k, None)
        spec['slides'].insert(1, div)
        return spec

    def test_closing_decision_slide_is_key_by_default(self):
        spec = self.spec()
        self.assertEqual(pptx_renderer.key_slide_ids(spec), {spec['slides'][-1]['slide_id']})
        spec['slides'][-1]['layout_spec']['emphasis'] = 'standard'
        self.assertEqual(pptx_renderer.key_slide_ids(spec), set())
        dark = pptx_renderer.key_slide_palette(spec['deck_meta'])
        for role in ('focal', 'text_primary', 'text_muted'):
            self.assertGreaterEqual(validate_spec.contrast_ratio(dark[role], dark['background']), 4.5, role)

    def test_validator_rules(self):
        self.assertFalse([e for e in self.result(self.spec())['errors'] if 'D-063' in e])
        spec = self.spec()
        spec['slides'][0]['layout_spec']['emphasis'] = 'key'
        self.assertIn('only non-chart slides can be key slides', ' '.join(self.result(spec)['errors']))
        spec = self.with_divider(self.spec())
        res = self.result(spec)
        self.assertFalse([e for e in res['errors'] if 'D-063' in e])
        self.assertIn('dividers pay off from', ' '.join(res['warnings']))
        div = spec['slides'][1]
        div['layout_spec'].pop('section_number')
        div['word_jobs']['section_question'] = ''
        div['word_jobs']['recommendation_callout'] = {'text': 'Duyệt ngay.'}
        errs = ' '.join(self.result(spec)['errors'])
        for msg in ('needs `layout_spec.section_number`', 'needs `word_jobs.section_question`', 'remove recommendation_callout'):
            self.assertIn(msg, errs)
        spec = self.spec()
        spec['slides'][-2].setdefault('layout_spec', {})
        spec['slides'][-2]['layout_spec'].update(layout_type='statement_or_transition', emphasis='key')
        spec['slides'][-2].pop('visual_spec', None)
        res = self.result(spec)
        self.assertIn('needs `emphasis_reason`', ' '.join(res['errors']))
        self.assertIn('two key slides in a row', ' '.join(res['warnings']))

    def test_renderers_draw_key_slides_and_dividers(self):
        from pptx import Presentation
        import html_renderer
        import pptx_qa
        spec = self.with_divider(self.spec())
        dark = pptx_renderer.key_slide_palette(spec['deck_meta'])
        deck = pptx_renderer.compile_pptx(spec, self.work / 'k.pptx')
        slides = content_slides(deck)
        div, closing = slides[1], slides[len(spec['slides']) - 1]
        for s in (div, closing):
            self.assertEqual(str(s.background.fill.fore_color.rgb), dark['background'].lstrip('#'))
        self.assertNotEqual(slides[0].background.fill.type, MSO_FILL.SOLID)
        names = {sh.name for sh in div.shapes}
        self.assertTrue({'pai:section_number', 'pai:section_question'} <= names)
        self.assertEqual(div.shapes.title.text_frame.text.replace('\xa0', ' '), 'Đơn trễ dồn vào hai khung giờ cao điểm.')
        tie = [r for r in closing.shapes.title.text_frame.paragraphs[0].runs if r.font.color and r.font.color.type is not None]
        self.assertIn(dark['focal'].lstrip('#'), {str(r.font.color.rgb) for r in tie})
        self.assertEqual(pptx_qa.inspect_pptx_typography(deck, 'live', deck_language='vi'), [])
        page = html_renderer.compile_html(spec, self.work / 'k.html').read_text(encoding='utf-8')
        self.assertIn('class="slide divider key', page)
        self.assertIn('class="section-number">02<', page)
        pngs = html_renderer.export_slide_pngs(spec, self.work / 'png')
        self.assertEqual(len(pngs), len(spec['slides']) + len(spec.get('appendix_slides') or []))


class TilesImageSpotlight(CoffeeWorkspace, unittest.TestCase):
    """D-064: two-thirds card grid, side image slot, big-number tiles and the spotlight slide."""
    RUN = ROOT / '50_evals/runs/bench_vi_briefing_no_ask'

    def result(self, spec):
        return validate_spec.validate_slide_spec_dict(spec, 't', self.work)

    def tile_slide(self, spec):
        return next(s for s in spec['slides'] if (s.get('word_jobs') or {}).get('step_style') == 'big_number')

    def test_tile_rules(self):
        self.assertFalse([e for e in self.result(self.spec())['errors'] if 'D-064' in e])
        spec = self.spec()
        steps = self.tile_slide(spec)['word_jobs']['implementation_steps']
        steps.append(dict(steps[1]))
        steps[1]['focal'] = True
        steps[2]['title'] = '18,3% trong số'
        steps[0]['source_cell_ref'] = 'difficulties.csv!R3C2'
        errs = ' '.join(self.result(spec)['errors'])
        for msg in ('one to 3 numbers', 'at most one tile is `focal`', 'a tile shows one number', 'does not match source'):
            self.assertIn(msg, errs)
        spec = self.spec()
        self.tile_slide(spec)['word_jobs']['implementation_steps'][1].pop('source_cell_ref')
        self.assertIn('needs `source_cell_ref`', ' '.join(self.result(spec)['errors']))

    def test_side_image_and_spotlight_rules(self):
        from PIL import Image
        Image.new('RGB', (40, 30), '#888888').save(self.work / 'inputs/kitchen.png')
        spec = self.spec()
        slide = self.tile_slide(spec)
        slide['word_jobs']['side_image'] = {'path': 'kitchen.png', 'alt_text': 'Bếp trung tâm', 'referenced_in': 'speaker_notes'}
        res = self.result(spec)
        self.assertFalse([e for e in res['errors'] if 'D-064' in e])
        self.assertIn('referenced in the speaker notes, but the slide has none', ' '.join(res['warnings']))
        slide['word_jobs']['side_image'] = {'path': 'missing.png', 'alt_text': '', 'referenced_in': 'slide_text'}
        errs = ' '.join(self.result(spec)['errors'])
        self.assertIn('was not found in inputs/', errs)
        self.assertIn('`alt_text` is required', errs)
        spec = self.spec()
        self.tile_slide(spec)['layout_spec']['emphasis'] = 'spotlight'
        self.assertFalse([e for e in self.result(spec)['errors'] if 'D-064' in e])
        spec['slides'][0]['layout_spec']['emphasis'] = 'spotlight'
        errs = ' '.join(self.result(spec)['errors'])
        self.assertIn('only for big-number tile slides', errs)
        self.assertIn('keep one per deck', errs)
        self.assertGreaterEqual(validate_spec.contrast_ratio('#FFFFFF', pptx_renderer.spotlight_palette({'theme_palette': {'two_tier_accent': {'primary_focal_hex': '#D95F02', 'shaded_delta_fill_hex': '#FEE6CE'}}})['background']), 4.5)

    def test_renderers_draw_grid_tiles_image_and_spotlight(self):
        from PIL import Image
        from pptx import Presentation
        from pptx.util import Emu
        import html_renderer
        Image.new('RGB', (40, 30), '#888888').save(self.work / 'inputs/kitchen.png')
        spec = self.spec()
        slide_spec = self.tile_slide(spec)
        idx = spec['slides'].index(slide_spec)
        deck = pptx_renderer.compile_pptx(spec, self.work / 'output/t.pptx')
        slide = content_slides(deck)[idx]
        hero = next(sh for sh in slide.shapes if sh.name == 'pai:statement_hero')
        tiles = [sh for sh in slide.shapes if sh.name == 'pai:step']
        self.assertEqual(len(tiles), 3)
        self.assertEqual(hero.left + hero.width, tiles[1].left + tiles[1].width)  # D-064: the card ends on a grid line
        numbers = [t.text_frame.paragraphs[0] for t in tiles]
        self.assertEqual(numbers[0].font.size.pt, pptx_renderer.TYPE_SCALES['live']['tile_number'])
        focal = spec['deck_meta']['theme_palette']['two_tier_accent']['primary_focal_hex'].lstrip('#')
        self.assertEqual(str(numbers[0].font.color.rgb), focal)
        self.assertNotEqual(str(numbers[1].font.color.rgb), focal)
        # one tile sits beside the card; the side image takes that column on a card slide
        one = yaml.safe_load(yaml.safe_dump(spec))
        self.tile_slide(one)['word_jobs']['implementation_steps'] = self.tile_slide(one)['word_jobs']['implementation_steps'][:1]
        s1 = content_slides(pptx_renderer.compile_pptx(one, self.work / 'output/one.pptx'))[idx]
        h1 = next(sh for sh in s1.shapes if sh.name == 'pai:statement_hero')
        t1 = next(sh for sh in s1.shapes if sh.name == 'pai:step')
        self.assertEqual((t1.top, t1.height), (h1.top, h1.height))
        img = yaml.safe_load(yaml.safe_dump(spec))
        wj = self.tile_slide(img)['word_jobs']
        wj.pop('step_style')
        wj['side_image'] = {'path': 'kitchen.png', 'alt_text': 'Bếp trung tâm', 'referenced_in': 'slide_text'}
        s2 = content_slides(pptx_renderer.compile_pptx(img, self.work / 'output/img.pptx'))[idx]
        pic = next(sh for sh in s2.shapes if sh.name == 'pai:side_image')
        self.assertEqual(pic._element.find('.//{*}cNvPr').get('descr'), 'Bếp trung tâm')
        # spotlight: focal-colour background, white text, cards without fill
        spot = yaml.safe_load(yaml.safe_dump(spec))
        self.tile_slide(spot)['layout_spec']['emphasis'] = 'spotlight'
        s3 = content_slides(pptx_renderer.compile_pptx(spot, self.work / 'output/spot.pptx'))[idx]
        self.assertEqual(str(s3.background.fill.fore_color.rgb), pptx_renderer.spotlight_palette(spot['deck_meta'])['background'].lstrip('#'))
        colours = [str(f.color.rgb) for sh in s3.shapes if sh.has_text_frame for p in sh.text_frame.paragraphs for f in [p.font] + [r.font for r in p.runs] if f.color and f.color.type is not None]
        self.assertTrue(colours and set(colours) == {'FFFFFF'}, set(colours))
        self.assertTrue(all(sh.fill.type != MSO_FILL.SOLID for sh in s3.shapes if sh.name in ('pai:step', 'pai:statement_hero')))
        page = html_renderer.compile_html(spot, self.work / 'output/spot.html').read_text(encoding='utf-8')
        self.assertIn('class="tile-number focal"', page)
        self.assertIn(' spotlight', page)
        self.assertIn('grid-template-columns: repeat(3, 1fr)', page)
        page = html_renderer.compile_html(img, self.work / 'output/img.html').read_text(encoding='utf-8')
        self.assertIn('class="side-image"', page)
        self.assertEqual(len(html_renderer.export_slide_pngs(spot, self.work / 'png')), len(spec['slides']) + len(spec.get('appendix_slides') or []))


class ImageEvidence(CoffeeWorkspace, unittest.TestCase):
    """D-105: the image_evidence layout in the contract, validator and three renderers."""

    def result(self, spec):
        return validate_spec.validate_slide_spec_dict(spec, 't', self.work)

    def image_slide(self, spec, size=(1800, 1100)):
        from PIL import Image
        Image.new('RGB', size, '#888888').save(self.work / 'inputs/tracker.png')
        slide = next(s for s in spec['slides'] if (s.get('layout_spec') or {}).get('layout_type') == 'one_sided_right_text')
        slide.pop('visual_spec')
        slide['layout_spec']['layout_type'] = 'image_evidence'
        slide['image_spec'] = {'path': 'tracker.png', 'alt_text': 'Applicant tracker queue', 'referenced_in': 'slide_text', 'panel_title': 'Applicant tracker'}
        return slide

    def d105(self, res, key='errors'):
        return [m for m in res[key] if 'D-105' in m]

    def test_valid_slide_and_errors(self):
        spec = self.spec()
        self.image_slide(spec)
        res = self.result(spec)
        self.assertEqual(self.d105(res), [])
        self.assertEqual(self.d105(res, 'warnings'), [])
        spec = self.spec()
        slide = self.image_slide(spec)
        slide['image_spec'].update({'path': 'missing.gif', 'alt_text': ' ', 'panel_title': ''})
        errs = ' '.join(self.result(spec)['errors'])
        for msg in ('was not found in inputs/', '`alt_text` is required', '`panel_title` is required', 'is not a PNG or JPEG'):
            self.assertIn(msg, errs)
        spec = self.spec()
        slide = self.image_slide(spec)
        spec['slides'][-1]['image_spec'] = slide.pop('image_spec')
        slide['visual_spec'] = {'render_mode': 'native_editable_chart', 'panels': []}
        errs = ' '.join(self.result(spec)['errors'])
        self.assertIn('requires `image_spec`', errs)
        self.assertIn('carries `image_spec`, not `visual_spec`', errs)
        self.assertIn('`image_spec` belongs only on `image_evidence` slides', errs)

    def test_low_resolution_and_missing_cards_warn(self):
        spec = self.spec()
        slide = self.image_slide(spec, size=(600, 400))
        slide['word_jobs'].pop('annotations', None)
        slide['word_jobs'].pop('recommendation_callout', None)
        slide['image_spec']['referenced_in'] = 'speaker_notes'
        slide.pop('progressive_reveal', None)
        warns = ' '.join(self.d105(self.result(spec), 'warnings'))
        self.assertIn('dpi at its placed width', warns)
        self.assertIn('no finding or callout beside the image', warns)
        self.assertIn('referenced in the speaker notes, but the slide has none', warns)

    def test_renderers_draw_the_image(self):
        from pptx.util import Emu
        spec = self.spec()
        slide_spec = self.image_slide(spec)
        slide_spec['image_spec']['credit'] = 'Screenshot: Copperleaf HR.'
        idx = spec['slides'].index(slide_spec)
        deck = pptx_renderer.compile_pptx(spec, self.work / 'output/img.pptx')
        slide = content_slides(deck)[idx]
        pic = next(sh for sh in slide.shapes if sh.name == 'pai:image_evidence')
        self.assertEqual(pic._element.find('.//{*}cNvPr').get('descr'), 'Applicant tracker queue')
        self.assertAlmostEqual(Emu(pic.left).inches, 0.60, places=2)  # top-left of the chart area
        self.assertAlmostEqual(pic.width / pic.height, 1800 / 1100, places=2)  # fitted, not cropped
        self.assertEqual(pic.line.width.pt, 0.75)
        side = [sh for sh in slide.shapes if sh.left >= pic.left + pic.width and sh.has_text_frame and sh.name != 'pai:footer']
        self.assertTrue(side)
        self.assertFalse([sh for sh in slide.shapes if getattr(sh, 'has_chart', False) and sh.has_chart])
        source = next(sh for sh in slide.shapes if sh.name == 'pai:source_footnote').text_frame.text
        self.assertTrue(source.endswith('Screenshot: Copperleaf HR.'), source)
        page = html_renderer.compile_html(spec, self.work / 'output/img.html').read_text(encoding='utf-8')
        self.assertIn('class="evidence-image"', page)
        self.assertIn('layout-image_evidence', page)
        pngs = html_renderer.export_slide_pngs(spec, self.work / 'png')
        self.assertEqual(len(pngs), len(spec['slides']) + len(spec.get('appendix_slides') or []))


class ImageGrid(CoffeeWorkspace, unittest.TestCase):
    """D-105: the image_grid layout in the contract, validator and three renderers."""

    def result(self, spec):
        return validate_spec.validate_slide_spec_dict(spec, 't', self.work)

    def grid_slide(self, spec, n=3, size=(1600, 1000)):
        from PIL import Image
        slide = next(s for s in spec['slides'] if (s.get('layout_spec') or {}).get('layout_type') == 'one_sided_right_text')
        slide.pop('visual_spec')
        slide['layout_spec']['layout_type'] = 'image_grid'
        names = ['Mint Chill Cold Brew', 'Hazelnut Cloud Mocha', 'Espresso Tonic', 'Maple Oat Latte']
        slide['image_panels'] = []
        for i in range(n):
            Image.new('RGB', size, '#888888').save(self.work / f'inputs/drink{i}.png')
            slide['image_panels'].append({'path': f'drink{i}.png', 'alt_text': names[i], 'panel_title': names[i], 'caption': 'Sold in every store'})
        slide['image_panels'][0]['focal'] = True
        return slide

    def d105(self, res, key='errors'):
        return [m for m in res[key] if 'D-105' in m]

    def test_valid_grid_and_errors(self):
        spec = self.spec()
        self.grid_slide(spec)
        res = self.result(spec)
        self.assertEqual(self.d105(res), [])
        self.assertEqual(self.d105(res, 'warnings'), [])
        spec = self.spec()
        slide = self.grid_slide(spec, n=4)
        slide['image_panels'][1].update({'focal': True, 'path': 'nope.gif', 'caption': 'Fell 14% in the year, far more than every other drink on the menu'})
        slide['image_panels'][2]['panel_title'] = ''
        errs = ' '.join(self.result(spec)['errors'])
        for msg in ('at most one image panel is `focal`', 'is not a PNG or JPEG', 'was not found in inputs/', '`panel_title` is required', 'the caption must stay short', "shows '14%'; add `source_cell_ref`"):
            self.assertIn(msg, errs)
        spec = self.spec()
        slide = self.grid_slide(spec)
        spec['slides'][-1]['image_panels'] = slide.pop('image_panels')
        errs = ' '.join(self.result(spec)['errors'])
        self.assertIn('shows 2-4 images (found 0)', errs)
        self.assertIn('`image_panels` belong only on `image_grid` slides', errs)

    def test_shape_and_resolution_warnings(self):
        from PIL import Image
        spec = self.spec()
        slide = self.grid_slide(spec, size=(500, 400))
        Image.new('RGB', (1600, 600), '#888888').save(self.work / 'inputs/drink2.png')
        for p in slide['image_panels']:
            p.pop('focal', None)
        slide['word_jobs']['takeaway_title']['color_tie_spans'] = [{'substring': slide['word_jobs']['takeaway_title']['text'].split()[0], 'color_hex': '#D95F02', 'linked_series_or_category': 'focal series'}]
        warns = ' '.join(self.d105(self.result(spec), 'warnings'))
        self.assertIn('dpi at its placed width', warns)
        self.assertIn('differ in shape by more than 15 %', warns)
        self.assertIn('no image panel is `focal`', warns)

    def test_renderers_draw_the_grid(self):
        from pptx.util import Emu
        for n in (3, 4):
            spec = self.spec()
            slide_spec = self.grid_slide(spec, n=n)
            idx = spec['slides'].index(slide_spec)
            slide = content_slides(pptx_renderer.compile_pptx(spec, self.work / f'output/grid{n}.pptx'))[idx]
            pics = [sh for sh in slide.shapes if sh.name == 'pai:image_evidence']
            self.assertEqual(len(pics), n)
            self.assertEqual(len({(p.width, p.height) for p in pics}), 1)  # equal panels
            self.assertAlmostEqual(Emu(pics[0].left).inches, 0.60, places=2)
            caps = [sh for sh in slide.shapes if sh.name == 'pai:image_caption']
            self.assertEqual(len({c.top for c in caps}), 2 if n == 4 else 1)  # one caption line per row
            focal = pptx_renderer.readable_text_hex(spec['deck_meta']['theme_palette']['two_tier_accent']['primary_focal_hex'], '#FFFFFF', 4.5).lstrip('#')
            self.assertEqual(str(caps[0].text_frame.paragraphs[0].font.color.rgb), focal)
            self.assertNotEqual(str(caps[1].text_frame.paragraphs[0].font.color.rgb), focal)
            cards = [sh for sh in slide.shapes if sh.has_text_frame and sh.name not in ('pai:image_caption', 'pai:panel_title') and sh.top > pics[0].top and sh.top < Emu(int(6.8 * 914400))]
            if n == 4:  # cards beside the 2 x 2 grid
                self.assertTrue(all(c.left >= pics[1].left + pics[1].width for c in cards), [c.name for c in cards])
            else:  # cards in the bottom strip
                self.assertTrue(all(c.top >= caps[0].top + caps[0].height for c in cards), [c.name for c in cards])
            page = html_renderer.compile_html(spec, self.work / f'output/grid{n}.html').read_text(encoding='utf-8')
            self.assertEqual(page.count('class="evidence-image"'), n)
            self.assertIn('class="image-caption focal"', page)
        self.assertEqual(len(html_renderer.export_slide_pngs(spec, self.work / 'png')), len(spec['slides']) + len(spec.get('appendix_slides') or []))



class QuoteEvidence(CoffeeWorkspace, unittest.TestCase):
    """D-105 / D-108: the quote_evidence layout in the contract, validator and three renderers."""

    COMMENTS = [
        'I passed the interview, then heard nothing about a trial shift for over a week. By then I had taken another job.',
        'The hourly rate in the offer was lower than the café across the street pays.',
        'They could only offer early mornings, and I have classes until ten.',
    ]

    def result(self, spec):
        return validate_spec.validate_slide_spec_dict(spec, 't', self.work)

    def quote_slide(self, spec, n=3):
        import csv
        with (self.work / 'inputs/quotes.csv').open('w', encoding='utf-8', newline='') as fh:
            w = csv.writer(fh)
            w.writerow(['id', 'store', 'comment'])
            for i, c in enumerate(self.COMMENTS):
                w.writerow([f'W{i}', 'Harbor Street', c])
        with (self.work / 'inputs/reasons.csv').open('w', encoding='utf-8', newline='') as fh:
            fh.write('reason,applicants\nWaited,14\nPay,9\nHours,7\n')
        slide = next(s for s in spec['slides'] if (s.get('layout_spec') or {}).get('layout_type') == 'one_sided_right_text')
        slide.pop('visual_spec')
        slide['layout_spec']['layout_type'] = 'quote_evidence'
        texts = ['I passed the interview, then heard nothing about a trial shift for over a week… I had taken another job.', self.COMMENTS[1], self.COMMENTS[2]]
        slide['quotes'] = [
            {'text': texts[i], 'speaker': 'Barista applicant, Harbor Street', 'source_ref': f'quotes.csv!R{i + 2}C3',
             'group_label': f'Reason {i + 1}: {(14, 9, 7)[i]} applicants', 'count_ref': f'reasons.csv!R{i + 2}C2'}
            for i in range(n)
        ]
        slide['quotes'][0]['focal'] = True
        return slide

    def d108(self, res, key='errors'):
        return [m for m in res[key] if 'D-108' in m or 'D-105' in m]

    def test_valid_quotes_and_errors(self):
        for n in (1, 3):
            spec = self.spec()
            self.quote_slide(spec, n=n)
            res = self.result(spec)
            self.assertEqual(self.d108(res), [])
            self.assertEqual(self.d108(res, 'warnings'), [])
        spec = self.spec()
        slide = self.quote_slide(spec)
        slide['quotes'][1].update({'focal': True, 'text': 'The hourly rate was lower than the café across the street.'})
        slide['quotes'][2].update({'speaker': '', 'count_ref': 'reasons.csv!R2C2'})
        slide['quotes'][0]['count_ref'] = ''
        slide['quotes'][0]['color_tie_spans'] = [{'substring': 'trial shift', 'color_hex': '#D95F02', 'linked_series_or_category': 'focal'}]
        slide['quotes'][1]['color_tie_spans'] = [{'substring': 'no such words', 'color_hex': '#D95F02', 'linked_series_or_category': 'focal'}]
        errs = ' '.join(self.result(spec)['errors'])
        for msg in ('at most one quote is `focal`', 'is not verbatim', '`speaker` is required', "shows '1', '14'; add `count_ref`",
                    'at most one Color Tie span across the quotes', 'is not an exact substring of the quote', 'does not match source'):
            self.assertIn(msg, errs)
        spec = self.spec()
        slide = self.quote_slide(spec)
        slide['quotes'][1]['text'] = ' '.join(['word'] * 21)
        slide['quotes'][2]['source_ref'] = 'quotes.csv!R2C3:R3C3'
        spec['slides'][-1]['quotes'] = [dict(slide['quotes'][0])]
        errs = ' '.join(self.result(spec)['errors'])
        self.assertIn('the quote must stay short (<= 20 words', errs)
        self.assertIn('a quote cites one CSV cell', errs)
        self.assertIn('`quotes` belong only on `quote_evidence` slides', errs)
        spec = self.spec()
        slide = self.quote_slide(spec)
        slide['quotes'] = slide['quotes'] * 2
        self.assertIn('shows 1-3 quotes (found 6)', ' '.join(self.result(spec)['errors']))

    def test_warnings(self):
        spec = self.spec()
        slide = self.quote_slide(spec)
        slide['quotes'][0].pop('focal')
        slide['quotes'][1]['speaker'] = 'Maria Lopez, Union Square'
        slide['quotes'][2]['text'] = '"' + slide['quotes'][2]['text'] + '"'
        slide['word_jobs']['takeaway_title']['color_tie_spans'] = [{'substring': slide['word_jobs']['takeaway_title']['text'].split()[0], 'color_hex': '#D95F02', 'linked_series_or_category': 'focal series'}]
        warns = ' '.join(self.d108(self.result(spec), 'warnings'))
        self.assertIn('looks like a personal name', warns)
        self.assertIn('drop the quotation marks', warns)
        self.assertIn('no quote is `focal`', warns)
        self.assertTrue(validate_spec.quote_is_verbatim('the trainer came… five days later', 'The trainer came only five days later.'))
        self.assertFalse(validate_spec.quote_is_verbatim('five days later… the trainer came', 'The trainer came only five days later.'))

    def test_renderers_draw_the_quotes(self):
        from pptx.util import Emu
        for n in (1, 3):
            spec = self.spec()
            slide_spec = self.quote_slide(spec, n=n)
            idx = spec['slides'].index(slide_spec)
            slide = content_slides(pptx_renderer.compile_pptx(spec, self.work / f'output/quotes{n}.pptx'))[idx]
            boxes = [sh for sh in slide.shapes if sh.name == 'pai:quote_text']
            self.assertEqual(len(boxes), n)
            self.assertAlmostEqual(Emu(boxes[0].left).inches, 0.65, places=2)
            first = boxes[0].text_frame.paragraphs[0].text
            self.assertTrue(first.startswith('\u201c') and first.endswith('\u201d'), first)
            self.assertEqual(boxes[0].text_frame.paragraphs[1].text, 'Barista applicant, Harbor Street')
            rules = [sh for sh in slide.shapes if sh.name == 'pai:quote_rule']
            self.assertEqual(len(rules), n)
            self.assertEqual(rules[0].line.width, pptx_renderer.Pt(1.5))
            cards = [sh for sh in slide.shapes if sh.has_text_frame and not sh.name.startswith('pai:quote') and sh.top > boxes[0].top and sh.top < Emu(int(6.8 * 914400))]
            if n == 1:  # cards beside the quote
                self.assertTrue(cards and all(c.left >= boxes[0].left + boxes[0].width for c in cards), [c.name for c in cards])
            else:  # cards in the bottom strip, columns of equal width
                self.assertEqual(len({b.width for b in boxes}), 1)
                self.assertTrue(cards and all(c.top >= boxes[0].top + boxes[0].height for c in cards), [c.name for c in cards])
            page = html_renderer.compile_html(spec, self.work / f'output/quotes{n}.html').read_text(encoding='utf-8')
            self.assertEqual(page.count('<blockquote class="quote-text">'), n)
            self.assertIn('class="quote-rule focal"', page)
            self.assertEqual(len(html_renderer.export_slide_pngs(spec, self.work / f'png{n}')), len(spec['slides']) + len(spec.get('appendix_slides') or []))

class ScatterPlots(CoffeeWorkspace, unittest.TestCase):
    """D-065 / PAT-VIS-010: scatter contract, validator rules and the three renderers."""

    def result(self, spec):
        return validate_spec.validate_slide_spec_dict(spec, 't', self.work)

    def scatter(self, spec):
        slide = next(s for s in spec.get('appendix_slides') or [] if (s.get('visual_spec') or {}).get('panels', [{}])[0].get('chart_family') == 'scatter_plot')
        return slide, slide['visual_spec']['panels'][0]

    def test_validator_rules(self):
        self.assertFalse([e for e in self.result(self.spec())['errors'] if 'D-065' in e])
        spec = self.spec()
        slide, panel = self.scatter(spec)
        dp = panel['series'][0]['data_points'][0]
        dp.pop('x_source_cell_ref')
        panel['series'][1]['data_points'][0]['x_value'] = 9.5
        panel['trend_line'] = 'linear'
        panel['reference_lines'] = [{'axis': 'x', 'value': 5}, {'axis': 'x', 'value': 6}]
        panel['section_labels'][0]['text'] = 'Stores with waits over five minutes'
        panel['y_axis']['min'], panel['y_axis']['max'] = -5, 5
        errs = ' '.join(self.result(spec)['errors'])
        for msg in ('`x_source_cell_ref` is missing', 'lies outside the axes', 'needs `trend_reason`', 'one reference line per axis',
                    'must be at most 4 words', 'tick labels would print rounded'):
            self.assertIn(msg, errs)
        spec = self.spec()
        slide, panel = self.scatter(spec)
        panel['series'][1]['data_points'][1]['x_value'] = 6.4
        self.assertIn('does not match source', ' '.join(self.result(spec)['errors']))
        spec = self.spec()
        slide, _ = self.scatter(spec)
        slide['word_jobs']['takeaway_title']['text'] = 'Long waits cause the three stores to lose sales.'
        self.assertIn('reads as causal on a scatter plot', ' '.join(self.result(spec)['warnings']))
        spec = self.spec()
        spec['slides'][0]['visual_spec']['panels'][0]['trend_line'] = 'linear'
        self.assertIn('apply only to `scatter_plot`', ' '.join(self.result(spec)['errors']))

    def test_renderers(self):
        from pptx import Presentation
        import html_renderer
        spec = self.spec()
        slide_spec, panel = self.scatter(spec)
        idx = len(spec['slides']) + (spec.get('appendix_slides') or []).index(slide_spec)
        deck = pptx_renderer.compile_pptx(spec, self.work / 'output/s.pptx')
        slide = content_slides(deck)[idx]
        chart = next(sh.chart for sh in slide.shapes if getattr(sh, 'has_chart', False) and sh.has_chart)
        self.assertEqual(str(chart.chart_type), 'XY_SCATTER (-4169)')
        series = list(chart.plots[0].series)
        self.assertEqual(len(series), 3)  # two groups and the reference line
        focal = series[1]
        self.assertEqual([p.data_label.text_frame.text for p in focal.points], ['Harbor Street', 'Union Square', 'Riverside'])
        self.assertFalse(series[0].points[0].data_label.has_text_frame)  # 2A: context points stay unlabelled
        labels = [sh for sh in slide.shapes if sh.name == 'pai:label']
        self.assertEqual(len(labels), 2)
        accent = spec['deck_meta']['theme_palette']['two_tier_accent']['primary_focal_hex'].lstrip('#')
        over = next(l for l in labels if 'over' in l.text_frame.text)
        self.assertEqual(str(over.text_frame.paragraphs[0].font.color.rgb), accent)
        panel['trend_line'], panel['trend_reason'] = 'linear', 'The audience asked whether the pattern holds across all eight stores.'
        deck = pptx_renderer.compile_pptx(spec, self.work / 'output/t.pptx')
        chart = next(sh.chart for sh in content_slides(deck)[idx].shapes if getattr(sh, 'has_chart', False) and sh.has_chart)
        self.assertEqual(len(chart._chartSpace.xpath('.//c:trendline')), 1)
        page = html_renderer.compile_html(spec, self.work / 'output/s.html').read_text(encoding='utf-8')
        self.assertIn('stroke-dasharray="6 4"', page)
        self.assertIn('Waits over 5 min', page)
        self.assertEqual(len(html_renderer.export_slide_pngs(spec, self.work / 'png')), len(spec['slides']) + len(spec['appendix_slides']))


class StripPlots(CoffeeWorkspace, unittest.TestCase):
    """D-086 / PAT-VIS-013: strip plot contract, validator rules, packing model and the three renderers."""

    def result(self, spec):
        return validate_spec.validate_slide_spec_dict(spec, 't', self.work)

    def strip(self, spec):
        slide = next(s for s in spec.get('appendix_slides') or [] if (s.get('visual_spec') or {}).get('panels', [{}])[0].get('chart_family') == 'strip_plot')
        return slide, slide['visual_spec']['panels'][0]

    def test_validator_rules(self):
        res = self.result(self.spec())
        self.assertFalse([m for m in res['errors'] + res['warnings'] if 'D-086' in m])
        spec = self.spec()
        slide, panel = self.strip(spec)
        focal = panel['series'][1]
        focal['data_points'] = focal['data_points'][:2]
        panel['series'][0]['data_points'][0]['value'] = 13.0
        panel['highlight_band_label'] = 'The slowest fifth of stores'
        errs = ' '.join(self.result(spec)['errors'])
        for msg in ('exactly one dot in every row', 'lies outside the axis', 'at most 3 words'):
            self.assertIn(msg, errs)
        spec = self.spec()
        slide, panel = self.strip(spec)
        slide['word_jobs']['takeaway_title']['text'] = 'Harbor Street has longer waits than most stores.'
        panel['series'][0]['data_points'] = [dp for dp in panel['series'][0]['data_points'] if dp['category'] != 'Evening'][:-40] + \
            [dp for dp in panel['series'][0]['data_points'] if dp['category'] == 'Evening']
        warns = ' '.join(self.result(spec)['warnings'])
        self.assertIn('the title names no fifth', warns)
        self.assertIn('items; with fewer than 15', warns)
        spec = self.spec()
        spec['slides'][0]['visual_spec']['panels'][0]['highlight_band'] = 'top_fifth'
        self.assertIn('apply only to `strip_plot`', ' '.join(self.result(spec)['errors']))

    def test_model(self):
        _, panel = self.strip(self.spec())
        model = pptx_renderer.strip_model(panel, 6.0, 4.5, 0.0, 12.0)
        self.assertEqual([r['row'] for r in model['rows']], ['Morning rush', 'Midday', 'Evening'])
        for r in model['rows']:
            focal = [d for d in r['dots'] if d['focal']]
            self.assertEqual(len(focal), 1)
            self.assertEqual(focal[0]['offset'], 0.0)  # the focal dot sits on the row's centre line
            self.assertEqual(len(r['dots']), 48)
            self.assertLessEqual(r['focal'][0]['rank'], 9)  # the title: inside the slowest fifth of 48
            b0, b1 = r['band']
            self.assertTrue(b0 <= r['focal'][0]['value'] <= b1)
            # no two context dots overlap
            dx = pptx_renderer.STRIP_CONTEXT_PT / 72.0 / 6.0 * 12.0
            dy = pptx_renderer.STRIP_CONTEXT_PT / 72.0 / 1.5
            pts = [(d['value'], d['offset']) for d in r['dots']]
            clashes = sum(1 for i, a in enumerate(pts) for b in pts[i + 1:] if abs(a[0] - b[0]) < dx * 0.99 and abs(a[1] - b[1]) < dy * 0.99)
            self.assertEqual(clashes, 0)
        self.assertEqual(pptx_renderer.strip_model(panel, 6.0, 4.5, 0.0, 12.0)['rows'][0]['dots'][5]['offset'], model['rows'][0]['dots'][5]['offset'])

    def test_renderers(self):
        import html_renderer
        spec = self.spec()
        slide_spec, panel = self.strip(spec)
        idx = len(spec['slides']) + (spec.get('appendix_slides') or []).index(slide_spec)
        deck = pptx_renderer.compile_pptx(spec, self.work / 'output/s.pptx')
        slide = content_slides(deck)[idx]
        chart = next(sh.chart for sh in slide.shapes if getattr(sh, 'has_chart', False) and sh.has_chart)
        self.assertEqual(str(chart.chart_type), 'XY_SCATTER (-4169)')
        series = list(chart.plots[0].series)
        self.assertEqual(len(series), 5)  # context, focal and one median tick per row
        self.assertEqual(len(list(series[1].points)), 3)
        names = [sh.name for sh in slide.shapes]
        self.assertEqual(names.count('pai:strip_band'), 3)
        self.assertLess(names.index('pai:strip_band'), next(i for i, sh in enumerate(slide.shapes) if getattr(sh, 'has_chart', False) and sh.has_chart))
        values = [sh.text_frame.text for sh in slide.shapes if sh.name == 'pai:strip_value']
        self.assertEqual(values, ['9.1 min · rank 7', '6.1 min · rank 6', '5.3 min · rank 7'])
        lefts = {round(sh.left / 914400, 3) for sh in slide.shapes if sh.name == 'pai:strip_value'}
        self.assertEqual(len(lefts), 1)  # one aligned column
        self.assertIn('Slowest fifth', [sh.text_frame.text for sh in slide.shapes if sh.name == 'pai:strip_band_name'])
        page = html_renderer.compile_html(spec, self.work / 'output/s.html').read_text(encoding='utf-8')
        self.assertEqual(page.count('class="strip-band"'), 3)
        self.assertEqual(page.count('strip-focal'), 3)
        self.assertIn('9.1 min · rank 7', page)
        self.assertEqual(len(html_renderer.export_slide_pngs(spec, self.work / 'png')), len(spec['slides']) + len(spec['appendix_slides']))


class TimeAxes(CoffeeWorkspace, unittest.TestCase):
    """D-087 / ANTI-VIS-005: uneven year gaps and month ticks without a year."""

    def result(self, spec):
        return validate_spec.validate_slide_spec_dict(spec, 't', self.work)

    def line_panel(self, spec):
        for s in spec['slides'] + (spec.get('appendix_slides') or []):
            for p in (s.get('visual_spec') or {}).get('panels') or []:
                if p.get('chart_family') == 'line_chart':
                    return s, p
        raise AssertionError('no line chart in the coffee benchmark')

    def relabel(self, panel, cats):
        old = panel['x_axis']['categories'][:len(cats)]
        panel['x_axis']['categories'] = cats
        for ser in panel['series']:
            ser['data_points'] = [dict(dp, category=cats[old.index(dp['category'])]) for dp in ser['data_points'] if dp['category'] in old]

    def test_rules(self):
        self.assertFalse([w for w in self.result(self.spec())['warnings'] if 'ANTI-VIS-005' in w])
        spec = self.spec()
        slide, panel = self.line_panel(spec)
        self.relabel(panel, ['1990', '2000', '2010', '2015', '2020'])
        self.assertIn('unequal gaps', ' '.join(self.result(spec)['warnings']))
        panel['time_spacing_reason'] = 'Only census years are reported.'
        self.assertNotIn('unequal gaps', ' '.join(self.result(spec)['warnings']))
        spec = self.spec()
        slide, panel = self.line_panel(spec)
        self.relabel(panel, ['4 Feb', '20 Jun', '4 Nov', '21 Mar'])
        slide['word_jobs']['chart_title'] = 'Orders per day'
        panel['panel_chart_title'] = 'All stores'
        slide['word_jobs']['source_footnote'] = 'Source: store tills.'
        self.assertIn('no year', ' '.join(self.result(spec)['warnings']))
        slide['word_jobs']['chart_title'] = 'Orders per day, 2025'
        self.assertNotIn('no year', ' '.join(self.result(spec)['warnings']))


class EqualLineAndSideTotals(CoffeeWorkspace, unittest.TestCase):
    """D-088: the y = x equal-change line on scatter plots and side-total brackets on diverging stacks."""
    VI = ROOT / '50_evals/runs/bench_vi_briefing_no_ask'

    def result(self, spec, work=None):
        return validate_spec.validate_slide_spec_dict(spec, 't', work or self.work)

    def scatter(self, spec):
        slide = next(s for s in spec.get('appendix_slides') or [] if (s.get('visual_spec') or {}).get('panels', [{}])[0].get('chart_family') == 'scatter_plot')
        return slide, slide['visual_spec']['panels'][0]

    def same_unit(self, panel):
        panel['x_axis'].update(min=-6, max=8, number_format='0')
        panel['y_axis'].update(min=-6, max=8, number_format='0')
        panel['reference_lines'] = [{'axis': 'diagonal', 'label': 'Equal'}]
        panel['section_labels'] = []

    def test_diagonal_rules_and_render(self):
        import html_renderer
        spec = self.spec()
        slide, panel = self.scatter(spec)
        panel['reference_lines'] = [{'axis': 'diagonal'}]
        self.assertIn('same range and number format', ' '.join(self.result(spec)['errors']))
        spec = self.spec()
        slide, panel = self.scatter(spec)
        self.same_unit(panel)
        self.assertFalse([e for e in self.result(spec)['errors'] if 'D-088' in e or 'reference line' in e])
        idx = len(spec['slides']) + spec['appendix_slides'].index(slide)
        deck = pptx_renderer.compile_pptx(spec, self.work / 'output/d.pptx')
        sl = content_slides(deck)[idx]
        chart = next(sh.chart for sh in sl.shapes if getattr(sh, 'has_chart', False) and sh.has_chart)
        ref = list(chart.plots[0].series)[2]
        xs = [float(v) for v in ref._element.xpath('./c:xVal//c:v/text()')]
        ys = [float(v) for v in ref._element.xpath('./c:yVal//c:v/text()')]
        self.assertEqual(xs, ys)
        self.assertEqual((xs[0], xs[-1]), (-6.0, 8.0))
        self.assertIn('Equal', [sh.text_frame.text for sh in sl.shapes if sh.name == 'pai:diagonal_label'])
        mini = {'reference_lines': [{'axis': 'diagonal'}]}
        groups = [{'visual_role': 'focal_primary_tier1', 'data_points': [{'x_value': 6, 'value': 2}, {'x_value': 5, 'value': 4}]},
                  {'visual_role': 'context_greyscale', 'data_points': [{'x_value': 2, 'value': 6}, {'x_value': 1, 'value': 3}]}]
        self.assertTrue(pptx_renderer.scatter_section_is_focal(mini, groups, 7.0, 1.0))  # below y = x
        self.assertFalse(pptx_renderer.scatter_section_is_focal(mini, groups, 1.0, 7.0))  # above y = x
        page = html_renderer.compile_html(spec, self.work / 'output/d.html').read_text(encoding='utf-8')
        self.assertIn('class="diagonal-label"', page)

    def test_side_totals(self):
        import html_renderer
        spec = yaml.safe_load((self.VI / 'artifacts/slide_spec.yaml').read_text(encoding='utf-8'))
        slide = next(s for s in spec['slides'] + (spec.get('appendix_slides') or [])
                     if any(p.get('side_totals') == 'brackets' for p in (s.get('visual_spec') or {}).get('panels') or []))
        panel = slide['visual_spec']['panels'][0]
        model = pptx_renderer.side_totals_model(panel, panel['series'], panel['x_axis']['categories'], '#FFFFFF')
        self.assertEqual([[round(t) for _, _, t, _ in row] for row in model], [[42, 27], [31, 35], [22, 50]])
        self.assertTrue(all(lo < hi for row in model for lo, hi, _, _ in row))
        idx = (spec['slides'] + (spec.get('appendix_slides') or [])).index(slide)
        deck = pptx_renderer.compile_pptx(spec, self.work / 'output/v.pptx')
        sl = content_slides(deck)[idx]
        self.assertEqual([sh.text_frame.text for sh in sl.shapes if sh.name == 'pai:side_total'], ['42', '27', '31', '35', '22', '50'])
        self.assertEqual(sum(1 for sh in sl.shapes if sh.name == 'pai:side_bracket'), 18)
        page = html_renderer.compile_html(spec, self.work / 'output/v.html').read_text(encoding='utf-8')
        self.assertEqual(page.count('class="side-total"'), 6)
        panel['orientation'] = 'vertical'
        self.assertIn('only to horizontal diverging stacks', ' '.join(self.result(spec, self.VI)['errors']))


class SideColumn(unittest.TestCase):
    """D-095: a side column of changes beside a horizontal bar chart (showcase slide 3, right panel)."""
    RUN = ROOT / '50_evals/runs/showcase_en_coffee_editorial'

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='pai_d095_')
        self.addCleanup(self.tmp.cleanup)
        self.work = Path(self.tmp.name) / 'ws'
        shutil.copytree(self.RUN, self.work)
        self.output = contextlib.redirect_stdout(io.StringIO())
        self.output.__enter__()
        self.addCleanup(self.output.__exit__, None, None, None)
        self.spec = yaml.safe_load((self.work / 'artifacts/slide_spec.yaml').read_text(encoding='utf-8'))
        self.idx = next(i for i, sl in enumerate(self.spec['slides']) if any(p.get('side_column') for p in sl['visual_spec']['panels']))
        self.panel = next(p for p in self.spec['slides'][self.idx]['visual_spec']['panels'] if p.get('side_column'))

    def errors(self):
        return validate_spec.validate_slide_spec_dict(self.spec, 't', self.work)['errors']

    def test_text_and_rows(self):
        self.assertEqual([pptx_renderer.side_column_text(v, 'en') for v in (-22, -0.5, 3, 0)], ['−22', '−0.5', '+3', '0'])
        self.assertEqual(pptx_renderer.side_column_text(-0.5, 'vi'), '−0,5')
        model = pptx_renderer.side_column_model(self.panel, self.panel['x_axis']['categories'], '#FFFFFF', 'en')
        self.assertEqual(model['title'], 'Against plan')
        self.assertEqual([r[0] for r in model['rows']], ['−22', '−2', '−6', '0'])
        self.assertEqual([r[2] for r in model['rows']], [True, False, False, False])  # only the focal bar's row is bold
        self.assertIsNotNone(model['rows'][0][1])
        self.assertTrue(all(r[1] is None for r in model['rows'][1:]))
        self.assertIsNone(pptx_renderer.side_column_model({**self.panel, 'chart_family': 'vertical_bar_chart'}, [], '#FFFFFF', 'en'))

    def test_renderers_draw_one_row_per_bar(self):
        import html_renderer
        deck = pptx_renderer.compile_pptx(self.spec, self.work / 'output/s.pptx')
        sl = content_slides(deck)[self.idx]
        rows = sorted((sh for sh in sl.shapes if sh.name == 'pai:side_column'), key=lambda sh: sh.top)
        self.assertEqual([sh.text_frame.text for sh in rows], ['−22', '−2', '−6', '0'])
        self.assertEqual([sh.text_frame.text for sh in sl.shapes if sh.name == 'pai:side_column_title'], ['Against plan'])
        gaps = [b.top - a.top for a, b in zip(rows, rows[1:])]
        self.assertLess(max(gaps) - min(gaps), 3000)  # rows keep one spacing, the bars' band
        chart = next(sh for sh in sl.shapes if getattr(sh, 'has_chart', False) and sh.top < rows[0].top < sh.top + sh.height)
        self.assertGreaterEqual(rows[0].left, chart.left + chart.width * 0.6)  # in the strip right of the plot
        page = html_renderer.compile_html(self.spec, self.work / 'output/s.html').read_text(encoding='utf-8')
        self.assertEqual(page.count('class="side-column"'), 4)
        self.assertEqual(page.count('class="side-column-title"'), 1)

    def test_validator(self):
        self.assertEqual(self.errors(), [])
        self.panel['chart_family'] = 'vertical_bar_chart'
        self.assertIn('applies only to `horizontal_bar_chart`', ' '.join(self.errors()))
        self.panel['chart_family'] = 'horizontal_bar_chart'
        self.panel['side_column']['data_points'].pop()
        self.assertIn('each category of `x_axis.categories` exactly once', ' '.join(self.errors()))
        self.panel['side_column']['data_points'].append({'category': 'Bakers', 'value': 5.0, 'source_cell_ref': 'roles.csv!R5C3,R5C2', 'aggregation': 'diff'})
        self.assertIn('does not match source', ' '.join(self.errors()))  # 5 is not 60 - 60: the column is traced
        self.panel['side_column']['data_points'][-1]['value'] = 0.0
        self.panel['side_column']['title'] = ' '
        self.assertIn('must name the reference and unit', ' '.join(self.errors()))


class PillowPanelFindings(unittest.TestCase):
    """Pillow previews draw each panel's finding above its chart on paired slides (BACKLOG, D-075)."""
    RUN = ROOT / '50_evals/runs/showcase_en_coffee_editorial'

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='pai_pvf_')
        self.addCleanup(self.tmp.cleanup)
        self.work = Path(self.tmp.name)
        self.output = contextlib.redirect_stdout(io.StringIO())
        self.output.__enter__()
        self.addCleanup(self.output.__exit__, None, None, None)

    def drawn_texts(self, spec, name):
        import html_renderer
        seen, real = [], html_renderer.draw_colored_paragraph_pil

        def spy(draw, **kw):
            seen.append(str(kw.get('text', '')))
            return real(draw, **kw)
        html_renderer.draw_colored_paragraph_pil = spy
        try:
            html_renderer.export_slide_pngs(spec, self.work / name)
        finally:
            html_renderer.draw_colored_paragraph_pil = real
        return seen

    def test_headline_and_text_are_drawn(self):
        spec = yaml.safe_load((self.RUN / 'artifacts/slide_spec.yaml').read_text(encoding='utf-8'))
        paired = next(sl for sl in spec['slides'] if sl['layout_spec']['layout_type'] == 'two_sided_paired_views')
        panels = paired['visual_spec']['panels']
        heads = [p['panel_headline']['text'] for p in panels]
        bodies = [p['panel_text'] for p in panels]
        drawn = self.drawn_texts(spec, 'a')
        for text in heads + bodies:  # the coffee deck is standalone, so the short text shows too
            self.assertIn(text, drawn)
        spec['deck_meta']['delivery_mode'] = 'live'
        live = self.drawn_texts(spec, 'b')
        self.assertTrue(all(h in live for h in heads))
        self.assertFalse(any(b in live for b in bodies))  # a live talk keeps the text in the speaker notes
        for p in panels:
            p.pop('panel_headline'), p.pop('panel_text')
        bare = self.drawn_texts(spec, 'c')
        self.assertFalse(any(t in bare for t in heads + bodies))


class EditorialTemplate(CoffeeWorkspace, unittest.TestCase):
    """D-089 (Editorial step 4): the generated template and the doctor font check."""

    def build(self, editorial):
        spec = self.spec()
        if editorial:
            spec['deck_meta']['design_system'] = 'editorial'
        from pptx import Presentation
        path = pptx_renderer.compile_pptx(spec, self.work / f'output/t_{int(editorial)}.pptx')
        return spec, Presentation(str(path))

    def theme(self, prs):
        return prs.slide_master.part.part_related_by(pptx_renderer.RT.THEME).blob.decode('utf-8')

    def test_editorial_template(self):
        spec, prs = self.build(True)
        self.assertEqual([l.name for l in prs.slide_layouts], ['Title', 'Content', 'Section Divider', 'Closing'])
        theme = self.theme(prs)
        self.assertIn('<a:majorFont><a:latin typeface="Aptos Display"', theme)
        self.assertIn('<a:minorFont><a:latin typeface="Aptos"', theme)
        self.assertIn('<a:dk1><a:srgbClr val="18202B"/>', theme)
        focal = spec['deck_meta']['theme_palette']['two_tier_accent']['primary_focal_hex'].lstrip('#').upper()
        self.assertIn(f'<a:accent1><a:srgbClr val="{focal}"/>', theme)
        names = [s.slide_layout.name for s in prs.slides]
        self.assertEqual(names[0], 'Title')
        self.assertEqual(names[len(spec['slides'])], 'Closing')  # slide 0 is the title slide
        self.assertTrue(all(n == 'Content' for n in names[1:len(spec['slides'])]))
        self.assertTrue(all(s.shapes.title is not None for s in prs.slides))  # every layout keeps the title placeholder

    def test_brand_font_and_classic(self):
        spec = self.spec()
        spec['deck_meta']['design_system'] = 'editorial'
        spec['deck_meta']['typography'] = {'font_family': 'Arial'}
        from pptx import Presentation
        prs = Presentation(str(pptx_renderer.compile_pptx(spec, self.work / 'output/b.pptx')))
        self.assertIn('<a:minorFont><a:latin typeface="Arial"', self.theme(prs))
        _, prs = self.build(False)
        self.assertIn('Title Only', [l.name for l in prs.slide_layouts])
        self.assertIn('typeface="Calibri"', self.theme(prs))

    def test_html_tick_labels_use_chart_text(self):
        spec = self.spec()
        classic = html_renderer.compile_html(spec, self.work / 'output/c.html').read_text(encoding='utf-8')
        spec['deck_meta']['design_system'] = 'editorial'
        editorial = html_renderer.compile_html(spec, self.work / 'output/e.html').read_text(encoding='utf-8')
        tick = pptx_renderer.chrome_token(spec['deck_meta'], 'chart_text', '')
        self.assertTrue(tick)
        self.assertNotIn(f'fill="{tick}"', classic)
        self.assertIn(f'fill="{tick}" font-size', editorial)

    def test_doctor_font_check(self):
        sys.path.insert(0, str(ROOT / '40_plugin/scripts'))
        import deckctl
        found = deckctl.aptos_font_found()
        self.assertTrue(found is None or 'ptos' in found)


class WaterfallCharts(CoffeeWorkspace, unittest.TestCase):
    """D-067 / PAT-VIS-011: waterfall contract, validator rules, native build and the HTML mirror."""

    def result(self, spec):
        return validate_spec.validate_slide_spec_dict(spec, 't', self.work)

    def waterfall(self, spec):
        slide = next(s for s in spec.get('appendix_slides') or [] if (s.get('visual_spec') or {}).get('panels', [{}])[0].get('chart_family') == 'waterfall_chart')
        return slide, slide['visual_spec']['panels'][0]

    def test_model_and_validator(self):
        self.assertFalse([e for e in self.result(self.spec())['errors'] if 'D-067' in e])
        spec = self.spec()
        _, panel = self.waterfall(spec)
        bars = pptx_renderer.waterfall_model(panel)
        self.assertEqual([(b['category'], b['kind'], b['lo'], b['hi']) for b in bars],
                         [('Baristas', 'down', -22.0, 0.0), ('Shift supervisors', 'down', -28.0, -22.0), ('Store managers', 'down', -30.0, -28.0), ('Net gap', 'total', -30.0, 0.0)])
        self.assertEqual(bars[-1]['label'], '\u221230')
        panel['y_axis']['min'], panel['y_axis']['max'] = -20, 0
        self.assertIn('lies outside the value axis', ' '.join(self.result(spec)['errors']))
        spec = self.spec()
        _, panel = self.waterfall(spec)
        panel['series'][0]['data_points'][0]['value'] = 5.0
        self.assertIn('crosses zero', ' '.join(self.result(spec)['errors']))
        spec = self.spec()
        _, panel = self.waterfall(spec)
        panel['waterfall_mode'] = 'full'
        self.assertIn('runs one `start`', ' '.join(self.result(spec)['errors']))

    def test_renderers(self):
        from pptx import Presentation
        import html_renderer
        spec = self.spec()
        slide_spec, panel = self.waterfall(spec)
        idx = len(spec['slides']) + (spec.get('appendix_slides') or []).index(slide_spec)
        deck = pptx_renderer.compile_pptx(spec, self.work / 'output/w.pptx')
        slide = content_slides(deck)[idx]
        chart = next(sh.chart for sh in slide.shapes if getattr(sh, 'has_chart', False) and sh.has_chart)
        self.assertEqual(str(chart.chart_type), 'COLUMN_STACKED (52)')
        self.assertEqual([s.name for s in chart.plots[0].series], ['Base', 'Total', 'Decrease', 'Increase'])
        self.assertEqual(len([sh for sh in slide.shapes if sh.name == 'pai:waterfall_connector']), 3)
        self.assertEqual(len(chart._chartSpace.xpath('.//c:invertIfNegative[@val="0"]')), 4)
        page = html_renderer.compile_html(spec, self.work / 'output/w.html').read_text(encoding='utf-8')
        self.assertIn('Net gap', page)
        self.assertEqual(len(html_renderer.export_slide_pngs(spec, self.work / 'png')), len(spec['slides']) + len(spec['appendix_slides']))


class ScaleAnnotationUnits(CoffeeWorkspace, unittest.TestCase):
    """D-073: nominal vs ordinal bar order (PAT-VIS-004), marked-on-chart notes (PAT-VIS-012), table units and precision (PAT-VIS-006)."""
    RUN = ROOT / '50_evals/runs/bench_vi_briefing_no_ask'

    def result(self, spec):
        return validate_spec.validate_slide_spec_dict(spec, 't', self.work)

    def bars(self, spec):
        return spec['slides'][1]['visual_spec']['panels'][0]

    def test_category_scale(self):
        spec = self.spec()
        bars = self.bars(spec)
        bars['series'] = bars['series'][:1]
        cats = bars['x_axis']['categories']
        vals = [dp['value'] for dp in bars['series'][0]['data_points']]
        self.assertEqual(vals, sorted(vals, reverse=True), 'fixture must start sorted')
        bars['category_scale'] = 'nominal'
        self.assertFalse([w for w in self.result(spec)['warnings'] if 'D-073' in w])
        bars['category_order'] = 'natural'
        self.assertIn('nominal categories have no order of their own', ' '.join(self.result(spec)['warnings']))
        bars.pop('category_order')
        bars['x_axis']['categories'] = list(reversed(cats))
        bars['series'][0]['data_points'] = list(reversed(bars['series'][0]['data_points']))
        self.assertIn('nominal categories are not sorted largest first', ' '.join(self.result(spec)['warnings']))
        bars['category_scale'], bars['category_order'] = 'ordinal', 'by_value'
        self.assertIn('ordinal categories', ' '.join(self.result(spec)['warnings']))
        bars['category_order'] = 'natural'
        self.assertFalse([w for w in self.result(spec)['warnings'] if 'D-073' in w])

    def test_annotation_anchor_and_cap(self):
        spec = self.spec()
        slide = spec['slides'][1]
        panel = self.bars(spec)
        pid, cats = panel['panel_id'], panel['x_axis']['categories']
        note = lambda anchor, **kw: dict({'text': 'The jump follows the change.', 'target_panel_id': pid, 'anchor_data_point': anchor}, **kw)
        slide['word_jobs']['annotations'] = [note(cats[0])]
        self.assertFalse([w for w in self.result(spec)['warnings'] if 'PAT-VIS-012' in w])
        slide['word_jobs']['annotations'] = [note('No such category')]
        self.assertIn("anchor 'No such category' is not a category or series", ' '.join(self.result(spec)['warnings']))
        slide['word_jobs']['annotations'] = [note(cats[1], anchor_end_data_point=cats[0])]
        self.assertIn('the span must run forward', ' '.join(self.result(spec)['warnings']))
        slide['word_jobs']['annotations'] = [note(cats[0]), note(cats[1]), note(cats[0])]
        self.assertIn('keep at most 2', ' '.join(self.result(spec)['warnings']))

    def test_table_unit_repeat_and_precision(self):
        self.RUN = ROOT / '50_evals/runs/bench_en_coffee_two_tier'
        shutil.rmtree(self.work)
        shutil.copytree(self.RUN, self.work)
        spec = self.spec()
        table = spec['appendix_slides'][0]['table_spec']
        self.assertFalse([w for w in self.result(spec)['warnings'] if 'D-073' in w])
        rows = table['rows']
        for row in rows:
            row['cells']['sales']['formatted_label'] += '%'
        self.assertIn('every cell repeats the unit', ' '.join(self.result(spec)['warnings']))


class OnChartNotes(CoffeeWorkspace, unittest.TestCase):
    """D-074 / PAT-VIS-012: a short anchored note is drawn on a line or column chart (ring on a point, band across a span)."""
    RUN = ROOT / '50_evals/runs/bench_vi_bep_giao_do_an'

    def slide(self, spec):
        return next(sl for sl in spec['slides'] if sl['slide_id'] == 'slide_04')

    def notes(self, spec, *notes):
        sl = self.slide(spec)
        panel = sl['visual_spec']['panels'][0]
        sl['word_jobs']['annotations'] = [
            {'text': t, 'target_panel_id': panel['panel_id'], 'anchor_data_point': a, **({'anchor_end_data_point': e} if e else {})}
            for t, a, e in notes
        ]
        return panel

    def shapes(self, spec):
        from pptx import Presentation
        deck = pptx_renderer.compile_pptx(spec, self.work / 'd.pptx')
        slide_no = [sl['slide_id'] for sl in spec['slides']].index('slide_04')
        return list(content_slides(deck)[slide_no].shapes)

    def test_point_and_span_are_drawn_on_the_chart(self):
        spec = self.spec()
        self.notes(spec, ('Giờ thấp: 20 đơn', '15:00', None), ('Đỉnh chiều: 56 đơn', '18:00', '19:00'))
        shapes = self.shapes(spec)
        names = [sh.name for sh in shapes]
        self.assertEqual(names.count('pai:event_band'), 1)
        chart_at = next(i for i, sh in enumerate(shapes) if getattr(sh, 'has_chart', False) and sh.has_chart)
        self.assertLess(names.index('pai:event_band'), chart_at)  # the band sits beneath the chart
        chart = shapes[chart_at]
        band = shapes[names.index('pai:event_band')]
        self.assertGreater(band.left, chart.left)
        self.assertLess(band.left + band.width, chart.left + chart.width)
        texts = [sh.text_frame.text for sh in shapes if sh.has_text_frame]
        for t in ('Giờ thấp: 20 đơn', 'Đỉnh chiều: 56 đơn'):
            self.assertEqual(texts.count(t), 1)  # drawn once: on the chart or, when no spot is clear, as a card
        on_chart = [sh for sh in shapes if sh.name == 'pai:annotation' and sh.shape_type == 17]  # text boxes
        self.assertTrue(on_chart)

    def test_long_notes_stay_cards_and_the_cap_holds(self):
        spec = self.spec()
        long_note = 'Một ghi chú dài quá mức không thể đặt lên biểu đồ mà không che các đường dữ liệu quan trọng'
        self.notes(spec, (long_note, '12:00', None))
        names = [sh.name for sh in self.shapes(spec)]
        self.assertNotIn('pai:event_ring', names)
        self.assertNotIn('pai:event_band', names)
        spec = self.spec()
        self.notes(spec, ('Một', '12:00', None), ('Hai', '14:00', None), ('Ba', '16:00', None))
        targets = chart_marks.note_targets(self.slide(spec), 'vi')
        self.assertEqual(sorted(targets), [0, 1])  # at most two notes per panel; the third is a card

    def section(self, spec):
        page = html_renderer.compile_html(spec, self.work / 'o.html').read_text(encoding='utf-8')
        return re.search(r'<section class="slide[^"]*" id="slide_04".*?</section>', page, re.S).group(0)

    def test_html_draws_the_same_notes(self):
        spec = self.spec()
        self.notes(spec, ('Đỉnh chiều: 56 đơn', '18:00', '19:00'))
        sec = self.section(spec)
        self.assertEqual(sec.count('class="event-band ann-note"'), 1)  # a band beneath the data
        self.assertLess(sec.index('event-band'), sec.index('chart-series'))
        self.assertIn('class="annotation-note"', sec)
        self.assertNotIn('class="ann-card"', sec)  # drawn on the chart, so no card
        self.assertIn('rec-card', sec)
        long_note = 'Một ghi chú dài quá mức không thể đặt lên biểu đồ mà không che các đường dữ liệu quan trọng'
        spec = self.spec()
        self.notes(spec, (long_note, '12:00', None))
        sec = self.section(spec)
        self.assertNotIn('event-band', sec)
        self.assertEqual(sec.count('class="ann-card"'), 1)

    def test_unmatched_anchor_and_bar_value(self):
        spec = self.spec()
        sl = self.slide(spec)
        self.notes(spec, ('Nope', 'no such hour', None))
        self.assertEqual(chart_marks.note_targets(sl, 'vi'), {})
        panel = sl['visual_spec']['panels'][0]
        self.assertEqual(chart_marks.find_category(panel['x_axis']['categories'], '12:00'), panel['x_axis']['categories'].index('12:00'))


class PanelFindings(CoffeeWorkspace, unittest.TestCase):
    """D-075 / PAT-DSN-001 §3: a one-line finding heads each panel of a two-sided slide; short text only off live."""

    def slide(self, spec):
        return next(sl for sl in spec['slides'] if sl['slide_id'] == 'slide_03')

    def errors(self, spec):
        return ' '.join(e for e in validate_spec.validate_slide_spec_dict(spec, 't', self.work)['errors'] if 'D-075' in e)

    def test_benchmark_passes(self):
        self.assertEqual(self.errors(self.spec()), '')

    def test_checks(self):
        spec = self.spec()
        left, right = self.slide(spec)['visual_spec']['panels']
        right.pop('panel_headline')
        right.pop('panel_text')
        self.assertIn('both panels carry a `panel_headline` or neither', self.errors(spec))
        spec = self.spec()
        left = self.slide(spec)['visual_spec']['panels'][0]
        left['panel_headline']['text'] = 'Stores end the year thirty staff below the plan they set'
        self.assertIn('must fit one line', self.errors(spec))
        left['panel_headline']['text'] = self.slide(spec)['word_jobs']['takeaway_title']['text']
        self.assertIn('repeats the takeaway title', self.errors(spec))
        spec = self.spec()
        spec['deck_meta']['delivery_mode'] = 'live'
        self.assertIn('`panel_text` is for standalone or hybrid decks', self.errors(spec))
        spec = self.spec()
        self.slide(spec)['word_jobs']['annotations'] = [{'text': 'Baristas are most of the gap.', 'target_panel_id': 'panel_roles', 'anchor_data_point': '-'}]
        self.assertIn('carries a headline, so this card repeats it', self.errors(spec))
        spec = self.spec()
        panel = self.slide(spec)['visual_spec']['panels'][1]
        panel.pop('panel_headline')
        self.assertIn('`panel_text` needs a `panel_headline`', self.errors(spec))

    def test_pptx_draws_findings_and_aligns_titles(self):
        from pptx import Presentation

        spec = self.spec()
        deck = pptx_renderer.compile_pptx(spec, self.work / 'd.pptx')
        shapes = list(content_slides(deck)[2].shapes)
        heads = [sh for sh in shapes if sh.name == 'pai:panel_headline']
        texts = [sh for sh in shapes if sh.name == 'pai:panel_text']
        titles = [sh for sh in shapes if sh.name == 'pai:panel_title']
        self.assertEqual((len(heads), len(texts), len(titles)), (2, 2, 2))
        self.assertEqual(titles[0].top, titles[1].top, 'chart titles line up under findings of different length')
        self.assertTrue(all(h.top < t.top for h, t in zip(heads, titles)))
        run = titles[0].text_frame.paragraphs[0]  # the title style sits on the paragraph
        self.assertFalse(run.font.bold)
        self.assertEqual(str(run.font.color.rgb), spec['deck_meta']['theme_palette'].get('text_muted_hex', '#6B7280').lstrip('#').upper())
        self.assertFalse([sh for sh in shapes if 'Baristas make up' in (sh.text_frame.text if sh.has_text_frame else '') and sh.name != 'pai:panel_headline'])
        spec['deck_meta']['delivery_mode'] = 'live'
        deck = pptx_renderer.compile_pptx(spec, self.work / 'live.pptx')
        names = [sh.name for sh in content_slides(deck)[2].shapes]
        self.assertIn('pai:panel_headline', names)
        self.assertNotIn('pai:panel_text', names)

    def test_html_findings_row(self):
        page = html_renderer.compile_html(self.spec(), self.work / 'o.html').read_text(encoding='utf-8')
        page = re.search(r'<section class="slide[^"]*" id="slide_03".*?</section>', page, re.S).group(0)  # slide 4 has findings too
        self.assertIn('panels-zone panels-count-2 has-findings', page)
        self.assertEqual(page.count('class="panel-headline"'), 2)
        self.assertEqual(page.count('class="panel-title panel-title-quiet"'), 2)


class SlideFooter(CoffeeWorkspace, unittest.TestCase):
    """D-075: slide number bottom right, the short deck name before it off live, nothing on dividers."""

    def test_footer_text(self):
        meta = {'delivery_mode': 'standalone', 'deck_language': 'en', 'footer_label': 'FY2026 plan'}
        plot = {'slide_number': 3, 'layout_spec': {'layout_type': 'one_sided_right_text'}}
        self.assertEqual(pptx_renderer.slide_footer_text(plot, 2, 5, meta), 'FY2026 plan · 3')
        self.assertEqual(pptx_renderer.slide_footer_text(plot, 2, 5, {**meta, 'delivery_mode': 'live'}), '3')
        self.assertEqual(pptx_renderer.slide_footer_text({'layout_spec': {'layout_type': 'section_divider'}}, 1, 5, meta), '')
        self.assertEqual(pptx_renderer.slide_footer_text(plot, 6, 5, {**meta, 'deck_language': 'vi'}), 'Phụ lục 2')

    def test_label_checks(self):
        def errs(spec):
            res = validate_spec.validate_slide_spec_dict(spec, 't', self.work)
            return ' '.join(e for e in res['errors'] + res['warnings'] if 'footer_label' in e)
        spec = self.spec()
        self.assertEqual(errs(spec), '')
        spec['deck_meta']['footer_label'] = 'Copperleaf FY2026 menu and staffing plan'
        self.assertIn('keep the deck name short', errs(spec))
        spec['deck_meta']['footer_label'] = '[Deck name]'
        self.assertIn('bracketed placeholder', errs(spec))
        spec['deck_meta'].update(footer_label='Staffing plan', delivery_mode='live')
        self.assertIn('slide number only', errs(spec))

    def test_pptx_and_html_footer(self):
        from pptx import Presentation

        spec = self.spec()
        deck = pptx_renderer.compile_pptx(spec, self.work / 'd.pptx')
        slides = content_slides(deck)
        n_main = len(spec['slides'])
        for i, sl in enumerate(slides):
            foot = [sh for sh in sl.shapes if sh.name == 'pai:slide_footer']
            self.assertEqual(len(foot), 1, f'slide {i + 1}')
            src = [sh for sh in sl.shapes if sh.name == 'pai:source_footnote']
            if src:
                self.assertLessEqual(src[0].left + src[0].width, foot[0].left, f'slide {i + 1}: source runs under the number')
        self.assertEqual([sh for sh in slides[2].shapes if sh.name == 'pai:slide_footer'][0].text_frame.text,
                         f"{spec['deck_meta']['footer_label']} · 3")
        self.assertEqual([sh for sh in slides[n_main].shapes if sh.name == 'pai:slide_footer'][0].text_frame.text, 'Appendix 1')
        page = html_renderer.compile_html(spec, self.work / 'o.html').read_text(encoding='utf-8')
        self.assertIn(f'<span class="slide-counter">{spec["deck_meta"]["footer_label"]} · 3</span>', page)
        self.assertIn('data-counter="Slide 3 / 4"', page)  # the HUD keeps its navigation count


class ExecutiveSummary(CoffeeWorkspace, unittest.TestCase):
    """D-075 / PAT-STR-004 / PRIN-STR-004: answer-first summary slide, its points and the storyline sections."""
    RUN = ROOT / '50_evals/runs/bench_vi_briefing_no_ask'

    def issues(self, spec, kind='errors'):
        return ' '.join(e for e in validate_spec.validate_slide_spec_dict(spec, 't', self.work)[kind] if 'D-075' in e)

    def set_story(self, **fields):
        path = self.work / 'artifacts/storyline.md'
        fm, body, _ = validate_spec.parse_markdown_frontmatter(path)
        fm.update(fields)
        fm['checkpoint_g2_status'] = fm['checkpoint_g3_status'] = 'draft'
        fm.pop('approvals', None)
        path.write_text('---\n' + yaml.safe_dump(fm, allow_unicode=True, sort_keys=False) + '---' + body, encoding='utf-8')
        return path

    def test_benchmark_is_clean(self):
        res = validate_spec.validate_slide_spec_dict(self.spec(), 't', self.work)
        self.assertEqual([e for e in res['errors'] + res['warnings'] if 'D-075' in e], [])

    def test_points_and_placement(self):
        spec = self.spec()
        summary = spec['slides'][0]
        pts = summary['word_jobs']['summary_points']
        summary['word_jobs']['summary_points'] = pts[:1]
        self.assertIn('has 2–4 points', self.issues(spec))
        spec = self.spec()
        spec['slides'][0]['word_jobs']['summary_points'][0]['evidence_slides'] = [1]
        self.assertIn('does not come after the summary', self.issues(spec))
        spec['slides'][0]['word_jobs']['summary_points'][0]['evidence_slides'] = [9]
        self.assertIn('is not a main-deck slide', self.issues(spec))
        spec = self.spec()
        spec['slides'][0]['word_jobs']['summary_points'][1]['detail'] = 'Câu một. Câu hai.'
        self.assertIn('one supporting sentence', self.issues(spec))
        spec = self.spec()
        spec['slides'][0]['word_jobs']['takeaway_title']['text'] = 'Tóm tắt kết quả khảo sát hội viên năm 2026.'
        self.assertIn('not the label', self.issues(spec))
        spec = self.spec()
        spec['slides'][0]['word_jobs']['recommendation_callout'] = {'text': 'Thống nhất cách đọc chung.'}
        self.assertIn('no callout on the executive summary', self.issues(spec))
        spec = self.spec()
        spec['slides'][0], spec['slides'][1] = spec['slides'][1], spec['slides'][0]
        self.assertIn('is the first slide of the main deck', self.issues(spec))
        spec = self.spec()
        spec['slides'][1]['arc_stage'] = 'summary'
        self.assertIn('`arc_stage: summary` and `layout_type: executive_summary` go together', self.issues(spec))

    def test_storyline_agreement_and_sections(self):
        self.set_story(opening_summary={'enabled': False, 'reason': 'Buổi trình bày trực tiếp.'})
        self.assertIn('`opening_summary.enabled` is False', self.issues(self.spec()))
        self.set_story(opening_summary={'enabled': True, 'reason': 'x'},
                       sections=[{'number': 1, 'claim': 'A.', 'slides': [2, 3]}, {'number': 2, 'claim': 'B.', 'slides': [4]}])
        spec = self.spec()
        self.assertIn('belongs to no section', self.issues(spec))
        self.assertIn('3 summary points for 2 sections', self.issues(spec, 'warnings'))
        self.assertIn('outside section 2', self.issues(spec, 'warnings'))
        path = self.set_story(sections=[{'number': 1, 'claim': 'A.', 'slides': [2]}, {'number': 2, 'claim': 'B.', 'slides': [2, 3]}])
        self.assertIn('each slide belongs to one section', ' '.join(validate_spec.validate_storyline(path)['errors']))
        path = self.set_story(opening_summary={'enabled': True})
        self.assertIn('needs `enabled` (true or false) and a one-line `reason`', ' '.join(validate_spec.validate_storyline(path)['errors']))

    def test_default_on_warning_and_skeptics(self):
        spec = self.spec()
        spec['slides'] = spec['slides'][1:]
        self.set_story(opening_summary=None)
        path = self.work / 'artifacts/storyline.md'
        fm, body, _ = validate_spec.parse_markdown_frontmatter(path)
        fm.pop('opening_summary', None)
        fm.pop('sections', None)
        path.write_text('---\n' + yaml.safe_dump(fm, allow_unicode=True, sort_keys=False) + '---' + body, encoding='utf-8')
        self.assertIn('opens with an executive summary by default', self.issues(spec, 'warnings'))
        self.set_brief(audience_map={**(validate_spec.load_context_brief_fm(self.work).get('audience_map') or {}),
                                     'resistance_assessment': 'mapped'})
        self.assertIn('the brief maps resistance', self.issues(self.spec(), 'warnings'))

    def test_renderers_draw_rows(self):
        from pptx import Presentation

        spec = self.spec()
        deck = pptx_renderer.compile_pptx(spec, self.work / 'd.pptx')
        shapes = list(content_slides(deck)[0].shapes)
        names = [sh.name for sh in shapes]
        self.assertEqual(names.count('pai:summary_point'), 3)
        refs = [sh.text_frame.text for sh in shapes if sh.name == 'pai:summary_ref']
        self.assertEqual(refs, ['Slide 2', 'Slide 3', 'Slide 4'])
        point = next(sh for sh in shapes if sh.name == 'pai:summary_point').text_frame.paragraphs[0]
        lead = spec['slides'][0]['word_jobs']['summary_points'][0]['lead']
        self.assertEqual(''.join(r.text for r in point.runs if r.font.bold).replace('\u00a0', ' ').strip(), lead)
        self.assertFalse([sh for sh in shapes if getattr(sh, 'has_chart', False)])
        self.assertEqual(pptx_renderer.evidence_ref_label([4, 3], 'en'), 'Slides 3–4')
        self.assertEqual(pptx_renderer.evidence_ref_label([2, 4], 'en'), 'Slides 2, 4')
        page = html_renderer.compile_html(spec, self.work / 'o.html').read_text(encoding='utf-8')
        self.assertEqual(page.count('class="summary-row"'), 3)
        self.assertIn('<div class="summary-ref">Slide 4</div>', page)


class TitleSlide(CoffeeWorkspace, unittest.TestCase):
    """D-075 (mock-up S2): an unnumbered title slide opens the deck; no drafting text reaches it."""

    def issues(self, spec, kind='errors'):
        return ' '.join(e for e in validate_spec.validate_slide_spec_dict(spec, 't', self.work)[kind] if 'title_slide' in e or 'title slide' in e)

    def test_checks(self):
        spec = self.spec()
        self.assertEqual(self.issues(spec) + self.issues(spec, 'warnings'), '')
        spec['deck_meta']['title_slide']['date'] = '[meeting date]'
        self.assertIn("replace the placeholder '[meeting date]'", self.issues(spec))
        spec = self.spec()
        spec['deck_meta']['title_slide']['title'] = ' '.join(['word'] * 16)
        self.assertIn('keep the deck title to one line', self.issues(spec))
        spec = self.spec()
        spec['deck_meta']['title_slide'].pop('presenter')
        self.assertIn('presenter missing', self.issues(spec, 'warnings'))
        spec = self.spec()
        spec['deck_meta']['title_slide'] = {'enabled': False}
        self.assertIn('needs a one-line `disabled_reason`', self.issues(spec))
        spec['deck_meta'].pop('title_slide')
        self.assertIn('open on a title slide by default', self.issues(spec, 'warnings'))

    def test_pptx_and_html(self):
        from pptx import Presentation
        import render_qa_pngs

        spec = self.spec()
        deck = pptx_renderer.compile_pptx(spec, self.work / 'd.pptx')
        prs = Presentation(str(deck))
        first = prs.slides[0]
        names = [sh.name for sh in first.shapes]
        self.assertIn('pai:deck_title', names)
        self.assertNotIn('pai:slide_footer', names)
        self.assertEqual(first.shapes.title.text_frame.text, spec['deck_meta']['title_slide']['title'])
        meta = next(sh for sh in first.shapes if sh.name == 'pai:title_meta').text_frame.text
        self.assertEqual(meta, 'November 2026 · Store Operations and Finance')
        self.assertEqual(len(prs.slides), 1 + len(spec['slides']) + len(spec['appendix_slides']))
        self.assertEqual([sh for sh in prs.slides[1].shapes if sh.name == 'pai:slide_footer'][0].text_frame.text,
                         f"{spec['deck_meta']['footer_label']} · 1")
        self.assertTrue(render_qa_pngs.opens_on_title_slide(deck))
        spec['deck_meta']['title_slide']['enabled'] = False
        spec['deck_meta']['title_slide']['disabled_reason'] = 'Slides go into a larger board pack.'
        plain = pptx_renderer.compile_pptx(spec, self.work / 'plain.pptx')
        self.assertFalse(render_qa_pngs.opens_on_title_slide(plain))
        self.assertEqual(len(Presentation(str(plain)).slides), len(spec['slides']) + len(spec['appendix_slides']))
        page = html_renderer.compile_html(self.spec(), self.work / 'o.html').read_text(encoding='utf-8')
        self.assertIn('<section class="slide title-slide active" id="title_slide"', page)
        self.assertEqual(page.count('class="slide active"') + page.count('class="slide  active"'), 0)


class EvidenceColumns(CoffeeWorkspace, unittest.TestCase):
    """D-075 / PAT-DSN-001: a decision slide with one recommendation line over 2-3 columns of heading, finding and chart."""

    def slide(self, spec):
        return next(sl for sl in spec['slides'] if sl['slide_id'] == 'slide_04')

    def issues(self, spec, kind='errors'):
        return ' '.join(m for m in validate_spec.validate_slide_spec_dict(spec, 't', self.work)[kind] if 'D-075' in m or 'G4.6' in m or 'PAT-DSN-004' in m)

    def three_columns(self, spec):
        import copy
        panels = self.slide(spec)['visual_spec']['panels']
        extra = copy.deepcopy(panels[1])
        extra['panel_id'] = 'panel_third'
        extra['column_heading'] = 'Third'
        panels.append(extra)
        return panels

    def test_benchmark_passes(self):
        spec = self.spec()
        self.assertEqual(self.slide(spec)['layout_spec']['layout_type'], 'evidence_columns')
        self.assertEqual(self.issues(spec), '')
        self.assertEqual(self.issues(self.three_columns(spec) and spec), '')  # three columns are allowed

    def test_line_and_headings(self):
        spec = self.spec()
        wj = self.slide(spec)['word_jobs']
        line = wj.pop('recommendation_line')
        self.assertIn('need a `word_jobs.recommendation_line`', self.issues(spec))
        wj['recommendation_line'] = {'text': wj['takeaway_title']['text'], 'color_tie_spans': []}
        self.assertIn('repeats the takeaway title', self.issues(spec))
        wj['recommendation_line'] = {**line, 'text': ' '.join(['word'] * 26)}
        self.assertIn('the line must fit', self.issues(spec))
        wj['recommendation_line'] = line
        wj['recommendation_callout'] = {'text': 'Approve the plan today.', 'distinct_from_takeaway_title': True, 'color_tie_spans': []}
        self.assertIn('not a `recommendation_callout`', self.issues(spec))
        spec = self.spec()
        panels = self.slide(spec)['visual_spec']['panels']
        panels[0]['column_heading'] = 'Payoff in dollars per year'
        self.assertIn('`column_heading` is a criterion of at most 3 words', self.issues(spec))
        panels[0].pop('column_heading')
        self.assertIn('needs a `column_heading`', self.issues(spec))
        spec = self.spec()
        panels = self.slide(spec)['visual_spec']['panels']
        panels[0]['panel_headline']['text'] = 'Barista hiring leads on payoff at $1.5M while the menu refresh adds $0.9M on top.'
        self.assertIn('must fit one sentence', self.issues(spec))
        panels[0]['panel_headline']['text'] = 'Hiring leads on payoff, then price changes and the menu refresh.'
        panels[1]['panel_text'] = 'Extra text.'
        self.assertIn('drop `panel_text`', self.issues(spec))

    def test_size_and_family_limits(self):
        spec = self.spec()
        panels = self.slide(spec)['visual_spec']['panels']
        panels.pop()
        self.assertIn('take 2-3 panels', self.issues(spec))
        spec = self.spec()
        panels = self.three_columns(spec)
        panels.append({**panels[0], 'panel_id': 'panel_fourth', 'column_heading': 'Fourth'})
        self.assertIn('take 2-3 panels', self.issues(spec))
        spec = self.spec()
        panels = self.slide(spec)['visual_spec']['panels']
        panels[0]['x_axis']['categories'] = panels[0]['x_axis']['categories'] + ['Seventh option']
        self.assertIn('at most 6 categories', self.issues(spec))
        spec = self.spec()
        panels = self.slide(spec)['visual_spec']['panels']
        panels[0]['series'].append(dict(panels[0]['series'][0], series_name='Second series'))
        panels[0]['series'].append(dict(panels[0]['series'][0], series_name='Third series'))
        self.assertIn('at most 2 series', self.issues(spec))
        spec = self.spec()
        self.slide(spec)['visual_spec']['panels'][0]['chart_family'] = 'stacked_bar_chart'
        self.assertIn('bar, column, line or dot-plot charts only', self.issues(spec))

    def test_notes_must_sit_on_the_chart(self):
        spec = self.spec()
        wj = self.slide(spec)['word_jobs']
        wj['annotations'] = [{'text': 'Hiring costs more up front.', 'target_panel_id': 'panel_payoff', 'anchor_data_point': '-'}]
        self.assertIn('no card strip', self.issues(spec))

    def test_one_colour_per_entity_across_columns(self):
        spec = self.spec()
        panel = self.slide(spec)['visual_spec']['panels'][1]
        point = next(dp for dp in panel['series'][0]['data_points'] if dp['category'] == 'Fill 22 barista roles')
        point['point_color_override_hex'] = '#1F77B4'
        point['point_visual_role_override'] = 'focal_secondary_tier2'
        self.assertIn('PAT-DSN-004', self.issues(spec))

    def test_headline_colour_tie_is_checked(self):
        spec = self.spec()
        panel = self.slide(spec)['visual_spec']['panels'][0]
        panel['panel_headline']['color_tie_spans'][0]['substring'] = 'Not in the headline'
        self.assertIn("not found in `panel_payoff.panel_headline`", self.issues(spec))

    def test_the_fields_belong_to_this_layout(self):
        spec = self.spec()
        other = spec['slides'][1]
        other['word_jobs']['recommendation_line'] = {'text': 'Approve the plan.', 'color_tie_spans': []}
        other['visual_spec']['panels'][0]['column_heading'] = 'Payoff'
        found = self.issues(spec)
        self.assertIn('`recommendation_line` belongs to `evidence_columns` slides', found)
        self.assertIn('`column_heading` belongs to `evidence_columns` slides', found)

    def test_live_decks_reveal_one_column_at_a_time(self):
        spec = self.spec()
        spec['deck_meta']['delivery_mode'] = 'live'
        sl = self.slide(spec)
        sl.pop('panel_text', None)
        self.assertIn('reveal one column at a time', self.issues(spec, 'warnings'))
        sl['progressive_reveal'] = {
            'enabled': True, 'standalone_self_sufficient_verified': True,
            'reveal_steps': [
                {'step_number': 1, 'visible_panel_ids': ['panel_payoff'], 'visible_series_roles': ['context_greyscale', 'focal_primary_tier1', 'focal_secondary_tier2'],
                 'show_annotations': False, 'show_recommendation_callout': True, 'speaker_notes': 'Start with the payoff.'},
                {'step_number': 2, 'visible_panel_ids': ['panel_payoff', 'panel_effort'], 'visible_series_roles': ['context_greyscale', 'focal_primary_tier1', 'focal_secondary_tier2'],
                 'show_annotations': True, 'show_recommendation_callout': True, 'speaker_notes': 'Then the effort.'},
            ],
        }
        self.assertNotIn('reveal one column at a time', self.issues(spec, 'warnings'))
        sl['progressive_reveal']['reveal_steps'][1]['visible_panel_ids'] = ['panel_payoff']
        self.assertIn('reveal one column at a time', self.issues(spec, 'warnings'))

    def test_pptx_stack_per_column(self):
        spec = self.spec()
        deck = pptx_renderer.compile_pptx(spec, self.work / 'd.pptx')
        shapes = list(content_slides(deck)[3].shapes)
        by = lambda name: [sh for sh in shapes if sh.name == name]
        line, = by('pai:recommendation_line')
        heads, finds, titles = by('pai:column_heading'), by('pai:panel_headline'), by('pai:panel_title')
        charts = [sh for sh in shapes if getattr(sh, 'has_chart', False) and sh.has_chart]
        self.assertEqual((len(heads), len(finds), len(titles), len(charts)), (2, 2, 2, 2))
        self.assertEqual(heads[0].top, heads[1].top)
        self.assertEqual(titles[0].top, titles[1].top, 'chart titles line up under findings of different length')
        for h, f, t, c in zip(heads, finds, titles, charts):
            self.assertTrue(h.top < f.top < t.top < c.top)  # heading, finding, chart title, chart, top to bottom
            self.assertGreaterEqual(line.top, c.top + c.height)  # D-076: the recommendation line closes the slide under the columns
        self.assertLessEqual(charts[0].left + charts[0].width, charts[1].left)
        self.assertFalse(by('pai:annotation') or by('pai:callout'))
        self.assertEqual(line.text_frame.text, spec['slides'][3]['word_jobs']['recommendation_line']['text'])

    def test_three_columns_fit_without_overlap(self):
        spec = self.spec()
        self.three_columns(spec)
        deck = pptx_renderer.compile_pptx(spec, self.work / 'd3.pptx')
        shapes = list(content_slides(deck)[3].shapes)
        charts = sorted((sh for sh in shapes if getattr(sh, 'has_chart', False) and sh.has_chart), key=lambda sh: sh.left)
        self.assertEqual(len(charts), 3)
        for a, b in zip(charts, charts[1:]):
            self.assertLessEqual(a.left + a.width, b.left)
        self.assertLessEqual(charts[-1].left + charts[-1].width, 12.73 * 914400 + 1)
        self.assertLessEqual(max(sh.top + sh.height for sh in charts), 6.9 * 914400)  # clear of the source line

    def test_reveal_steps_hide_the_other_columns_but_keep_the_layout(self):
        from pptx import Presentation
        spec = self.spec()
        spec['deck_meta']['delivery_mode'] = 'live'
        self.slide(spec)['progressive_reveal'] = {
            'enabled': True, 'standalone_self_sufficient_verified': True,
            'reveal_steps': [
                {'step_number': 1, 'visible_panel_ids': ['panel_payoff'], 'visible_series_roles': ['context_greyscale', 'focal_primary_tier1', 'focal_secondary_tier2'],
                 'show_annotations': False, 'show_recommendation_callout': False, 'speaker_notes': 'Payoff.'},
                {'step_number': 2, 'visible_panel_ids': ['panel_payoff', 'panel_effort'], 'visible_series_roles': ['context_greyscale', 'focal_primary_tier1', 'focal_secondary_tier2'],
                 'show_annotations': True, 'show_recommendation_callout': True, 'speaker_notes': 'Effort.'},
            ],
        }
        deck = Presentation(str(pptx_renderer.compile_pptx(spec, self.work / 'r.pptx', expand_reveal=True)))
        slides = [sl for sl in deck.slides if any(sh.name == 'pai:column_heading' for sh in sl.shapes)]
        self.assertEqual(len(slides), 2)
        first, second = ([sh for sh in sl.shapes if sh.name == 'pai:column_heading'] for sl in slides)
        self.assertEqual((len(first), len(second)), (1, 2))
        self.assertFalse([sh for sh in slides[0].shapes if sh.name == 'pai:recommendation_line'])
        self.assertEqual(first[0].top, second[0].top)
        self.assertEqual(first[0].left, second[0].left)

    def test_html_columns_and_reveal_hooks(self):
        page = html_renderer.compile_html(self.spec(), self.work / 'o.html').read_text(encoding='utf-8')
        section = re.search(r'<section class="slide[^"]*" id="slide_04".*?</section>', page, re.S).group(0)
        self.assertIn('slide-body layout-evidence_columns', section)
        self.assertEqual(section.count('class="column-heading"'), 2)
        self.assertEqual(section.count('class="panel-headline"'), 2)
        self.assertEqual(section.count('class="rec-line"'), 1)
        self.assertIn('panels-zone panels-count-2 has-findings', section)
        self.assertGreater(section.index('rec-line'), section.index('panels-zone'))  # D-076: under the columns
        self.assertNotIn('ann-card', section)
        self.assertIn(".chart-panel, .panel-finding", page)  # a hidden column hides its heading and finding too
        self.assertIn(".rec-card, .rec-line", page)

    def test_preview_png_draws_the_columns(self):
        out = self.work / 'preview'
        files = html_renderer.export_slide_pngs(self.spec(), out)
        self.assertTrue(any(f.name == 'slide_04.png' for f in files))


class EditorialDesignSystem(unittest.TestCase):
    """D-078-D-080 step 1: fonts, type roles and text colours come from design_tokens.yaml; classic is unchanged."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='pai_design_test_')
        self.addCleanup(self.tmp.cleanup)
        self.work = Path(self.tmp.name)
        self.output = contextlib.redirect_stdout(io.StringIO())
        self.output.__enter__()
        self.addCleanup(self.output.__exit__, None, None, None)

    def spec(self, system='editorial'):
        spec = yaml.safe_load((ROOT / '50_evals/runs/bench_en_coffee_two_tier/artifacts/slide_spec.yaml').read_text(encoding='utf-8'))
        if system:
            spec['deck_meta']['design_system'] = system
        return spec

    def test_classic_is_the_default_and_unchanged(self):
        meta = {'delivery_mode': 'standalone'}
        self.assertIs(pptx_renderer.type_scale(meta), pptx_renderer.TYPE_SCALES['standalone'])
        self.assertEqual(pptx_renderer.deck_font(meta), 'Arial')
        self.assertEqual(pptx_renderer.title_font(meta), 'Arial')
        spec = self.spec(system=None)
        self.assertIs(pptx_renderer.apply_design_system(spec), spec)

    def test_editorial_roles_fonts_and_five_sizes(self):
        for mode, title, body, chart, small in (('standalone', 24, 12, 10.5, 9), ('live', 28, 16, 13.5, 12)):
            meta = {'delivery_mode': mode, 'design_system': 'editorial'}
            ts = pptx_renderer.type_scale(meta)
            self.assertEqual((ts['takeaway_title'], ts['annotation'], ts['value_tick'], ts['source_footnote']), (title, body, chart, small))
            self.assertEqual(ts['diagram_label'], body)
            sizes = sorted({ts[k] for k in pptx_renderer.design_system(meta)['role_of']}, reverse=True)
            self.assertLessEqual(len(sizes), 5)
            self.assertTrue(all(a - b >= 1.5 for a, b in zip(sizes, sizes[1:])))  # D-029
        meta = {'design_system': 'editorial'}
        self.assertEqual((pptx_renderer.deck_font(meta), pptx_renderer.title_font(meta)), ('Aptos', 'Aptos Display'))
        meta['typography'] = {'font_family': 'Arial'}
        self.assertEqual(pptx_renderer.title_font(meta), 'Arial')  # a brand body face does not pull in Aptos Display

    def test_text_colours_follow_the_tokens_on_a_copy(self):
        spec = self.spec()
        resolved = pptx_renderer.apply_design_system(spec)
        self.assertEqual(resolved['deck_meta']['theme_palette']['text_primary_hex'], '#18202B')
        self.assertEqual(resolved['deck_meta']['theme_palette']['text_muted_hex'], '#586273')
        self.assertEqual(spec['deck_meta']['theme_palette']['text_primary_hex'], '#1F2937')  # digest input untouched

    def test_compiled_deck_uses_the_editorial_title_face_and_ink(self):
        out = pptx_renderer.compile_pptx(self.spec(), self.work / 'out' / 'p.pptx')
        slide = content_slides(out)[0]
        title = next(sh for sh in slide.shapes if sh.name == 'pai:takeaway_title')
        runs = [r for p in title.text_frame.paragraphs for r in p.runs]
        self.assertTrue(all(r.font.name == 'Aptos Display' and r.font.size.pt == 24 for r in runs))
        self.assertIn('18202B', {str(r.font.color.rgb) for r in runs})

    def test_editorial_chrome_in_pptx(self):
        from pptx.util import Emu
        from color_contrast import contrast_ratio
        deck = content_slides(pptx_renderer.compile_pptx(self.spec(), self.work / 'out' / 'p.pptx'))
        s1, s4 = deck[0], deck[3]
        header_rules = [sh for sh in s1.shapes if sh.shape_type == 9 and Emu(sh.top).inches < 1.4 and Emu(sh.width).inches > 10]
        self.assertEqual(header_rules, [])  # space, not a rule, under the header
        ann = next(sh for sh in s1.shapes if sh.name == 'pai:annotation')
        self.assertEqual(ann.fill.type, MSO_FILL.BACKGROUND)
        self.assertTrue(any(sh.name == 'pai:card_rule' for sh in s1.shapes))
        callout = next(sh for sh in s1.shapes if sh.name == 'pai:callout')
        self.assertEqual(callout.text_frame.paragraphs[0].text, 'Implication and action')
        fill = '#' + str(callout.fill.fore_color.rgb)
        self.assertTrue(1.1 <= contrast_ratio(fill, '#FFFFFF') <= 1.13, fill)  # ANTI-DSN-002 floor kept
        bar = next(sh for sh in s4.shapes if sh.name == 'pai:recommendation_bar')
        self.assertEqual(bar.shape_type, 9)  # a hairline, not a filled bar

    def test_classic_chrome_unchanged(self):
        deck = content_slides(pptx_renderer.compile_pptx(self.spec(system=None), self.work / 'out' / 'c.pptx'))
        s1, s4 = deck[0], deck[3]
        callout = next(sh for sh in s1.shapes if sh.name == 'pai:callout')
        self.assertEqual(callout.text_frame.paragraphs[0].text, 'KEY IMPLICATION & ACTION')
        self.assertEqual('#' + str(callout.fill.fore_color.rgb), '#FEE6CE')
        self.assertFalse(any(sh.name == 'pai:card_rule' for sh in s1.shapes))
        self.assertNotEqual(next(sh for sh in s4.shapes if sh.name == 'pai:recommendation_bar').shape_type, 9)

    def test_aptos_width_keeps_every_month_label(self):
        meta = {'design_system': 'editorial'}
        self.assertAlmostEqual(pptx_renderer.font_width_factor(meta), 0.93)
        self.assertEqual(pptx_renderer.font_width_factor({'design_system': 'editorial', 'typography': {'font_family': 'Arial'}}), 1.0)
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        shown, _ = pptx_renderer.fit_category_labels(months, 0.366, 10.5, 'en', 0.93)
        self.assertEqual(shown, months)
        thinned, _ = pptx_renderer.fit_category_labels(months, 0.366, 10.5, 'en')
        self.assertIn('', thinned)  # the Arial estimate would thin them

    def test_editorial_chrome_in_html(self):
        page = html_renderer.compile_html(self.spec(), self.work / 'o.html').read_text(encoding='utf-8')
        self.assertIn('.slide-header { border-bottom: none; }', page)
        self.assertIn('Implication and action', page)
        self.assertNotIn('KEY IMPLICATION', page)
        classic = html_renderer.compile_html(self.spec(system=None), self.work / 'c.html').read_text(encoding='utf-8')
        self.assertNotIn('.slide-header { border-bottom: none; }', classic)
        self.assertIn('KEY IMPLICATION &amp; ACTION', classic)

    def test_editorial_title_slide_and_divider(self):
        from pptx import Presentation
        from pptx.util import Emu
        spec = self.spec()
        div = {'slide_id': 'div_x', 'slide_number': 2, 'arc_stage': 'rising_action',
               'layout_spec': {'layout_type': 'section_divider', 'emphasis': 'key', 'section_number': 2},
               'word_jobs': {'takeaway_title': {'text': 'Barista hiring decides most of the recovery', 'color_tie_spans': []},
                             'section_question': 'How short are stores?', 'source_footnote': ''}}
        spec['slides'] = spec['slides'][:1] + [div]
        prs = Presentation(str(pptx_renderer.compile_pptx(spec, self.work / 'out' / 'p.pptx')))
        title = prs.slides[0]
        names = [sh.name for sh in title.shapes]
        self.assertIn('pai:title_stroke', names)  # CONF-015: one short stroke, no rule
        self.assertFalse(any(sh.shape_type == 9 for sh in title.shapes))
        deck_title = next(sh for sh in title.shapes if sh.name == 'pai:deck_title')
        para = deck_title.text_frame.paragraphs[0]  # set_plain_paragraph styles the paragraph, not the run
        self.assertEqual((para.font.name, para.font.size.pt), ('Aptos Display', 36))
        meta = next(sh for sh in title.shapes if sh.name == 'pai:title_meta')
        self.assertAlmostEqual(Emu(meta.top).inches, 6.35, places=2)
        self.assertIn(' ', meta.text_frame.text)
        self.assertNotIn('·', meta.text_frame.text)
        number = next(sh for sh in prs.slides[2].shapes if sh.name == 'pai:section_number')
        self.assertEqual(number.text_frame.paragraphs[0].font.size.pt, 24 * 5.5)

    def test_classic_title_slide_unchanged(self):
        from pptx import Presentation
        prs = Presentation(str(pptx_renderer.compile_pptx(self.spec(system=None), self.work / 'out' / 'c.pptx')))
        title = prs.slides[0]
        self.assertNotIn('pai:title_stroke', [sh.name for sh in title.shapes])
        self.assertTrue(any(sh.shape_type == 9 for sh in title.shapes))
        self.assertIn(' · ', next(sh for sh in title.shapes if sh.name == 'pai:title_meta').text_frame.text)

    def test_one_line_title_gets_one_line_in_aptos(self):
        from pptx.util import Emu
        spec = self.spec()
        spec['deck_meta']['delivery_mode'] = 'live'
        spec['slides'][0]['word_jobs']['takeaway_title']['text'] = 'Giao trễ dồn vào hai khung cao điểm và tốn 1,8 tỷ đồng mỗi quý.'
        spec['slides'][0]['word_jobs']['takeaway_title']['color_tie_spans'] = []
        title = next(sh for sh in content_slides(pptx_renderer.compile_pptx(spec, self.work / 'out' / 'l.pptx'))[0].shapes
                     if sh.name == 'pai:takeaway_title')
        self.assertLess(Emu(title.height).inches, 0.7)  # 28 pt, one line; the Arial estimate reserved two

    def test_html_title_slide_stroke(self):
        page = html_renderer.compile_html(self.spec(), self.work / 'o.html').read_text(encoding='utf-8')
        self.assertIn('<div class="title-stroke"></div>', page)
        self.assertNotIn('<div class="title-rule"></div>', page)

    def test_validator_accepts_the_field_and_rejects_unknown_systems(self):
        path = self.work / 'slide_spec.yaml'
        for system, expect_error in (('editorial', False), ('fancy', True)):
            path.write_text(yaml.safe_dump(self.spec(system), allow_unicode=True, sort_keys=False), encoding='utf-8')
            errors = validate_spec.validate_slide_spec_file(path)['errors']
            self.assertEqual(any('design_system' in e for e in errors), expect_error, errors[:3])


class EditorialDesignChecks(unittest.TestCase):
    """D-090 (Editorial step 5): design-system checks on the compiled deck and the content digest."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix='pai_design_checks_')
        cls.work = Path(cls.tmp.name)
        cls.spec = yaml.safe_load((ROOT / '50_evals/runs/bench_en_coffee_two_tier/artifacts/slide_spec.yaml').read_text(encoding='utf-8'))
        cls.spec['deck_meta']['design_system'] = 'editorial'
        with contextlib.redirect_stdout(io.StringIO()):
            cls.deck = pptx_renderer.compile_pptx(cls.spec, cls.work / 'editorial.pptx')

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def findings(self, edit=None, spec=None):
        import design_qa
        from pptx import Presentation
        path = self.deck
        if edit:
            prs = Presentation(str(self.deck))
            edit(prs)
            path = self.work / f'edited_{id(edit)}.pptx'
            prs.save(str(path))
        return design_qa.design_findings(path, spec or self.spec)

    @staticmethod
    def shape(prs, name, slide=1):
        return next(sh for sh in prs.slides[slide].shapes if sh.name == name)

    def test_editorial_deck_passes_and_classic_is_not_checked(self):
        self.assertEqual(self.findings(), ([], []))
        classic = copy.deepcopy(self.spec)
        del classic['deck_meta']['design_system']
        self.assertEqual(self.findings(lambda prs: None, classic), ([], []))

    def test_text_colour_errors(self):
        from pptx.dml.color import RGBColor

        def off_token_grey(prs):
            self.shape(prs, 'pai:annotation').text_frame.paragraphs[0].runs[0].font.color.rgb = RGBColor(0x77, 0x77, 0x77)

        def pale_grey(prs):  # the context grey is a mark colour, but too pale for words in a text box
            self.shape(prs, 'pai:annotation').text_frame.paragraphs[0].runs[0].font.color.rgb = RGBColor(0x9E, 0x9E, 0x9E)

        def stray_hue(prs):
            self.shape(prs, 'pai:annotation').text_frame.paragraphs[0].runs[0].font.color.rgb = RGBColor(0x7A, 0x1F, 0xA2)

        for edit, expect in ((off_token_grey, 'is not a design-system ink'), (pale_grey, 'below 4.5:1'), (stray_hue, 'neither an ink nor a data colour')):
            errors, _ = self.findings(edit)
            self.assertTrue(any(expect in e and 'D-090' in e for e in errors), (edit.__name__, errors))

    def test_warnings(self):
        from pptx.dml.color import RGBColor
        from pptx.enum.shapes import MSO_SHAPE
        from pptx.util import Inches, Pt

        def caps_label(prs):
            self.shape(prs, 'pai:callout').text_frame.paragraphs[0].runs[0].text = 'IMPLICATION AND ACTION'

        def side_bar(prs):
            ann = self.shape(prs, 'pai:annotation')
            bar = prs.slides[1].shapes.add_shape(MSO_SHAPE.RECTANGLE, ann.left - Inches(0.15), ann.top, Inches(0.07), ann.height)
            bar.fill.solid()
            bar.fill.fore_color.rgb = RGBColor(0xD9, 0x5F, 0x02)

        def strong_fill(prs):
            self.shape(prs, 'pai:callout').fill.fore_color.rgb = RGBColor(0xFB, 0xB0, 0x70)

        def second_family(prs):
            self.shape(prs, 'pai:annotation').text_frame.paragraphs[0].runs[0].font.name = 'Georgia'

        def odd_size(prs):
            self.shape(prs, 'pai:annotation').text_frame.paragraphs[0].runs[0].font.size = Pt(11)

        cases = ((caps_label, 'set in capitals'), (side_bar, 'filled side bar'), (strong_fill, 'card fill'),
                 (second_family, 'second type family'), (odd_size, 'not a type-role size'))
        for edit, expect in cases:
            errors, warnings = self.findings(edit)
            self.assertEqual(errors, [], edit.__name__)
            self.assertTrue(any(expect in w for w in warnings), (edit.__name__, warnings))

    def test_title_stroke_and_hairlines_are_not_side_bars(self):
        _, warnings = self.findings()
        self.assertFalse(any('side bar' in w for w in warnings))

    def test_brand_face_is_the_one_family(self):
        spec = copy.deepcopy(self.spec)
        spec['deck_meta']['typography'] = {'font_family': 'Arial'}
        with contextlib.redirect_stdout(io.StringIO()):
            deck = pptx_renderer.compile_pptx(spec, self.work / 'brand.pptx')
        import design_qa
        self.assertFalse([w for w in design_qa.design_findings(deck, spec)[1] if 'type family' in w])

    def test_content_digest(self):
        from spec_digest import content_digest
        base = content_digest(self.spec)
        spec = copy.deepcopy(self.spec)
        spec['slides'][0]['finish'] = {'chart_height_in': 4.5}
        spec['g4_review_audit'] = {'status': 'rerun'}
        spec['slides'][0]['claim_evidence_contract']['rendered_png_qa'] = {'zero_text_overlap_or_clipping': False}
        self.assertEqual(content_digest(spec), base)  # design adjustments and QA results are free
        for edit in (lambda s: s['slides'][0]['word_jobs']['takeaway_title'].update(text='Changed.'),
                     lambda s: s['slides'][0]['layout_spec'].update(layout_type='statement_or_transition'),
                     lambda s: s['deck_meta'].update(typography={'font_family': 'Arial'})):
            spec = copy.deepcopy(self.spec)
            edit(spec)
            self.assertNotEqual(content_digest(spec), base)


class FinishPass(unittest.TestCase):
    """D-091 (Editorial step 6): the finish block in the renderers and the validator, and the content-digest guard."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='pai_finish_')
        self.addCleanup(self.tmp.cleanup)
        self.work = Path(self.tmp.name)
        self.output = contextlib.redirect_stdout(io.StringIO())
        self.output.__enter__()
        self.addCleanup(self.output.__exit__, None, None, None)
        self.spec = yaml.safe_load((ROOT / '50_evals/runs/bench_en_coffee_two_tier/artifacts/slide_spec.yaml').read_text(encoding='utf-8'))
        self.spec['deck_meta']['design_system'] = 'editorial'

    def process_slide(self, spec):
        return next(s for s in spec['appendix_slides'] if (s.get('diagram_spec') or {}).get('process_flow'))

    def errors(self, spec):
        return [e for e in validate_spec.validate_slide_spec_dict(spec, 't', ROOT / '50_evals/runs/bench_en_coffee_two_tier')['errors'] if 'D-091' in e]

    def test_break_index(self):
        self.assertEqual(pptx_renderer.title_break_index('Recover $2.4M in FY2026 through barista hiring', 5), 31)
        self.assertIsNone(pptx_renderer.title_break_index('Two words', 2))
        self.assertIsNone(pptx_renderer.title_break_index('Two words', 0))
        self.assertEqual(pptx_renderer.text_with_break('a b c', 1), 'a\nb c')

    def test_pptx_fields(self):
        from pptx import Presentation
        from pptx.util import Emu
        spec = copy.deepcopy(self.spec)
        spec['deck_meta']['title_slide']['finish'] = {'title_break_after': 5}
        spec['slides'][0]['finish'] = {'title_break_after': 1, 'side_card_cols': 3, 'chart_height_in': 4.0}
        self.process_slide(spec)['finish'] = {'diagram_height_in': 2.5}
        base = Presentation(str(pptx_renderer.compile_pptx(self.spec, self.work / 'base.pptx')))
        prs = Presentation(str(pptx_renderer.compile_pptx(spec, self.work / 'fin.pptx')))
        deck_title = next(sh for sh in prs.slides[0].shapes if sh.name == 'pai:deck_title')
        self.assertEqual(len(deck_title.text_frame.paragraphs[0]._p.findall(qn('a:br'))), 1)
        self.assertEqual(deck_title.text_frame.text.replace('\v', ' '), spec['deck_meta']['title_slide']['title'])
        title = next(sh for sh in prs.slides[1].shapes if sh.name == 'pai:takeaway_title')
        para = title.text_frame.paragraphs[0]
        self.assertEqual(len(para._p.findall(qn('a:br'))), 1)  # inside the Color Tie span "Seasonal drinks fell"
        tie = {str(r.font.color.rgb) for r in para.runs if r.text.strip() in ('Seasonal', 'drinks fell')}
        self.assertEqual(len(tie), 1)
        self.assertNotIn('18202B', tie)  # both halves keep the focal colour
        callout = next(sh for sh in prs.slides[1].shapes if sh.name == 'pai:callout')
        self.assertAlmostEqual(Emu(callout.width).inches, pptx_renderer.side_card_width_in(3), places=2)
        chart = next(sh for sh in prs.slides[1].shapes if getattr(sh, 'has_chart', False) and sh.has_chart)
        base_chart = next(sh for sh in base.slides[1].shapes if getattr(sh, 'has_chart', False) and sh.has_chart)
        self.assertLess(chart.height, base_chart.height)
        self.assertGreater(chart.width, base_chart.width)
        idx = 1 + len(spec['slides']) + spec['appendix_slides'].index(self.process_slide(spec))

        def lowest(p):
            group = next(sh for sh in p.slides[idx].shapes if sh.name == 'pai:diagram')
            return max(c.top + c.height for c in group.shapes)
        self.assertLess(lowest(prs), lowest(base))

    def test_preview_fields(self):
        from PIL import Image, ImageDraw
        draw = ImageDraw.Draw(Image.new('RGB', (1920, 200), 'white'))
        font = html_renderer.load_ttf_font(34, bold=True)
        args = dict(x=0, y=0, max_w=1800, text='Seasonal drinks fell sharply', spans=[], default_hex='#000000', font_reg=font, font_bold=font, line_height=44)
        self.assertEqual(html_renderer.draw_colored_paragraph_pil(draw, **args), 44)
        self.assertEqual(html_renderer.draw_colored_paragraph_pil(draw, **args, break_at=pptx_renderer.title_break_index(args['text'], 2)), 88)
        spec = copy.deepcopy(self.spec)
        base = html_renderer.export_slide_pngs(spec, self.work / 'pv0')[0]
        spec['slides'][0]['finish'] = {'title_break_after': 3, 'side_card_cols': 3, 'chart_height_in': 4.0}
        fin = html_renderer.export_slide_pngs(spec, self.work / 'pv1')[0]
        self.assertNotEqual(base.read_bytes(), fin.read_bytes())

    def test_html_fields(self):
        spec = copy.deepcopy(self.spec)
        spec['deck_meta']['title_slide']['finish'] = {'title_break_after': 5}
        spec['slides'][0]['finish'] = {'title_break_after': 3, 'side_card_cols': 4}
        page = html_renderer.compile_html(spec, self.work / 'o.html').read_text(encoding='utf-8')
        self.assertIn('Recover $2.4M in FY2026 through<br>barista', page)
        self.assertIn('style="grid-template-columns: 1fr 32.2%"', page)
        self.assertNotIn('align-self: start', page)
        spec['slides'][0]['finish']['chart_height_in'] = 3.5
        page = html_renderer.compile_html(spec, self.work / 'h.html').read_text(encoding='utf-8')
        self.assertIn('style="height: 68.0%; align-self: start"', page)
        self.assertIn('viewBox="0 0 760 279"', page)
        self.assertEqual(html_renderer.insert_br_html('<b>A &amp; B</b> C', 5), '<b>A &amp; B</b><br>C')

    def test_validator_rules(self):
        self.assertEqual(self.errors(self.spec), [])
        cases = (
            (lambda s: s['slides'][0].update(finish={'colour': 'red'}), 'are not finish fields'),
            (lambda s: s['slides'][0].update(finish={'chart_height_in': 4.03}), 'off the 0.05 in base unit'),
            (lambda s: s['slides'][0].update(finish={'diagram_height_in': 3.0}), 'only to `diagram` slides'),
            (lambda s: s['slides'][0].update(finish={'side_card_cols': 5}), '3 or 4 of the 12'),
            (lambda s: s['slides'][0].update(finish={'title_break_after': 40}), 'whole number of words'),
            (lambda s: s['deck_meta']['title_slide'].update(finish={'title_break_after': 1}), 'does not fit on one line'),
            (lambda s: s['deck_meta']['title_slide'].update(finish={'side_card_cols': 3}), 'only `title_break_after` applies'),
        )
        for edit, expect in cases:
            spec = copy.deepcopy(self.spec)
            edit(spec)
            self.assertTrue(any(expect in e for e in self.errors(spec)), (expect, self.errors(spec)))

    def test_content_digest_guard(self):
        from spec_digest import content_digest
        spec = copy.deepcopy(self.spec)
        spec['g4_review_audit']['finish'] = {'content_digest': content_digest(spec)}
        spec['slides'][0]['finish'] = {'side_card_cols': 4}
        self.assertEqual(self.errors(spec), [])
        spec['slides'][0]['word_jobs']['takeaway_title']['text'] = 'Seasonal drinks fell while core drinks grew.'
        self.assertTrue(any('content changed after the finish pass began' in e for e in self.errors(spec)))

    def test_deckctl_digest(self):
        from spec_digest import content_digest
        work = self.work / 'ws'
        (work / 'artifacts').mkdir(parents=True)
        shutil.copy(ROOT / '50_evals/runs/bench_en_coffee_two_tier/artifacts/slide_spec.yaml', work / 'artifacts/slide_spec.yaml')
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(deckctl.cmd_digest(work), 0)
        spec = yaml.safe_load((work / 'artifacts/slide_spec.yaml').read_text(encoding='utf-8'))
        self.assertEqual(out.getvalue().strip(), content_digest(spec))


if __name__ == '__main__':
    unittest.main(verbosity=2)
