from memoryforall.pack import pack
from test_search import conv, make


def test_quote_rules_and_speaker(tmp_path, fake):
    from memoryforall.kb import validate
    c = validate({'platform': 'chatgpt', 'chat_id': 'a', 'title': 'Unique title words only',
                  'created': '2025-01-01T00:00:00Z', 'updated': '2025-01-01T00:00:00Z',
                  'messages': [{'sender': 'user', 'text': 'I prefer a wooden guitar'},
                               {'sender': 'assistant', 'text': 'Choose a bright amplifier'}]})
    kb = make(tmp_path, fake, [c])
    writer = Writer({'subjects': [{'quotes': ['I prefer a wooden guitar', 'Choose a bright amplifier', 'yes',
                                                'wooden guitar Assistant Choose a bright', 'Unique title words only'],
                                   'speaker': 'user'}]})
    result = pack(kb, 'guitar', writer)
    assert '**You:** "I prefer a wooden guitar" [1] (2025-01-01)' in result.text
    assert '**ChatGPT suggested:** "Choose a bright amplifier" [1] (2025-01-01)' in result.text
    assert [d.reason for d in result.dropped] == ['too short', 'spans two messages', 'from the title line']


def test_matching_sources_choose_newest_and_ranked_speaker(tmp_path, fake):
    from dataclasses import replace
    from types import SimpleNamespace
    kb = make(tmp_path, fake, [conv('a', 'The shared guitar has six strings')])
    hit = kb.search('guitar')[0]
    text = 'The shared guitar has six strings'
    first = replace(hit.chunk, text='Chat: first\nUser: ' + text, date='2025-01-01')
    second = replace(hit.chunk, text='Chat: second\nAssistant: ' + text, platform='chatgpt', date='2025-02-01')
    kb.search = lambda *args, **kwargs: [SimpleNamespace(chunk=c, score=1) for c in (first, second)]
    result = pack(kb, 'guitar', Writer({'subjects': [{'quotes': [text]}]}))
    assert '**ChatGPT suggested:** "' + text + '" [1] [2] (2025-02-01)' in result.text
    second.date = first.date
    result = pack(kb, 'guitar', Writer({'subjects': [{'quotes': [text]}]}))
    assert '**You:** "' + text + '" [1] [2] (2025-01-01)' in result.text


def test_notes_and_cli_dropped_reason(tmp_path, fake, capsys, monkeypatch):
    from memoryforall.cli import main
    monkeypatch.setenv('MEMORYFORALL_CONFIG_DIR', str(tmp_path / 'config'))
    kb = make(tmp_path / 'kb', fake, [conv('a', 'other things')])
    p = next(kb.folder.rglob('*.md'))
    p.write_bytes(p.read_bytes() + b'my own important guitar notes\n')
    kb.refresh_index()
    writer = Writer({'subjects': [{'quotes': ['my own important guitar notes', 'yes']}]})
    assert main(['pack', 'guitar', '--kb', str(kb.folder)], embedder=fake, writer=writer) == 0
    out = capsys.readouterr()
    assert '**You:** "my own important guitar notes"' in out.out
    assert 'Dropped: yes (too short)' in out.err


class Writer:
    name = 'fake'
    def __init__(self, answer):
        self.answer, self.calls = answer, 0
    def ask(self, prompt):
        self.calls += 1
        return self.answer


def test_verified_quote_and_invention(tmp_path, fake):
    kb = make(tmp_path, fake, [conv('a', 'I chose the blue guitar for recording')])
    writer = Writer({'subjects': [{'quotes': ['I CHOSE the blue guitar, for recording!', 'invented words here'], 'source': 99}]})
    result = pack(kb, 'guitar', writer)
    assert 'I CHOSE the blue guitar, for recording!' in result.text
    assert '[1]' in result.text and 'invented words here' not in result.text
    assert result.dropped[0].reason == 'not in any source'
    assert writer.calls == 2


def test_cli_pack_outputs_pack_and_time(tmp_path, fake, capsys, monkeypatch):
    from memoryforall.cli import main
    monkeypatch.setenv('MEMORYFORALL_CONFIG_DIR', str(tmp_path / 'config'))
    kb = make(tmp_path / 'kb', fake, [conv('a', 'I chose the blue guitar for recording')])
    writer = Writer({'subjects': [{'quotes': ['I chose the blue guitar for recording']}]})
    assert main(['pack', 'guitar', '--kb', str(kb.folder)], embedder=fake, writer=writer) == 0
    output = capsys.readouterr()
    assert 'Context from my past chats' in output.out
    assert 'seconds' in output.err


