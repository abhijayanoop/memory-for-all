from dataclasses import replace
from types import SimpleNamespace
from pathlib import Path
from memoryforall.pack import pack
from test_search import conv, make


def test_prototype_database_summary(tmp_path, fake):
    old = Path('prototype/data/c1.md').read_text(encoding='utf8')
    new = Path('prototype/data/c2.md').read_text(encoding='utf8')
    suggestion = next(x.split('**Assistant:** ', 1)[1] for x in old.splitlines() if 'I\'d suggest Postgres' in x)
    chosen = next(x.split('**User:** ', 1)[1] for x in new.splitlines() if 'Decision:' in x)
    kb = make(tmp_path, fake, [conv('a', 'PennyPilot database')])
    base = kb.search('PennyPilot')[0].chunk
    chunks = [replace(base, date='2026-01-10', text='Chat: PennyPilot\nAssistant: ' + suggestion),
              replace(base, date='2026-03-05', chat_id='b', text='Chat: PennyPilot\nUser: ' + chosen)]
    kb.search = lambda *args, **kwargs: [SimpleNamespace(chunk=c, score=1) for c in chunks]
    class Writer:
        def ask(self, prompt):
            if prompt.startswith('Split the Request'):
                return {'needs': [{'need': 'database', 'quote': 1}]}
            return {'subjects': [{'quotes': [chosen, 'SQLite with Litestream backups'], 'replaces': ['SQLite with Litestream backups']}]}
    result = pack(kb, 'Which database did I choose for PennyPilot?', Writer())
    assert 'Changed from "' + 'SQLite with Litestream backups' + '"' not in result.text




def test_prototype_suggestion_is_not_previous_decision(tmp_path, fake):
    old = Path('prototype/data/c1.md').read_text(encoding='utf8')
    suggestion = next(x.split('**Assistant:** ', 1)[1] for x in old.splitlines() if "I'd suggest Postgres" in x)
    chosen = Path('prototype/data/c2.md').read_text(encoding='utf8').split('**User:** ', 1)[1].splitlines()[0]
    kb = make(tmp_path, fake, [conv('a', 'PennyPilot database')])
    base = kb.search('PennyPilot')[0].chunk
    chunks = [replace(base, date='2026-01-10', text='Chat: PennyPilot\nAssistant: ' + suggestion),
              replace(base, date='2026-03-05', chat_id='b', text='Chat: PennyPilot\nUser: ' + chosen)]
    kb.search = lambda *args, **kwargs: [SimpleNamespace(chunk=c, score=1) for c in chunks]
    class Writer:
        def ask(self, prompt):
            if prompt.startswith('Split the Request'):
                return {'needs': [{'need': 'database', 'quote': 1}]}
            return {'subjects': [{'quotes': [suggestion, chosen], 'replaces': [suggestion]}]}
    result = pack(kb, 'Which database did I choose for PennyPilot?', Writer())
    assert 'Changed from "' + suggestion + '"' not in result.text
    assert '**Claude suggested:** "' + suggestion + '"' in result.text


def test_assistant_response_cannot_replace_user_decision(tmp_path, fake):
    data = Path('prototype/data/c2.md').read_text(encoding='utf8')
    chosen = data.split('**User:** ', 1)[1].splitlines()[0]
    response = data.split('**Assistant:** ', 1)[1].splitlines()[0]
    kb = make(tmp_path, fake, [conv('a', 'PennyPilot database')])
    base = kb.search('PennyPilot')[0].chunk
    chunk = replace(base, date='2026-03-05', text='Chat: PennyPilot\nUser: ' + chosen + '\nAssistant: ' + response)
    kb.search = lambda *a, **kw: [SimpleNamespace(chunk=chunk, score=1)]
    class Writer:
        def ask(self, prompt):
            if prompt.startswith('Split the Request'):
                return {'needs': [{'need': 'database', 'quote': 1}]}
            return {'subjects': [{'quotes': [response], 'replaces': ['SQLite with Litestream backups']}]}
    result = pack(kb, 'Which database did I choose for PennyPilot?', Writer())
    assert 'Changed from' not in result.text
    assert '**You:** "SQLite with Litestream backups"' in result.text.split('**Key decisions')[0]
    assert '**Claude suggested:** "' + response + '"' in result.text
