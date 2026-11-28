import json
import math
from dataclasses import dataclass
from pathlib import Path

from .pack import _normal


@dataclass
class TestSet:
    questions: list
    next_id: int

    @property
    def shortfalls(self):
        return [f'{name}: {count}/{minimum}' for name, count, minimum in (
            ('questions', len(self.questions), 20),
            ('unanswerable', sum(q['label'] == 'unanswerable' for q in self.questions), 4),
            ('changed-mind', sum(q['changed_mind'] for q in self.questions), 3)) if count < minimum]


def load_test_set(path) -> TestSet:
    path = Path(path)
    if not path.exists():
        return TestSet([], 1)
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except (ValueError, UnicodeError) as e:
        raise ValueError(f'Test Set questions: {e}') from e
    if not isinstance(data, dict) or not isinstance(data.get('questions'), list):
        raise ValueError('Test Set questions: expected a list')
    questions = data['questions']
    ids = set()
    for q in questions:
        name = q.get('question', '<unknown>') if isinstance(q, dict) else '<unknown>'
        def check(condition, field):
            if not condition:
                raise ValueError(f'{name}: invalid {field}')
        check(isinstance(q, dict), 'question')
        check(isinstance(name, str) and bool(name.strip()), 'question')
        check(type(q.get('id')) is int and q['id'] > 0 and q['id'] not in ids, 'id')
        ids.add(q['id'])
        check(q.get('label') in ('answerable', 'partly', 'unanswerable'), 'label')
        check(type(q.get('changed_mind')) is bool, 'changed_mind')
        right = q.get('right', [])
        check(isinstance(right, list) and (q['label'] == 'unanswerable' or bool(right)), 'right')
        for mark in right:
            check(isinstance(mark, dict) and all(isinstance(mark.get(k), str) and mark[k].strip()
                  for k in ('conversation', 'phrase')), 'right')
        if q['changed_mind']:
            for field in ('current', 'replaced'):
                check(isinstance(q.get(field), str) and bool(q[field].strip()), field)
    next_id = data.get('next_id', max(ids, default=0) + 1)
    if type(next_id) is not int or next_id <= max(ids, default=0):
        raise ValueError('Test Set: invalid next_id')
    return TestSet(questions, next_id)