def test_no_hits_no_call_and_empty_request(tmp_path, fake):
    import pytest
    from memoryforall.kb import KnowledgeBase
    kb = KnowledgeBase(tmp_path, fake)
    writer = Writer({})
    assert pack(kb, 'guitar', writer).nothing_found
    assert writer.calls == 0
    with pytest.raises(ValueError, match='empty'):
        pack(kb, ' ', writer)


def test_floor_and_all_dropped(tmp_path, fake, monkeypatch):
    from memoryforall import pack as packmod
    kb = make(tmp_path, fake, [conv('a', 'I chose the blue guitar for recording')])
    writer = Writer({'subjects': [{'quotes': ['invented words here']}]})
    monkeypatch.setattr(packmod, 'NOT_FOUND_FLOOR', 99)
    assert pack(kb, 'guitar', writer).nothing_found and writer.calls == 0
    monkeypatch.setattr(packmod, 'NOT_FOUND_FLOOR', 0)
    result = pack(kb, 'guitar', writer)
    assert result.nothing_found and result.dropped[0].reason == 'not in any source'


def test_invalid_writer_response_and_errors(tmp_path, fake):
    import pytest
    from memoryforall.pack import WritingModelError
    kb = make(tmp_path, fake, [conv('a', 'I chose the blue guitar for recording')])
    with pytest.raises(WritingModelError):
        pack(kb, 'guitar', Writer('not json'))
    class Broken:
        def ask(self, prompt):
            raise WritingModelError('fix it')
    with pytest.raises(WritingModelError, match='fix it'):
        pack(kb, 'guitar', Broken())
    assert pack(kb, 'guitar', Writer({})).nothing_found


def test_cli_nothing_found_and_error(tmp_path, fake, capsys, monkeypatch):
    from memoryforall.cli import main
    from memoryforall.pack import WritingModelError
    monkeypatch.setenv('MEMORYFORALL_CONFIG_DIR', str(tmp_path / 'config'))
    folder = tmp_path / 'kb'
    assert main(['pack', 'guitar', '--kb', str(folder)], embedder=fake, writer=Writer({})) == 0
    output = capsys.readouterr()
    assert 'Nothing found in your chats for this' in output.out and 'reindex' in output.err
    make(folder, fake, [conv('a', 'I chose the blue guitar for recording')])
    class Broken:
        def ask(self, prompt):
            raise WritingModelError('start Ollama')
    assert main(['pack', 'guitar', '--kb', str(folder)], embedder=fake, writer=Broken()) == 1
    output = capsys.readouterr()
    assert output.out == '' and 'start Ollama' in output.err


def test_local_writer_error_and_json(monkeypatch):
    import pytest
    from memoryforall.pack import LocalWriter, WritingModelError
    def unavailable(*args, **kwargs):
        raise OSError('unavailable')
    monkeypatch.setattr('urllib.request.urlopen', unavailable)
    with pytest.raises(WritingModelError, match='ollama pull qwen3:4b-instruct'):
        LocalWriter().ask('prompt')
    class Response:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def read(self): return b'{"response": "not json"}'
    monkeypatch.setattr('urllib.request.urlopen', lambda *args, **kwargs: Response())
    with pytest.raises(WritingModelError):
        LocalWriter().ask('prompt')


import pytest


@pytest.mark.slow
def test_local_pack_end_to_end(tmp_path, record_property):
    import urllib.request
    from memoryforall.kb import KnowledgeBase
    from memoryforall.pack import LocalWriter, WritingModelError
    try:
        with urllib.request.urlopen('http://localhost:11434/api/tags', timeout=2) as response:
            if b'qwen3:4b-instruct' not in response.read():
                pytest.skip('local writing model not pulled')
    except OSError:
        pytest.skip('Ollama is not reachable')
    kb = KnowledgeBase(tmp_path)
    kb.save(conv('a', 'I chose the blue guitar for recording at home.'))
    kb.refresh_index()
    try:
        result = pack(kb, 'What guitar did I choose for recording?', LocalWriter())
    except WritingModelError as e:
        pytest.fail(str(e))
    record_property('pack_seconds', result.seconds)
    assert not result.nothing_found and result.text.startswith('Context from my past chats')
    assert all(any(d.quote.lower() in h.chunk.text.lower() for h in result.sources) for d in result.decisions)


