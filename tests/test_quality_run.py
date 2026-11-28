from types import SimpleNamespace
from memoryforall.quality import TestSet, run, score, write_review, read_review


def test_run_scores_finding_and_abstention_and_round_trips(tmp_path, monkeypatch):
    from memoryforall import quality
    hit = SimpleNamespace(chunk=SimpleNamespace(platform='claude', chat_id='a', text='I chose the Katana!'))
    kb = SimpleNamespace(search=lambda question, k: [hit] if question == 'amp' else [])
    monkeypatch.setattr(quality, 'pack', lambda kb, question, writer: SimpleNamespace(text='pack', nothing_found=False) if question == 'amp' else SimpleNamespace(text=None, nothing_found=True))
    questions = [{'id': 1, 'question': 'amp', 'label': 'answerable', 'changed_mind': False, 'right': [{'conversation': 'claude:a', 'phrase': 'chose the katana'}]}, {'id': 2, 'question': 'unknown', 'label': 'unanswerable', 'changed_mind': False, 'right': []}]
    report = run(kb, TestSet(questions, 3), None)
    assert all(check.passed for check in score(report))
    assert all(check.passed for check in score(read_review(write_review(report, tmp_path))))


def test_wrong_conversation_and_writer_failure_fail_checks(monkeypatch):
    from memoryforall import quality
    from memoryforall.pack import WritingModelError
    hit = SimpleNamespace(chunk=SimpleNamespace(platform='claude', chat_id='other', text='I chose the Katana'))
    kb = SimpleNamespace(search=lambda question, k: [hit])
    def fake_pack(kb, question, writer):
        if question == 'later':
            raise WritingModelError('writer failed')
        return SimpleNamespace(text='pack', nothing_found=False)
    monkeypatch.setattr(quality, 'pack', fake_pack)
    q = {'id': 1, 'question': 'amp', 'label': 'answerable', 'changed_mind': False, 'right': [{'conversation': 'claude:a', 'phrase': 'chose the katana'}]}
    report = run(kb, TestSet([q, {**q, 'id': 2, 'question': 'later'}], 3), None)
    assert score(report)[0].failures == ['amp', 'later']
    assert report.questions[1]['error'] == 'writer failed'


def test_finding_only_uses_top_eight_after_rechunking(monkeypatch):
    from memoryforall import quality
    other = SimpleNamespace(chunk=SimpleNamespace(platform='claude', chat_id='b', text='right phrase'))
    right = SimpleNamespace(chunk=SimpleNamespace(platform='claude', chat_id='a', text='new chunk: RIGHT, phrase!'))
    hits = [other] * 8 + [right]
    kb = SimpleNamespace(search=lambda question, k: hits)
    monkeypatch.setattr(quality, 'pack', lambda kb, question, writer: SimpleNamespace(text='pack', nothing_found=False))
    q = {'id': 1, 'question': 'where', 'label': 'answerable', 'changed_mind': False, 'right': [{'conversation': 'claude:a', 'phrase': 'right phrase'}]}
    assert not score(run(kb, TestSet([q], 2), None))[0].passed
    hits.insert(0, hits.pop())
    assert score(run(kb, TestSet([q], 2), None))[0].passed


def test_cli_run_and_score(tmp_path, fake, monkeypatch, capsys):
    import json
    from memoryforall.cli import main
    from memoryforall import quality
    monkeypatch.setattr(quality, 'pack', lambda kb, question, writer: SimpleNamespace(text=None, nothing_found=True))
    path = tmp_path / 'quality' / 'test-set.json'
    path.parent.mkdir()
    path.write_text(json.dumps({'questions': [{'id': 1, 'question': 'unknown', 'label': 'unanswerable', 'changed_mind': False, 'right': []}]}))
    monkeypatch.setenv('MEMORYFORALL_CONFIG_DIR', str(tmp_path / 'config'))
    assert main(['quality', 'run', '--kb', str(tmp_path)], embedder=fake, writer=object()) == 0
    assert 'Current Decision' in capsys.readouterr().out
    assert len(list((tmp_path / 'quality' / 'runs').glob('*.md'))) == 1
    assert main(['quality', 'score', '--kb', str(tmp_path)], embedder=fake) == 0
    assert 'Current Decision' in capsys.readouterr().out
    monkeypatch.setattr(quality, 'pack', lambda kb, question, writer: SimpleNamespace(text='pack', nothing_found=False))
    assert main(['quality', 'run', '--kb', str(tmp_path)], embedder=fake, writer=object()) == 1
    assert main(['quality', 'score', '--kb', str(tmp_path)], embedder=fake) == 1


def test_current_decision_with_dated_chunks(tmp_path, fake):
    from dataclasses import replace
    from test_search import conv, make
    from test_pack import Writer
    kb = make(tmp_path, fake, [conv('a', 'base text for guitar')])
    chunk = kb.search('guitar')[0].chunk
    old = replace(chunk, date='2025-01-01', text='Chat: title\nUser: I chose the old guitar model')
    new = replace(chunk, date='2025-03-01', text='Chat: title\nUser: I chose the new guitar model')
    kb.search = lambda *a, **kw: [SimpleNamespace(chunk=c, score=1) for c in (old, new)]
    q = {'id': 1, 'question': 'guitar', 'label': 'answerable', 'changed_mind': True,
         'right': [{'conversation': f'{chunk.platform}:{chunk.chat_id}', 'phrase': 'old guitar'}],
         'current': 'NEW guitar', 'replaced': 'old guitar'}
    writer = Writer({'subjects': [{'quotes': ['I chose the new guitar model'],
                                    'replaces': ['I chose the old guitar model']}]})
    report = run(kb, TestSet([q], 2), writer)
    check = next(c for c in score(report) if c.name == 'Current Decision')
    assert check.passed and check.value.startswith('1/1')
    path = write_review(report, tmp_path)
    assert 'Current Decision pass' in path.read_text(encoding='utf-8')
    assert next(c for c in score(read_review(path)) if c.name == 'Current Decision').passed
    for current, replaced in [('missing', 'old guitar'), ('old guitar', 'new guitar')]:
        q = {**q, 'current': current, 'replaced': replaced}
        report = run(kb, TestSet([q], 2), writer)
        assert not next(c for c in score(report) if c.name == 'Current Decision').passed


def test_current_decision_fails_for_nothing_found_and_writer_error(monkeypatch):
    from memoryforall import quality
    from memoryforall.pack import WritingModelError
    kb = SimpleNamespace(search=lambda *a, **kw: [])
    def fake_pack(kb, question, writer):
        if question == 'error':
            raise WritingModelError('writer failed')
        return SimpleNamespace(text=None, nothing_found=True)
    monkeypatch.setattr(quality, 'pack', fake_pack)
    q = {'id': 1, 'question': 'nothing', 'label': 'unanswerable', 'changed_mind': True,
         'right': [], 'current': 'new', 'replaced': 'old'}
    report = run(kb, TestSet([q, {**q, 'id': 2, 'question': 'error'}], 3), None)
    check = next(c for c in score(report) if c.name == 'Current Decision')
    assert not check.passed and check.failures == ['nothing', 'error']
