import json
import pytest
from memoryforall.cli import main
from memoryforall.kb import KnowledgeBase, validate
from memoryforall.quality import load_test_set

def test_invalid_question_names_field(tmp_path):
    path = tmp_path / 'set.json'
    path.write_text(json.dumps({'questions': [{'id': 1, 'question': 'Where?', 'label': 'answerable', 'changed_mind': False, 'right': []}]}))
    with pytest.raises(ValueError, match='Where.*right'):
        load_test_set(path)

@pytest.mark.parametrize(('change', 'field'), [({'label': 'bad'}, 'label'),
    ({'changed_mind': True}, 'current'), ({'changed_mind': True, 'current': 'new'}, 'replaced')])
def test_other_invalid_fields(tmp_path, change, field):
    path = tmp_path / 'set.json'
    q = {'id': 1, 'question': 'Where?', 'label': 'unanswerable', 'changed_mind': False, 'right': []}
    q.update(change)
    path.write_text(json.dumps({'questions': [q]}))
    with pytest.raises(ValueError, match=f'Where.*{field}'):
        load_test_set(path)

def test_add_and_skip_quality_folder(tmp_path, fake, monkeypatch, capsys):
    kb = KnowledgeBase(tmp_path, fake)
    kb.save(validate({'platform': 'claude', 'chat_id': 'a', 'title': 'Chat', 'created': '2025-01-01T00:00:00Z', 'updated': '2025-01-01T00:00:00Z', 'messages': [{'sender': 'user', 'text': 'I chose the Katana'}, {'sender': 'assistant', 'text': 'ok'}]}))
    kb.refresh_index()
    answers = iter(['1', 'wrong phrase', '1', 'chose the Katana', ''])
    monkeypatch.setattr('builtins.input', lambda prompt='': next(answers))
    assert main(['quality', 'add', 'What amp?', '--label', 'answerable', '--kb', str(tmp_path)], embedder=fake) == 0
    assert 'not found' in capsys.readouterr().out.lower()
    data = load_test_set(tmp_path / 'quality' / 'test-set.json')
    assert data.questions[0]['right'] == [{'conversation': 'claude:a', 'phrase': 'chose the Katana'}]
    (tmp_path / 'quality' / 'fake.md').write_text('---\nplatform: claude\nchat_id: x\ntitle: bad\n')
    assert kb.refresh_index()['skipped'] == 0
    assert len(kb.conversations()) == 1
