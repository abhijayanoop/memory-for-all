"""Build a Context Pack from quotes selected by a writing model."""
import json
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass

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
    speaker: str
    date: str


@dataclass
class PackResult:
    text: str | None
    nothing_found: bool
    sources: list
    decisions: list
    dropped: list
    seconds: float


def _normal(text):
    return re.sub(r"\W+", " ", text.lower()).strip()


def _messages(chunk):
    body = chunk.text.partition("\n")[2]
    if chunk.kind == "notes":
        return [("You", body.removeprefix("My notes:\n"))]
    parts = re.split(r"(?m)^(User|Assistant): ", body)
    return [("You" if role == "User" else {"chatgpt": "ChatGPT", "claude": "Claude"}.get(chunk.platform.lower(), chunk.platform), text)
            for role, text in zip(parts[1::2], parts[2::2])]


def pack(kb, request, writer):
    started = time.monotonic()
    sources = [h for h in kb.search(request, k=8) if h.score >= NOT_FOUND_FLOOR]
    decisions, dropped = [], []

    def result(text=None):
        return PackResult(text, text is None, sources, decisions, dropped, time.monotonic() - started)

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
            if len(norm) < 12:
                dropped.append(DroppedQuote(quote, "too short"))
                continue
            matches = [(i, speaker) for i, h in enumerate(sources, 1)
                       for speaker, text in _messages(h.chunk) if norm in _normal(text)]
            if matches:
                indexes = list(dict.fromkeys(i for i, _ in matches))
                i, speaker = max(matches, key=lambda match: (sources[match[0] - 1].chunk.date, -match[0]))
                decisions.append(Decision(quote, indexes, speaker, sources[i - 1].chunk.date))
            else:
                bodies = [h.chunk.text.partition("\n")[2] for h in sources]
                if any(norm in _normal(body) for body in bodies):
                    reason = "spans two messages"
                elif any(norm in _normal(h.chunk.text.partition("\n")[0]) for h in sources):
                    reason = "from the title line"
                else:
                    reason = "not in any source"
                dropped.append(DroppedQuote(quote, reason))
    if not decisions:
        return result()
    lines = ["Context from my past chats (Memory for All):", f"**Request:** {request}", "",
             "**Key decisions and facts:**"]
    lines.extend(f'- **{d.speaker}:** "{d.quote}" ' + " ".join(f"[{i}]" for i in d.sources) + f" ({d.date[:10]})" for d in decisions)
    lines.extend(["", "**Sources:**", descriptions])
    return result("\n".join(lines))
