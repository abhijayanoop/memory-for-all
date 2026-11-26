from memoryforall.pack import pack
from test_search import conv, make


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
    assert writer.calls == 1


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
