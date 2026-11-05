"""Build the failure-analysis PDF and Markdown from the saved benchmark run.

Requires ReportLab and the restored media for HA01, HB01 and HA08.
Does not change model responses, scoring, labels or execution manifests.
"""
import hashlib
import json
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    Flowable, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

from protocol import HERE, expected_state, parse_response, score_episode

ROOT = HERE.parents[2]
OUTPUT = ROOT / 'output/pdf/HOLOASSIST_20_FAILURE_ANALYSIS_EN.pdf'
WIDTH = A4[0] - 100
INK = colors.HexColor('#172131')
BLUE = colors.HexColor('#265783')
PALE = colors.HexColor('#f1f5f9')
GRAY = colors.HexColor('#526174')
AMBER = colors.HexColor('#fff5df')
PHASE_ORDER = ['joint', 'chronological_0', 'chronological_1', 'delayed_0', 'delayed_1']
PHASE_NAMES = {'joint': 'Joint A+B', 'chronological_0': 'Chronological: A',
               'chronological_1': 'Chronological: B', 'delayed_0': 'Reversed: B',
               'delayed_1': 'Reversed: A'}
SHORT_TASKS = {
    'HA01': 'DSLR lens separated', 'HA02': 'Printer LCD illuminated',
    'HA03': 'Round tabletop seated', 'HA04': 'Cabinet door open',
    'HA05': 'Hand in fastener bin', 'HA06': 'DSLR battery clear',
    'HA07': 'Action camera out of insert', 'HA08': 'Vessel tilted over reservoir',
    'HA09': 'Perforated-panel underside exposed', 'HA10': 'Basket tilted relative to cart',
    'HB01': 'Drive belt free of pulley route', 'HB02': 'Cabinet door open',
    'HB03': 'DSLR lens separated', 'HB04': 'Action camera out of insert',
    'HB05': 'Desktop side panel clear', 'HB06': 'Expansion board outside chassis',
    'HB07': 'Round tabletop removed', 'HB08': 'Black rail separated',
    'HB09': 'Paper drawer extended', 'HB10': 'Reservoir under flowing water',
}


def load_run():
    cases = json.loads((HERE / 'cases.json').read_text())
    records = {case['case_id']: json.loads((HERE / 'responses' / f"{case['case_id']}.json").read_text())
               for case in cases}
    analysis = json.loads((HERE / 'analysis.json').read_text())
    episodes = {case['case_id']: score_episode(case, records[case['case_id']]['steps']) for case in cases}
    assert analysis['status'] == 'complete' and analysis['totals']['n_actual_benchmark_responses'] == 100
    assert {item['case_id']: item['episode'] for item in analysis['per_video']} == episodes
    assert all(record['analysis'] == episodes[sid] for sid, record in records.items())
    return cases, records, analysis


def state(obj, short=False):
    obj = obj or {}
    values = [obj.get(key, 'missing') for key in ('earlier', 'latest')]
    if short:
        values = [{'no': 'N', 'yes': 'Y', 'unknown': 'U'}.get(value, '?') for value in values]
    return ' / '.join(values)


class PacketPanel(Flowable):
    """Place exact JPEG evidence with legible capture-time labels."""
    def __init__(self, case):
        super().__init__()
        self.case = case
        self.width, self.height = WIDTH, 182

    def draw(self):
        canvas = self.canv
        cell = self.width / 4
        image_height = cell * 9 / 16
        for row, pid in enumerate(('A', 'B')):
            packet = self.case['packets'][pid]
            top = self.height - row * 91
            for column, frame in enumerate(packet['frames']):
                path = HERE / frame['path']
                if hashlib.sha256(path.read_bytes()).hexdigest() != frame['sha256']:
                    raise ValueError(f'Evidence image changed: {path}')
                x = column * cell
                canvas.drawImage(str(path), x, top - image_height, width=cell - 1,
                                 height=image_height, preserveAspectRatio=True, anchor='c')
                canvas.setFont('Helvetica', 8)
                canvas.setFillColor(INK)
                canvas.drawString(x + 2, top - image_height - 11,
                                  f"{pid} | {frame['source_pts_seconds']:.3f} s")


