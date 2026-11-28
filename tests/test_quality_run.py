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


def test_cli_run_and_score(tmp_path, fake, monkeypatch):
    import json
    from memoryforall.cli import main
    from memoryforall import quality
    monkeypatch.setattr(quality, 'pack', lambda kb, question, writer: SimpleNamespace(text=None, nothing_found=True))
    path = tmp_path / 'quality' / 'test-set.json'
    path.parent.mkdir()
    path.write_text(json.dumps({'questions': [{'id': 1, 'question': 'unknown', 'label': 'unanswerable', 'changed_mind': False, 'right': []}]}))
    monkeypatch.setenv('MEMORYFORALL_CONFIG_DIR', str(tmp_path / 'config'))
    assert main(['quality', 'run', '--kb', str(tmp_path)], embedder=fake, writer=object()) == 0
    assert len(list((tmp_path / 'quality' / 'runs').glob('*.md'))) == 1
    assert main(['quality', 'score', '--kb', str(tmp_path)], embedder=fake) == 0
    monkeypatch.setattr(quality, 'pack', lambda kb, question, writer: SimpleNamespace(text='pack', nothing_found=False))
    assert main(['quality', 'run', '--kb', str(tmp_path)], embedder=fake, writer=object()) == 1
    assert main(['quality', 'score', '--kb', str(tmp_path)], embedder=fake) == 1
