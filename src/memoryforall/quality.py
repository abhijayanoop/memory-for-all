import json
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