def add(kb, question, label, changed_mind):
    path = kb.folder / 'quality' / 'test-set.json'
    test_set = load_test_set(path)
    hits = kb.search(question, k=20)
    for n, hit in enumerate(hits, 1):
        c = hit.chunk
        print(f'{n}. {c.title} ({c.platform}:{c.chat_id})\n   {c.text}')
    chunks = kb.chunks()
    q = {'id': test_set.next_id, 'question': question, 'label': label,
         'changed_mind': changed_mind, 'right': []}
    if label != 'unanswerable':
        while True:
            choice = input('Hit number, or conversation reference for a missed chunk (blank to finish): ').strip()
            if not choice:
                if q['right']:
                    break
                print('At least one right chunk is required.')
                continue
            if choice.isdigit() and 1 <= int(choice) <= len(hits):
                c = hits[int(choice) - 1].chunk
                reference = f'{c.platform}:{c.chat_id}'
                candidates = [c]
            else:
                reference = choice
                candidates = [c for c in chunks if f'{c.platform}:{c.chat_id}' == reference]
            phrase = input('Exact phrase: ').strip()
            if not _normal(phrase) or not any(_normal(phrase) in _normal(c.text) for c in candidates):
                print('Phrase not found in the chosen chunk or conversation.')
                continue
            q['right'].append({'conversation': reference, 'phrase': phrase})
    if changed_mind:
        for field in ('current', 'replaced'):
            while True:
                phrase = input(f'{field.capitalize()} choice phrase: ').strip()
                if _normal(phrase) and any(_normal(phrase) in _normal(c.text) for c in chunks):
                    q[field] = phrase
                    break
                print('Phrase not found in the Knowledge Base.')
    test_set.questions.append(q)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({'questions': test_set.questions, 'next_id': test_set.next_id + 1},
                               indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(f'Added question {q["id"]}.')
    if test_set.shortfalls:
        print('Test Set shortfall: ' + ', '.join(test_set.shortfalls))


from datetime import datetime
from .pack import pack, WritingModelError


@dataclass
class Report:
    questions: list
    settings: dict


@dataclass
class Check:
    name: str
    passed: bool
    value: str
    failures: list


@dataclass
class FloorSuggestion:
    floor: float
    unanswerable_let_through: int
    answerable_emptied: int


def suggest_floor(report):
    values = [r.get('floor_score') for r in report.questions if r.get('floor_score') is not None]
    if not values:
        return None
    candidates = sorted(set(values + [math.nextafter(v, math.inf) for v in values]))
    def suggestion(floor):
        let_through = sum(r['question']['label'] == 'unanswerable' and r.get('floor_score') is not None
                          and r['floor_score'] >= floor for r in report.questions)
        emptied = sum(r['question']['label'] != 'unanswerable' and
                      (r.get('floor_score') is None or r['floor_score'] < floor) for r in report.questions)
        return FloorSuggestion(floor, let_through, emptied)
    return min((suggestion(v) for v in candidates),
               key=lambda s: (s.unanswerable_let_through + s.answerable_emptied, s.floor))


def floor_text(report):
    suggestion = suggest_floor(report)
    if suggestion is None:
        return 'Suggested floor: unavailable (no scores)'
    return (f'Suggested floor: {suggestion.floor!r} '
            f'(unanswerable let through: {suggestion.unanswerable_let_through}, '
            f'answerable wrongly emptied: {suggestion.answerable_emptied})')


def run(kb, test_set, writer):
    rows = []
    for index, q in enumerate(test_set.questions):
        hits = kb.search(q['question'], k=8)[:8]
        right_hits = [h for h in hits if any(f'{h.chunk.platform}:{h.chunk.chat_id}' == mark['conversation']
                      and _normal(mark['phrase']) in _normal(h.chunk.text)
                      for mark in q.get('right', []))]
        finding = bool(right_hits)
        floor_score = (hits[0].score if hits else None) if q['label'] == 'unanswerable' else max(
            (h.score for h in right_hits), default=None)
        try:
            result = pack(kb, q['question'], writer)
            rows.append({'question': q, 'finding': finding, 'nothing_found': result.nothing_found,
                         'pack': result.text, 'error': None, 'floor_score': floor_score,
                         'needs': [f"{n.need} ({'covered' if n.covered else 'missing'})" for n in result.needs],
                         'match_score': result.match_score.text if result.match_score else None,
                         'current_decision': q['changed_mind'] and not result.nothing_found and any(_normal(q['current']) in _normal(d.quote) and
                             any(_normal(q['replaced']) in _normal(old.quote) for old in d.replaced)
                             for d in result.decisions)})
        except WritingModelError as e:
            if index == 0:
                raise
            rows.append({'question': q, 'finding': False, 'nothing_found': False,
                         'pack': None, 'error': str(e), 'floor_score': floor_score})
    return Report(rows, {})


def score(report):
    for r in report.questions:
        q = r['question']
        if q['label'] == 'unanswerable' or r['error']:
            continue
        for field in ('hallucinations', 'wrong_missing'):
            if type(r.get(field)) is not int or r[field] < 0:
                raise ValueError(f"{q['question']}: invalid or blank {field}")
        if r['nothing_found'] and (type(r.get('expected')) is not int or r['expected'] < 1):
            raise ValueError(f"{q['question']}: invalid or blank needs you expected")
        if q['label'] == 'partly' and r.get('missing_exact') not in ('yes', 'no'):
            raise ValueError(f"{q['question']}: invalid or blank missing needs named exactly")
    checks = []
    for name, selected, threshold in (
        ('Finding', [r for r in report.questions if r['question']['label'] != 'unanswerable'], 0.9),
        ('Correct Abstention', [r for r in report.questions if r['question']['label'] in ('unanswerable', 'partly')], 1.0),
    ):
        failures = [r['question']['question'] for r in selected if r['error'] or not (
            r['finding'] if name == 'Finding' else (r['nothing_found'] if r['question']['label'] == 'unanswerable' else r['missing_exact'] == 'yes'))]
        passed = len(selected) - len(failures)
        checks.append(Check(name, not selected or passed / len(selected) >= threshold,
                            f'{passed}/{len(selected)} (pass >= {threshold:.0%})', failures))
    rows = [r for r in report.questions if r['question']['label'] != 'unanswerable']
    names = lambda rs: [r['question']['question'] for r in rs]
    failed = [r for r in rows if r['error'] or r['hallucinations']]
    checks.insert(1, Check('Hallucination', not failed, f"{sum(r.get('hallucinations', 0) for r in rows)} (pass = 0)", names(failed)))
    numerator = sum(r.get('wrong_missing', 0) + (r.get('expected', 0) if r['nothing_found'] else 0) for r in rows)
    denominator = sum(len(r.get('needs', [])) + (r.get('expected', 0) if r['nothing_found'] else 0) for r in rows)
    failed = [r for r in rows if r['error'] or r.get('wrong_missing', 0) or (r['nothing_found'] and r.get('expected', 0))]
    checks.append(Check('Wrong Abstention', not any(r['error'] for r in rows) and (not denominator or numerator / denominator <= .1), f'{numerator}/{denominator} (pass <= 10%)', names(failed)))
    selected = [r for r in report.questions if r['question']['changed_mind']]
    failed = [r for r in selected if r['error'] or not r.get('current_decision')]
    checks.append(Check('Current Decision', not failed, f'{len(selected)-len(failed)}/{len(selected)} (pass = 100%)', names(failed)))
    shortfalls = TestSet([r['question'] for r in report.questions], 1).shortfalls
    checks.append(Check('Overall', all(c.passed for c in checks) and not shortfalls,
                        'Test Set shortfall: ' + ', '.join(shortfalls) if shortfalls else 'all five checks', []))
    return checks


def write_review(report, folder):
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / (datetime.now().strftime('%Y%m%d-%H%M%S-%f') + '.md')
    lines = ['# Quality review', '', *(f'{k}: {v}' for k, v in report.settings.items()), '', floor_text(report), '',
             '<!-- quality-data ' + json.dumps({'questions': report.questions, 'settings': report.settings}, ensure_ascii=False).replace('-->', r'--\u003e') + ' -->']
    for row in report.questions:
        q = row['question']
        lines.extend(['', f"## Q{q['id']}: {q['question']} ({q['label']})", '',
                      row['error'] or row['pack'] or 'Nothing found in your chats for this',
                      f"Match Score: {row.get('match_score') or 'none'}",
                      'Needs: ' + (', '.join(row.get('needs', [])) or 'none'),
                      '', f"Automatic: Finding {'pass' if row['finding'] else 'fail'}" if q['label'] != 'unanswerable'
                      else f"Automatic: Correct Abstention {'pass' if row['nothing_found'] and not row['error'] else 'fail'}"])
        if q['changed_mind']:
            lines[-1] += f" · Current Decision {'pass' if row.get('current_decision') and not row['error'] else 'fail'}"
        if q['label'] != 'unanswerable' and not row['error']:
            lines.extend(['Hallucinations: ____', 'Needs wrongly missing: ____'])
            if q['label'] == 'partly':
                lines.append('Missing needs named exactly (yes/no): ____')
            if row['nothing_found']:
                lines.append('Needs you expected: ____')
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return path


def read_review(path):
    text = Path(path).read_text(encoding='utf-8')
    try:
        data = json.loads(text.split('<!-- quality-data ', 1)[1].split(' -->', 1)[0])
        sections = text.split('\n## Q')[1:]
        if len(sections) != len(data['questions']):
            raise ValueError('question sections do not match')
        for row, section in zip(data['questions'], sections):
            q = row['question']
            if not section.startswith(f"{q['id']}: {q['question']} ("):
                raise ValueError(f"{q['question']}: question section does not match")
            if q['label'] == 'unanswerable' or row['error']:
                continue
            for label, field in (('Hallucinations', 'hallucinations'), ('Needs wrongly missing', 'wrong_missing'),
                                 ('Missing needs named exactly (yes/no)', 'missing_exact'), ('Needs you expected', 'expected')):
                values = [line[len(label)+2:].strip() for line in section.splitlines() if line.startswith(label + ': ')]
                value = values[0] if len(values) == 1 else ''
                row[field] = value if field == 'missing_exact' else int(value) if value.isdigit() else None
        return Report(data['questions'], data['settings'])
    except (IndexError, KeyError, ValueError, TypeError) as e:
        raise ValueError(f'Invalid review file: {path}') from e