def test_size_limit_cuts_lowest_ranked_source_first(tmp_path, fake):
    quote = 'I chose the blue guitar for recording'
    kb = make(tmp_path, fake, [conv('a', quote + ' ' + 'a' * 4800),
                               conv('b', 'guitar source ' + 'b' * 4800)])
    result = pack(kb, 'guitar', Writer({'subjects': [{'quotes': [quote]}]}))
    assert len(result.text) <= 9500
    assert not result.over_limit
    assert quote in result.text.split('**Sources:**')[0]
    assert f"[1] {result.sources[0].chunk.title}" in result.text
    assert f"[2] {result.sources[1].chunk.title}" in result.text
    assert result.sources[0].chunk.text in result.text
    last = result.sources[-1].chunk
    assert f'[{len(result.sources)}] {last.title} ({last.platform}, {last.date[:10]}) (text left out for length)' in result.text


def test_size_limit_reports_oversized_decisions(tmp_path, fake):
    quote = 'I chose the blue guitar for recording'
    kb = make(tmp_path, fake, [conv('a', quote)])
    result = pack(kb, 'guitar', Writer({'subjects': [{'quotes': [quote] * 300}]}))
    assert result.over_limit
    assert len(result.text) > 9500
    assert quote in result.text.split('**Sources:**')[0]
    assert '(text left out for length)' in result.text


def test_cli_warns_when_decisions_exceed_limit(tmp_path, fake, capsys, monkeypatch):
    from memoryforall.cli import main
    monkeypatch.setenv('MEMORYFORALL_CONFIG_DIR', str(tmp_path / 'config'))
    quote = 'I chose the blue guitar for recording'
    kb = make(tmp_path / 'kb', fake, [conv('a', quote)])
    writer = Writer({'subjects': [{'quotes': [quote] * 300}]})
    assert main(['pack', 'guitar', '--kb', str(kb.folder)], embedder=fake, writer=writer) == 0
    output = capsys.readouterr()
    assert 'exceeds 9,500 characters' in output.err
    assert 'exceeds 9,500 characters' not in output.out
@pytest.mark.parametrize('api,key', [('openai', 'OPENAI_API_KEY'), ('claude', 'ANTHROPIC_API_KEY')])
def test_hosted_pack_requires_key_before_work(tmp_path, fake, monkeypatch, capsys, api, key):
    from memoryforall.cli import main
    import json
    cfg = tmp_path / 'config'
    cfg.mkdir()
    (cfg / 'settings.json').write_text(json.dumps({'pack_mode': 'hosted', 'pack_api': api}))
    monkeypatch.setenv('MEMORYFORALL_CONFIG_DIR', str(cfg))
    monkeypatch.delenv(key, raising=False)
    writer = Writer({})
    folder = tmp_path / 'kb'
    assert main(['pack', 'guitar', '--kb', str(folder)], embedder=fake, writer=writer) == 2
    assert f'Hosted pack-writing with {api} needs {key} in the environment.' in capsys.readouterr().err
    assert writer.calls == 0 and not folder.exists()


@pytest.mark.parametrize('api,key,response', [
    ('openai', 'OPENAI_API_KEY', {'choices': [{'message': {'content': '{"subjects": []}'}}]}),
    ('claude', 'ANTHROPIC_API_KEY', {'content': [{'type': 'text', 'text': '{"subjects": []}'}]}),
])
def test_hosted_writer_http_and_errors(monkeypatch, api, key, response):
    import json
    import urllib.error
    from memoryforall.pack import HostedWriter, WritingModelError
    calls = []
    class Response:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def read(self): return json.dumps(response).encode()
    def send(req, **kwargs):
        calls.append(req)
        return Response()
    monkeypatch.setenv(key, 'secret-value')
    monkeypatch.setattr('urllib.request.urlopen', send)
    writer = HostedWriter(api)
    assert writer.ask('request and chunks') == {'subjects': []}
    body = json.loads(calls[0].data)
    assert body['temperature'] == 0 and body['messages'][0]['content'] == 'request and chunks'
    assert 'secret-value' not in calls[0].data.decode()
    def fail(*args, **kwargs):
        raise urllib.error.HTTPError('url', 401, 'secret-value', {}, None)
    monkeypatch.setattr('urllib.request.urlopen', fail)
    with pytest.raises(WritingModelError) as exc:
        writer.ask('request and chunks')
    assert key in str(exc.value) and 'secret-value' not in str(exc.value)
    monkeypatch.delenv(key)
    with pytest.raises(WritingModelError, match=key):
        writer.ask('request and chunks')