class EvidenceDiagram(Flowable):
    def __init__(self):
        super().__init__()
        self.width, self.height = WIDTH, 90

    def draw(self):
        c = self.canv
        c.setFillColor(PALE)
        c.roundRect(0, 0, self.width, self.height, 4, fill=1, stroke=0)
        c.setFont('Helvetica-Bold', 10)
        c.setFillColor(INK)
        c.drawString(12, 70, 'Fixed claim identity')
        c.drawString(260, 70, 'HA01 reversed final citations')
        c.setFont('Helvetica', 10)
        for y, left, right in [(48, 'Earlier claim at 8.045 s -> packet A', 'earlier=no -> [] (no cited support)'),
                               (26, 'Latest claim at 8.512 s -> packet B', 'latest=yes -> [A] (wrong capture time)')]:
            c.drawString(12, y, left)
            c.drawString(260, y, right)


def build():
    cases, records, analysis = load_run()
    by_id = {case['case_id']: case for case in cases}
    metrics, totals = analysis['metrics'], analysis['condition_totals']
    manifest = json.loads((HERE / 'execution_manifest.json').read_text())
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle('ReportTitle', fontName='Helvetica-Bold', fontSize=23,
                              leading=27, textColor=INK, spaceAfter=13))
    styles.add(ParagraphStyle('SectionTitle', fontName='Helvetica-Bold', fontSize=15,
                              leading=19, textColor=BLUE, spaceBefore=12, spaceAfter=9))
    styles.add(ParagraphStyle('BodyCopy', fontName='Helvetica', fontSize=10.4,
                              leading=14.7, textColor=INK, spaceAfter=8))
    styles.add(ParagraphStyle('SmallCopy', parent=styles['BodyCopy'], fontSize=8.6,
                              leading=11.7, textColor=GRAY, spaceAfter=6))
    styles.add(ParagraphStyle('CellCopy', parent=styles['BodyCopy'], fontSize=9,
                              leading=12, spaceAfter=0))
    styles.add(ParagraphStyle('CellHead', parent=styles['CellCopy'], fontName='Helvetica-Bold', textColor=BLUE))
    styles.add(ParagraphStyle('CodeCopy', fontName='Courier', fontSize=8.7, leading=12,
                              backColor=PALE, borderPadding=9, spaceBefore=4, spaceAfter=12))
    story, markdown = [], []

    def paragraph(text, kind='BodyCopy'):
        story.append(Paragraph(text, styles[kind]))
        markdown.extend([text.replace('<b>', '**').replace('</b>', '**').replace('<br/>', '\n'), ''])

    def heading(text, title=False):
        story.append(Paragraph(text, styles['ReportTitle' if title else 'SectionTitle']))
        markdown.extend([('# ' if title else '## ') + text, ''])

    def page():
        story.append(PageBreak())
        markdown.extend(['---', ''])

    def table(headers, rows, widths, highlight=None, padding=6):
        cells = [[Paragraph(escape(str(value)), styles['CellHead']) for value in headers]]
        cells += [[Paragraph(escape(str(value)), styles['CellCopy']) for value in row] for row in rows]
        result = Table(cells, colWidths=widths, hAlign='LEFT', repeatRows=1)
        rules = [('BACKGROUND', (0, 0), (-1, 0), PALE),
                 ('LINEBELOW', (0, 0), (-1, 0), 0.7, BLUE),
                 ('LINEBELOW', (0, 1), (-1, -1), 0.3, colors.HexColor('#dbe2e9')),
                 ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                 ('LEFTPADDING', (0, 0), (-1, -1), 6),
                 ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                 ('TOPPADDING', (0, 0), (-1, -1), padding),
                 ('BOTTOMPADDING', (0, 0), (-1, -1), padding)]
        for row in highlight or []:
            rules.append(('BACKGROUND', (0, row), (-1, row), AMBER))
        result.setStyle(TableStyle(rules))
        story.extend([result, Spacer(1, 9)])
        markdown.extend(['| ' + ' | '.join(headers) + ' |', '| ' + ' | '.join('---' for _ in headers) + ' |'])
        markdown.extend('| ' + ' | '.join(str(value).replace('|', '/') for value in row) + ' |' for row in rows)
        markdown.append('')

    def evidence(sid):
        story.append(PacketPanel(by_id[sid]))
        markdown.extend([f'Evidence panel: {sid}, exact four-frame packets A and B; source capture timestamps.', ''])

    def response(sid, phase):
        return parse_response(records[sid]['steps'][phase]['raw_response'])[0]

    def trace(sid, citations=False):
        rows = []
        for phase in PHASE_ORDER:
            obj = response(sid, phase)
            expected = expected_state(by_id[sid], phase)
            row = [PHASE_NAMES[phase], state(expected), state(obj)]
            if citations:
                row.append(str(obj['earlier_evidence']) + ' / ' + str(obj['latest_evidence']))
            rows.append(row)
        if citations:
            table(['Input step', 'Expected E / L', 'Observed E / L', 'Cites E / L'], rows,
                  [132, 126, 126, WIDTH - 384])
        else:
            table(['Input step', 'Expected earlier / latest', 'Observed earlier / latest'], rows,
                  [142, 176, WIDTH - 318])

    def rate(key):
        value = metrics[key]
        return f"{value['successes']}/{value['denominator']}"

    # 1. Scope and experimental evidence, following the supplied note's structure.
    heading('Historical Belief Revision in Streaming Video', title=True)
    paragraph('Failure analysis across 20 HoloAssist videos | Qwen2.5-VL-3B | 4 November 2026', 'SmallCopy')
    heading('Research question')
    paragraph('Can late-arriving video evidence correct a model\'s knowledge of the past, affect the right capture-time '
              'claim, and preserve already supported recent states? The event is fixed; the model\'s expressed belief '
              'and its claimed evidence may change. [1, 2]')
    heading('Experimental evidence')
    paragraph('Each recording supplies two event-centered packets: four native frames in earlier packet A and four in '
              'later packet B. The same eight frames are tested jointly, chronologically (A then B), and in reversed '
              'arrival order (B then A). Sequential requests see only the current packet and the exact prior response '
              'as external memory. Capture times and packet IDs are supplied explicitly.')
    evidence('HA01')
    paragraph('HA01 example: A ends at 8.044704 s; B ends at 8.512032 s. Condition: lens visibly separated from the DSLR '
              'body. Provisional endpoint labels: A=no, B=yes. These are sampled packets, not full-length clips.', 'SmallCopy')
    rows = []
    for phase, label in [('joint', 'Joint final'), ('chronological_1', 'Chronological final'), ('delayed_1', 'Reversed final')]:
        row = totals[phase]
        rows.append([label, f"{row['both_fields_correct_cases']}/17", f"{row['correct_state_fields']}/34",
                     f"{row['correct_known_value_and_packet']}/31"])
    table(['Condition', 'Both states correct', 'Correct state fields', 'Known fact + packet'], rows,
          [138, 110, 112, WIDTH - 360])
    paragraph('<b>Central finding:</b> state values are often recovered in reversed order, but none of the 31 known '
              'final fields has both a correct value and the required packet citation. A no-video schedule rule also '
              'scores 31/34 final state fields. Value correction alone therefore does not establish evidence use.')
    paragraph('100 requests completed; one greedy trial per condition. Seventeen targets are provisionally scored; '
              'HA05, HA09 and HA10 are diagnostic-only. All labels await independent adjudication. [1, 2]', 'SmallCopy')

    # 2. Historical correction, with a fully visible five-request case.
    page()
    heading('Question one: can knowledge change while the past event stays fixed?')
    paragraph(f'Before A arrives in reversed order, earlier=unknown in {rate("uncertainty_preserved_before_earlier_evidence")} '
              f'qualified cases. In the 14 cases with a known earlier label, {rate("clean_historical_update_success")} '
              'show the observable transition unknown to no after A. Unlike a correct early guess, this is a change '
              'in the historical value. It is still a value-only measure, not proof of visual grounding.')
    heading('HB01: joint success, failure in both sequential orders')
    paragraph('Condition: the drive belt is free of the machine pulley route. Earlier target: 34.489038 s (no); '
              'later target: 41.781579 s (yes). The positive endpoint precedes the legacy 52 s anchor; this run uses '
              'the reviewed native endpoint. [1, 2]')
    evidence('HB01')
    trace('HB01')
    paragraph('Chronological input first gives the correct no/no values. After B, earlier becomes unknown and latest '
              'stays no: a correct historical value is lost and the later positive is missed. Reversed input gives '
              'unknown/no before and after A, so the historical correction never occurs. Its latest answer was already '
              'wrong, so this is not loss of an initially correct recent fact.')
    paragraph('HB08 illustrates a different limit: reversed input does correct earlier from unknown to no, but ends '
              'no/no when no/yes is required. Historical correction can succeed while the full state remains wrong.')
    paragraph('<b>Answer:</b> observable historical value revision occurs in 13/14 eligible cases. That does not '
              'establish a stable evidence-driven policy: no-pixel rules can produce the same transitions, citations '
              'are incorrect, and individual sequential failures remain. Joint value success is a comparison condition, '
              'not proof of an internal representation or perception mechanism.')

    # 3. Evidence association, independent of value matching.
    page()
    heading('Question two: which belief does the new evidence affect?')
    paragraph('Fixed capture-time claims and evidence packet IDs make state accuracy separable from citation accuracy. '
              'Earlier targets A; latest targets B once B has arrived, even when older A is received last. A supplied '
              'packet ID tests expressed temporal attribution, not natural discovery that two views show the same event.')
    heading('HA01: correct reversed values, incorrect supporting packet')
    trace('HA01', citations=True)
    paragraph('After B, the model says unknown/yes and correctly cites B for latest. After older A, the values become '
              'no/yes, but earlier has no cited support and latest now cites A. The true latest target is still B\'s '
              'capture time. A correct value has survived while its expressed support has moved to the wrong packet.')
    story.extend([EvidenceDiagram(), Spacer(1, 12)])
    markdown.extend(['Fixed claim: earlier at 8.044704 s -> A; latest at 8.512032 s -> B.',
                     'Observed reversed final: earlier=no -> []; latest=yes -> [A].', ''])
    table(['Check', 'Observed result', 'Meaning'], [
        ['Known final value + packet', 'Joint 16/31; chronological 12/31; reversed 0/31',
         'Value-only scores hide evidence-association errors.'],
        ['Reversed latest cites older A', '14/17 qualified cases',
         'All 14 initially correct recent values are preserved, but each ends with the wrong A citation.'],
        ['Same-time field disagreement', '14/17 chronological first steps',
         'At this step both fields target the identical A endpoint; different answers are inconsistent.'],
    ], [138, 140, WIDTH - 278])
    paragraph('<b>Answer:</b> the model does not consistently assign expressed support to the requested capture-time '
              'claim. The observable errors include missing historical support, older-packet citations for the later '
              'claim, and conflicting same-time answers. They do not distinguish internal forgetting, overwriting, '
              'misbinding or a generic citation/prompt-following failure.')
    paragraph('Graph implication: keep evidence observations, fixed claims and model beliefs as separate node types. '
              'The exported belief graphs retain each request and memory link; model-cites edges remain unverified '
              'assertions. A correct state value does not turn these into verified support edges. [2]')

    # 4. Required uncertainty and conditional preservation.
    page()
    heading('Question three: when should the model revise or remain uncertain?')
    paragraph('Unknown has two distinct reasons here: the relevant packet has not arrived, or the received packet '
              'does not settle the visual relation. The second reason applies to HA06, HA08 and HB06 even after A. '
              'Those cases are uncertainty-maintenance tests, not clean unknown-to-known opportunities.')
    heading('HA08: the only joint-and-chronological success with reversed failure')
    evidence('HA08')
    paragraph('Condition: vessel tilted with its mouth over the open reservoir. Earlier target 19.498907 s remains '
              'unresolved; later target 20.798834 s is positive. Both joint and chronological final outputs are '
              'unknown/yes. Reversed output changes unknown/yes to no/yes after A. The earlier no is unjustified '
              'under the provisional packet label; this is an uncertainty-maintenance error. [1, 2]')
    table(['Case', 'Expected final E / L', 'Reversed first -> final', 'Failure distinction'], [
        ['HA06', 'unknown / yes', 'unknown / unknown -> no / unknown', 'Earlier overcommitment plus missed later positive.'],
        ['HA08', 'unknown / yes', 'unknown / yes -> no / yes', 'Earlier overcommitment; later value preserved.'],
        ['HB06', 'unknown / yes', 'unknown / yes -> no / yes', 'Earlier overcommitment; both sequential finals fail.'],
    ], [45, 112, 165, WIDTH - 322])
    paragraph(f'Recent values are preserved in {rate("recent_fact_preserved")} eligible reversed runs; the denominator '
              'includes only cases whose latest value was initially correct. HA06, HB01 and HB08 are excluded from '
              'this preservation rate because latest was already wrong or unknown. Historical preservation in '
              'chronological order is 0/1: only HB01 starts with a correct known earlier value.')
    paragraph('<b>Answer:</b> the model appropriately abstains before unseen historical evidence in 17/17 qualified '
              'cases, but does not reliably remain uncertain when received evidence is inconclusive. Correct recent '
              'values can persist with incorrect evidence citations. These are expressed state and abstention outcomes; '
              'no probability calibration or internal confidence is measured.')

    # 5. Interpretation and next experiment, explicitly contrasted with the reference.
    page()
    heading('Current conclusion and failure taxonomy')
    table(['Observed pattern', 'Cases or count', 'Supported interpretation'], [
        ['Joint correct; both sequential finals fail', 'HB01, HB06',
         'Segmented-input difficulty in these cases; HB06 has an unknown prior label.'],
        ['Joint + chronological correct; reversed fails', 'HA08 only',
         'Order-sensitive uncertainty failure in one trial; not failure to recover a known earlier fact.'],
        ['All final state values correct', 'HB07 only',
         'A positive value-level comparison; its reversed citations are still incorrect.'],
        ['Invalid JSON or truncated output', '0/100; 0/100',
         'Observed errors are not explained by invalid formatting or the output cap.'],
        ['Unresolved original task', 'HA05, HA09, HA10',
         'Retain raw traces; exclude from primary correctness and revision rates.'],
    ], [148, 100, WIDTH - 248])
    heading('What differs from the supplied findings note?')
    paragraph('The reference table-assembly example reported a premature earlier=no commitment and loss of a '
              'previously correct latest=yes. [3] Neither pattern should be copied into this batch\'s conclusion: '
              'all 17 qualified reversed runs initially answer earlier=unknown, and all 14 initially correct latest '
              'values remain correct. The prominent new observation is broken evidence attribution despite retained '
              'values. This comparison is qualitative: prompts, sampling and the reference\'s undocumented runtime '
              'settings prevent an exact replication claim.')
    heading('A no-video rule exposes a benchmark confound')
    paragraph('Consider an analytical rule: earlier=unknown until A, then no; latest=no until B, then yes. Without '
              'examining any pixels, it achieves 31/34 final state fields, 14/17 fully correct cases and all 14 '
              'unknown-to-no transitions. This is a label-balance calculation, not a model run. The observed model '
              'reaches only 12/17 fully correct reversed finals. These results cannot establish visual evidence use '
              'or reliable historical revision from value-transition scores alone.')
    heading('Next experiment')
    paragraph('<b>1.</b> Balance unchanged-positive, unchanged-negative, negative-to-positive and positive-to-negative '
              'cases. Add wrong-time and shuffled-packet controls to test whether answers depend on the evidence. '
              '<b>2.</b> Obtain independent labels and adjudicate HA05/HA09/HA10 and uncertain endpoints. '
              '<b>3.</b> Grade value correctness, time targeting, evidence citations and conditional preservation '
              'separately; retain same-time consistency checks. <b>4.</b> Repeat across trials and vary packet gaps '
              'and memory format before estimating reliability or attributing an internal mechanism.')
    paragraph('Scope: one deterministic trial, event-centered eight-frame inputs and external response memory. This '
              'is not native continuous-stream evaluation, natural replay discovery, a causal mechanism experiment, '
              'or a reproduction of the reference\'s separate uniform whole-video sampling experiment.', 'SmallCopy')

    # 6. Every case, plus concise reproducibility and source references.
    page()
    heading('Appendix: all 20 videos')
    paragraph('Every entry is an exact final earlier/latest output, not an accuracy percentage. N=no, Y=yes, '
              'U=unknown. Gold denotes provisional endpoint labels after both packets. Dashes mark unscored '
              'targets; highlighted rows are diagnostic-only. Earlier questions and latest boundaries use the '
              'capture endpoints recorded in cases.json.', 'SmallCopy')
    rows, excluded_rows = [], []
    for index, case in enumerate(cases, 1):
        sid = case['case_id']
        gold = state({'earlier': case['earlier_gold'], 'latest': case['later_gold']}, short=True) \
            if case['primary_qualified'] else '--'
        rows.append([sid, SHORT_TASKS[sid], gold,
                     state(response(sid, 'joint'), short=True),
                     state(response(sid, 'chronological_1'), short=True),
                     state(response(sid, 'delayed_1'), short=True)])
        if not case['primary_qualified']:
            excluded_rows.append(index)
    table(['ID', 'Visible condition (short label)', 'Gold', 'Joint', 'Chronol.', 'Reversed'],
          rows, [35, 206, 55, 62, 67, WIDTH - 425], highlight=excluded_rows, padding=3)
    heading('Reproducibility and sources')
    paragraph('Official checkpoint: Qwen/Qwen2.5-VL-3B-Instruct; revision '
              + manifest['signatures']['model_revision'] + '. FP16, Apple MPS (CPU fallback enabled), SDPA; '
              'greedy decoding, seed 20261104, 128-token cap, 112,896 max pixels/frame. The run completed '
              '100 benchmark requests with no infrastructure failures or output-limit hits. All 100 responses '
              'are valid four-key JSON. Full provenance audit and eight metric tests passed.', 'SmallCopy')
    paragraph('[1] experiments/holoassist_20/belief_revision_v1/: cases.json, analysis.json, execution_manifest.json, '
              'responses/&lt;ID&gt;.json and analysis/&lt;ID&gt;.md. All counts were recomputed from saved outputs.', 'SmallCopy')
    paragraph('[2] experiments/holoassist_20/online_pilot_v0/reviews/batch_v1/&lt;ID&gt;/evidence_graph.json; '
              'belief_revision_v1/belief_graphs/&lt;ID&gt;.json. Source records and attribution are in '
              'online_pilot_v0/sources.json and ATTRIBUTION.md.', 'SmallCopy')
    paragraph('[3] User-supplied reference: STREAMING_BELIEF_REVISION_FINDINGS_EN.pdf, six pages. '
              'The present report follows its three-question structure; its historical examples are not pooled '
              'with this run. HoloAssist recordings are attributed to Wang et al., ICCV 2023; local source bytes '
              'come from the pinned EgoIT-99K mirror recorded in sources.json. Images show the exact selected '
              'frames, with source capture timestamps. Annotations remain provisional.', 'SmallCopy')

    def page_furniture(canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(GRAY)
        if doc.page > 1:
            canvas.drawString(50, A4[1] - 30, 'STREAM-EVAL-BENCH | QWEN2.5-VL-3B FAILURE ANALYSIS')
        canvas.drawCentredString(A4[0] / 2, 26, str(doc.page))
        canvas.restoreState()

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    document = SimpleDocTemplate(str(OUTPUT), pagesize=A4, rightMargin=50, leftMargin=50,
                                 topMargin=44, bottomMargin=42,
                                 title='Historical Belief Revision in Streaming Video: 20-Video Failure Analysis',
                                 author='Stream-Eval-Bench', pageCompression=1)
    document.build(story, onFirstPage=page_furniture, onLaterPages=page_furniture)
    text = '\n'.join(markdown).replace('&lt;', '<').replace('&gt;', '>')
    (HERE / 'FAILURE_ANALYSIS.md').write_text(text)
    print(OUTPUT)
    print(HERE / 'FAILURE_ANALYSIS.md')


if __name__ == '__main__':
    build()
