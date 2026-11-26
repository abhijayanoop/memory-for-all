"""Build a Context Pack from quotes selected by a writing model."""
import json
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass

PACK_LIMIT = 9500
LOCAL_MODEL = "qwen3:4b-instruct"
NOT_FOUND_FLOOR = 0.0  # untuned; spec 4 will calibrate against the Test Set


class WritingModelError(RuntimeError):
    """A writing model could not produce a JSON object."""


class LocalWriter:
    name = LOCAL_MODEL

    def ask(self, prompt):
        payload = json.dumps({"model": self.name, "prompt": prompt, "stream": False,
                              "format": "json", "options": {"temperature": 0}}).encode()
        req = urllib.request.Request("http://localhost:11434/api/generate", data=payload,
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=120) as response:
                answer = json.loads(response.read())["response"]
            result = json.loads(answer)
            if not isinstance(result, dict):
                raise ValueError("expected an object")
            return result
        except (OSError, ValueError, KeyError, TypeError) as e:
            raise WritingModelError(f"Local writing model failed. Start Ollama, then run: ollama pull {LOCAL_MODEL}") from e


@dataclass
class DroppedQuote:
    quote: str
    reason: str


@dataclass
class Decision:
    quote: str
    sources: list[int]


@dataclass
class PackResult:
    text: str | None
    nothing_found: bool
    sources: list
    decisions: list
    dropped: list
    seconds: float
    over_limit: bool


def _normal(text):
    return re.sub(r"\W+", " ", text.lower()).strip()


def pack(kb, request, writer):
    started = time.monotonic()
    sources = [h for h in kb.search(request, k=8) if h.score >= NOT_FOUND_FLOOR]
    decisions, dropped = [], []

    def result(text=None):
        return PackResult(text, text is None, sources, decisions, dropped, time.monotonic() - started,
                          text is not None and len(text) > PACK_LIMIT)

    if not sources:
        return result()
    descriptions = "\n\n".join(f"[{i}] {h.chunk.title} ({h.chunk.platform}, {h.chunk.date[:10]})\n{h.chunk.text}"
                                 for i, h in enumerate(sources, 1))
    prompt = ("Choose and order exact quotes from the sources grouped by subject. Do not summarize or draw conclusions. "
              "If sources disagree list both. Return JSON object with subjects, each containing subject, quotes, "
              "replaces, and accepted_by.\nRequest: " + request + "\nSources:\n" + descriptions)
    answer = writer.ask(prompt)
    if not isinstance(answer, dict):
        raise WritingModelError("Writing model returned invalid JSON; check the model and try again.")
    subjects = answer.get("subjects", [])
    if not isinstance(subjects, list):
        subjects = []
    for subject in subjects:
        if not isinstance(subject, dict):
            continue
        quotes = subject.get("quotes", [])
        if not isinstance(quotes, list):
            continue
        for quote in quotes:
            if not isinstance(quote, str):
                continue
            norm = _normal(quote)
            matches = [i for i, h in enumerate(sources, 1) if norm and norm in _normal(h.chunk.text)]
            if matches:
                decisions.append(Decision(quote, matches))
            else:
                dropped.append(DroppedQuote(quote, "not in any source"))
    if not decisions:
        return result()
    lines = ["Context from my past chats (Memory for All):", f"**Request:** {request}", "",
             "**Key decisions and facts:**"]
    lines.extend(f'- "{d.quote}" ' + " ".join(f"[{i}]" for i in d.sources) for d in decisions)
    lines.extend(["", "**Sources:**"])
    source_lines = [f"[{i}] {h.chunk.title} ({h.chunk.platform}, {h.chunk.date[:10]})\n{h.chunk.text}"
                    for i, h in enumerate(sources, 1)]
    text = "\n".join(lines + ["\n\n".join(source_lines)])
    for i in range(len(source_lines) - 1, -1, -1):
        if len(text) <= PACK_LIMIT:
            break
        h = sources[i]
        source_lines[i] = f"[{i + 1}] {h.chunk.title} ({h.chunk.platform}, {h.chunk.date[:10]}) (text left out for length)"
        text = "\n".join(lines + ["\n\n".join(source_lines)])
    return result(text)