@pytest.mark.parametrize('mode,api', [('local', 'openai'), ('hosted', 'openai'), ('hosted', 'claude')])
def test_cli_selects_writer_from_settings(tmp_path, fake, monkeypatch, mode, api):
    import json
    from memoryforall.cli import main
    from memoryforall import pack as packmod
    cfg = tmp_path / 'config'
    cfg.mkdir()
    (cfg / 'settings.json').write_text(json.dumps({'pack_mode': mode, 'pack_api': api}))
    monkeypatch.setenv('MEMORYFORALL_CONFIG_DIR', str(cfg))
    monkeypatch.setenv('OPENAI_API_KEY', 'key')
    monkeypatch.setenv('ANTHROPIC_API_KEY', 'key')
    selected = []
    def local():
        selected.append('local')
        return Writer({})
    def hosted(name):
        selected.append(name)
        return Writer({})
    monkeypatch.setattr(packmod, 'LocalWriter', local)
    monkeypatch.setattr(packmod, 'HostedWriter', hosted)
    assert main(['pack', 'guitar', '--kb', str(tmp_path / 'kb')], embedder=fake) == 0
    assert selected == [api if mode == 'hosted' else 'local']


def test_needs_use_only_verified_quotes(tmp_path, fake):
    kb = make(tmp_path, fake, [conv('a', 'I chose the blue guitar for recording')])
    class ScriptedWriter:
        def __init__(self): self.calls = 0
        def ask(self, prompt):
            self.calls += 1
            if self.calls == 1:
                return {'subjects': [{'quotes': ['I chose the blue guitar for recording', 'invented words here']}]}
            return {'needs': [{'need': 'guitar choice', 'quote': 1},
                              {'need': 'amplifier choice', 'quote': 2}, {'need': 'price', 'quote': 99}]}
    writer = ScriptedWriter()
    result = pack(kb, 'guitar and amplifier and price', writer)
    assert writer.calls == 2
    assert [(n.need, n.covered, n.quote) for n in result.needs] == [
        ('guitar choice', True, 'I chose the blue guitar for recording'),
        ('amplifier choice', False, None), ('price', False, None)]
    assert 'amplifier choice' not in result.text and 'Match Score' not in result.text


def test_cli_prints_needs_on_stderr(tmp_path, fake, capsys, monkeypatch):
    from memoryforall.cli import main
    monkeypatch.setenv('MEMORYFORALL_CONFIG_DIR', str(tmp_path / 'config'))
    kb = make(tmp_path / 'kb', fake, [conv('a', 'I chose the blue guitar for recording')])
    class ScriptedWriter:
        def __init__(self): self.calls = 0
        def ask(self, prompt):
            self.calls += 1
            return ({'subjects': [{'quotes': ['I chose the blue guitar for recording']}]} if self.calls == 1
                    else {'needs': [{'need': 'guitar choice', 'quote': 1}, {'need': 'price', 'quote': None}]})
    assert main(['pack', 'guitar', '--kb', str(kb.folder)], embedder=fake, writer=ScriptedWriter()) == 0
    output = capsys.readouterr()
    assert 'guitar choice' not in output.out and 'price' not in output.out
    assert 'guitar choice' in output.err and 'covered' in output.err
    assert 'price' in output.err and 'missing' in output.err
def test_current_decision_and_plain_facts(tmp_path, fake):
    from dataclasses import replace
    from types import SimpleNamespace
    kb = make(tmp_path, fake, [conv('a', 'base text for guitar')])
    chunk = kb.search('guitar')[0].chunk
    old = replace(chunk, date='2025-01-01', text='Chat: title\nUser: I chose the old guitar model')
    new = replace(chunk, date='2025-03-01', text='Chat: title\nUser: I chose the new guitar model')
    kb.search = lambda *a, **kw: [SimpleNamespace(chunk=c, score=1) for c in (old, new)]
    result = pack(kb, 'guitar', Writer({'subjects': [{'quotes': ['I chose the old guitar model', 'I chose the new guitar model'], 'replaces': ['I chose the old guitar model']}]}))
    short, rest = result.text.split('**Key decisions and facts:**')
    assert 'I chose the new guitar model' in short
    assert 'I chose the new guitar model' in rest.split('Changed from')[0]
    assert 'Changed from "I chose the old guitar model" [1] (2025-01-01)' in rest
    result = pack(kb, 'guitar', Writer({'subjects': [{'quotes': ['I chose the old guitar model', 'I chose the new guitar model']}]}))
    assert 'Changed from' not in result.text


def test_suggestion_acceptance_requires_later_same_conversation(tmp_path, fake):
    from dataclasses import replace
    from types import SimpleNamespace
    kb = make(tmp_path, fake, [conv('a', 'base text for guitar')])
    chunk = kb.search('guitar')[0].chunk
    suggestion = replace(chunk, platform='chatgpt', position=1, text='Chat: title\nAssistant: You should choose the blue guitar')
    acceptance = replace(chunk, platform='chatgpt', position=2, text='Chat: title\nUser: I agree with the blue guitar')
    sources = [suggestion, acceptance]
    kb.search = lambda *a, **kw: [SimpleNamespace(chunk=c, score=1) for c in sources]
    subject = {'quotes': ['You should choose the blue guitar'], 'accepted_by': 'I agree with the blue guitar'}
    result = pack(kb, 'guitar', Writer({'subjects': [subject]}))
    assert '**ChatGPT:** "You should choose the blue guitar"' in result.text
    assert '**You:** "I agree with the blue guitar"' in result.text
    for invalid in (replace(acceptance, chat_id='other'), replace(acceptance, position=0),
                    replace(acceptance, position=1, text='Chat: title\nUser: I agree with the blue guitar\nAssistant: You should choose the blue guitar')):
        sources[1] = invalid
        result = pack(kb, 'guitar', Writer({'subjects': [subject]}))
        assert '**ChatGPT suggested:** "You should choose the blue guitar"' in result.text
        assert '**You:** "I agree with the blue guitar"' not in result.text

def test_review_quote_regressions(tmp_path, fake):
    from dataclasses import replace
    from types import SimpleNamespace
    kb = make(tmp_path, fake, [conv('a', 'base text for guitar')])
    chunk = kb.search('guitar')[0].chunk
    chunk = replace(chunk, platform='chatgpt', text='Chat: title\nUser: I chose the old guitar model\nAssistant: You should choose the blue guitar\nUser: I agree with the blue guitar and browsed the catalogue today')
    kb.search = lambda *a, **kw: [SimpleNamespace(chunk=chunk, score=1)]
    class Scripted:
        def __init__(self, subject): self.subject, self.calls = subject, 0
        def ask(self, prompt):
            self.calls += 1
            if self.calls == 1: return {'subjects': [self.subject]}
            assert '[2] I chose the old guitar model' in prompt
            assert '[3] I agree with the blue guitar' in prompt
            return {'needs': [{'need': 'old', 'quote': 2}, {'need': 'agreement', 'quote': 3}]}
    subject = {'quotes': ['You should choose the blue guitar'], 'replaces': ['I chose the old guitar model'], 'accepted_by': 'I agree with the blue guitar'}
    result = pack(kb, 'guitar', Scripted(subject))
    short = result.text.split('**Key decisions')[0]
    assert '**ChatGPT:**' in short and '**You:** "I agree with the blue guitar"' in short
    assert [n.quote for n in result.needs] == ['I chose the old guitar model', 'I agree with the blue guitar']
    result = pack(kb, 'guitar', Writer({'subjects': [{'quotes': ['You should choose the blue guitar']}]}))
    assert '**ChatGPT suggested:**' in result.text.split('**Key decisions')[0]
    result = pack(kb, 'guitar', Writer({'subjects': [{'quotes': ['I chose the old guitar model', 'I agree with the blue guitar'], 'replaces': ['invented old choice']}]}))
    assert 'Changed from' not in result.text and len(result.decisions) == 2
    result = pack(kb, 'guitar', Writer({'subjects': [{'quotes': ['browsed the cat']}]}))
    assert result.nothing_found
