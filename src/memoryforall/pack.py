"""Build a Context Pack from quotes selected by a writing model."""
import json
import os
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field

PACK_LIMIT = 9500
from .embed import KEYS

OPENAI_MODEL = "gpt-4o-mini"
CLAUDE_MODEL = "claude-haiku-4-5-20251001"
LOCAL_MODEL = "qwen3:4b-instruct"
NOT_FOUND_FLOOR = 0.0  # untuned; spec 4 will calibrate against the Test Set


class WritingModelError(RuntimeError):
    """A writing model could not produce a JSON object."""


class WritingModelConnectionError(WritingModelError):
    """The writing model could not be reached."""


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
            error = WritingModelConnectionError if isinstance(e, OSError) and not isinstance(e, urllib.error.HTTPError) else WritingModelError
            raise error(f"Local writing model failed. Start Ollama, then run: ollama pull {LOCAL_MODEL}") from e


class HostedWriter:
    def __init__(self, api):
        self.api = api
        self.name = OPENAI_MODEL if api == "openai" else CLAUDE_MODEL

    def ask(self, prompt):
        key_name = KEYS[self.api]
        key = os.environ.get(key_name)
        if not key:
            raise WritingModelError(f"Hosted pack-writing with {self.api} needs {key_name} in the environment.")
        payload = {"model": self.name, "temperature": 0, "messages": [{"role": "user", "content": prompt}]}
        headers = {"Content-Type": "application/json"}
        if self.api == "openai":
            url = "https://api.openai.com/v1/chat/completions"
            headers["Authorization"] = f"Bearer {key}"
            payload["response_format"] = {"type": "json_object"}
        else:
            url = "https://api.anthropic.com/v1/messages"
            headers.update({"x-api-key": key, "anthropic-version": "2023-06-01"})
            payload["max_tokens"] = 4096
        req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=120) as response:
                data = json.loads(response.read())
            answer = data["choices"][0]["message"]["content"] if self.api == "openai" else data["content"][0]["text"]
            result = json.loads(answer)
            if not isinstance(result, dict):
                raise ValueError("expected an object")
            return result
        except (OSError, ValueError, KeyError, TypeError, IndexError) as e:
            error = WritingModelConnectionError if isinstance(e, OSError) and not isinstance(e, urllib.error.HTTPError) else WritingModelError
            raise error(f"Hosted pack-writing with {self.api} failed; check {key_name}, API access and billing, then try again.") from None


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
    replaced: list = field(default_factory=list)
    acceptance: object = None
    suggested: bool = False


@dataclass
class Need:
    need: str
    covered: bool
    quote: str | None


@dataclass
class MatchScore:
    percentage: int
    missing_needs: list[str]
    text: str


@dataclass
class PackResult:
    text: str | None
    nothing_found: bool
    sources: list
    decisions: list
    needs: list
    dropped: list
    seconds: float
    over_limit: bool
    match_score: MatchScore | None


def _normal(text):
    return re.sub(r"\W+", " ", text.lower()).strip()


def _find(text, quote):
    return (" " + _normal(text) + " ").find(" " + quote + " ")


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
    decisions, needs, dropped = [], [], []

    def result(text=None):
        match_score = None
        if text is not None and needs:
            missing = [need.need for need in needs if not need.covered]
            percentage = round(100 * (len(needs) - len(missing)) / len(needs))
            score_text = f"{percentage}%" + (f": missing {', '.join(missing)}" if missing else "")
            match_score = MatchScore(percentage, missing, score_text)
        return PackResult(text, text is None, sources, decisions, needs, dropped, time.monotonic() - started,
                          text is not None and len(text) > PACK_LIMIT, match_score)

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
    def verify(quote):
        if not isinstance(quote, str) or not quote:
            return None, []
        norm = _normal(quote)
        if len(norm) < 12:
            dropped.append(DroppedQuote(quote, "too short"))
            return None, []
        matches = [(i, speaker, pos, _find(text, norm))
                   for i, h in enumerate(sources, 1)
                   for pos, (speaker, text) in enumerate(_messages(h.chunk)) if _find(text, norm) >= 0]
        if matches:
            indexes = list(dict.fromkeys(i for i, _, _, _ in matches))
            i, speaker, _, _ = max(matches, key=lambda m: (sources[m[0] - 1].chunk.date, -m[0]))
            return Decision(quote, indexes, speaker, sources[i - 1].chunk.date), matches
        bodies = [h.chunk.text.partition("\n")[2] for h in sources]
        if any(_find(body, norm) >= 0 for body in bodies):
            reason = "spans two messages"
        elif any(_find(h.chunk.text.partition("\n")[0], norm) >= 0 for h in sources):
            reason = "from the title line"
        else:
            reason = "not in any source"
        dropped.append(DroppedQuote(quote, reason))
        return None, []

    groups = []
    for subject in subjects:
        if not isinstance(subject, dict):
            continue
        quotes = subject.get("quotes", [])
        replacements = subject.get("replaces", [])
        if not isinstance(quotes, list):
            quotes = []
        if not isinstance(replacements, list):
            replacements = []
        verified = []
        valid_replacement = False
        for index, quote in enumerate(quotes + replacements):
            if index >= len(quotes) and any(d.quote == quote for d, _ in verified):
                valid_replacement = True
                continue
            decision, matches = verify(quote)
            if decision:
                verified.append((decision, matches))
                valid_replacement |= index >= len(quotes)
        if not verified:
            continue
        verified.sort(key=lambda pair: pair[0].date, reverse=True)
        displayed = verified
        if valid_replacement:
            current, current_matches = verified[0]
            lead = max(current_matches, key=lambda m: (sources[m[0] - 1].chunk.date, -m[0]))
            lead_chunk = sources[lead[0] - 1].chunk
            accepted, accepted_matches = verify(subject.get("accepted_by", "")) if current.speaker != "You" else (None, [])
            accepted_current = bool(accepted and any(
                speaker == "You"
                and (sources[i - 1].chunk.platform, sources[i - 1].chunk.chat_id) == (lead_chunk.platform, lead_chunk.chat_id)
                and (sources[i - 1].chunk.position, pos, offset) > (lead_chunk.position, lead[2], lead[3])
                for i, speaker, pos, offset in accepted_matches))
            old_pairs = []
            for old, matches in verified[1:]:
                if old.quote not in replacements or old.speaker != "You" or (current.speaker != "You" and not accepted_current):
                    continue
                prior = max(matches, key=lambda m: (sources[m[0] - 1].chunk.date, -m[0]))
                chunk = sources[prior[0] - 1].chunk
                same_chat = (chunk.platform, chunk.chat_id) == (lead_chunk.platform, lead_chunk.chat_id)
                earlier = chunk.date < lead_chunk.date or (chunk.date == lead_chunk.date and same_chat
                           and (chunk.position, prior[2]) < (lead_chunk.position, lead[2]))
                if earlier:
                    old_pairs.append((old, matches))
            current.replaced = [old for old, _ in old_pairs]
            displayed = [pair for pair in verified if pair not in old_pairs]
            if not old_pairs:
                displayed.sort(key=lambda pair: pair[0].speaker == "You", reverse=True)
        for decision, matches in displayed:
            if decision.speaker != "You":
                decision.suggested = True
                acceptance, accepted_matches = verify(subject.get("accepted_by", ""))
                if acceptance:
                    lead = max(matches, key=lambda m: (sources[m[0] - 1].chunk.date, -m[0]))
                    lead_chunk = sources[lead[0] - 1].chunk
                    for i, speaker, pos, offset in accepted_matches:
                        chunk = sources[i - 1].chunk
                        if (speaker == "You" and (chunk.platform, chunk.chat_id) == (lead_chunk.platform, lead_chunk.chat_id)
                                and (chunk.position, pos, offset) > (lead_chunk.position, lead[2], lead[3])):
                            decision.acceptance = Decision(acceptance.quote, [i], "You", chunk.date)
                            decision.suggested = False
                            break
            decisions.append(decision)
        groups.append([d for d, _ in displayed])
    if not decisions:
        return result()
    evidence = [q for d in decisions for q in [d, *d.replaced, *([d.acceptance] if d.acceptance else [])]]
    numbered_quotes = "\n".join(f"[{i}] {d.quote}" for i, d in enumerate(evidence, 1))
    answer = writer.ask("Split the Request alone into 1 to 4 short needs. For each need, identify which "
                        "numbered verified quote covers it, or null if none does. Return JSON object with "
                        "needs, each containing need and quote (a number or null).\nRequest: " + request +
                        "\nVerified quotes:\n" + numbered_quotes)
    if not isinstance(answer, dict):
        raise WritingModelError("Writing model returned invalid JSON; check the model and try again.")
    items = answer.get("needs", [])
    if isinstance(items, list):
        for item in items[:4]:
            if not isinstance(item, dict) or not isinstance(item.get("need"), str) or not item["need"].strip():
                continue
            number = item.get("quote")
            quote = evidence[number - 1].quote if type(number) is int and 1 <= number <= len(evidence) else None
            needs.append(Need(item["need"], quote is not None, quote))
    if not needs:
        raise WritingModelError("Writing model returned no valid needs; check the model and try again.")
    def cite(d):
        return f'"{d.quote}" ' + " ".join(f"[{i}]" for i in d.sources) + f" ({d.date[:10]})"

    current = [group[0] for group in groups if group[0].replaced] or [groups[0][0]]
    lines = ["Context from my past chats (Memory for All):", f"**Request:** {request}", "",
             "**In short:**"]
    def labelled(d):
        label = d.speaker + (" suggested" if d.suggested else "")
        line = f"**{label}:** {cite(d)}"
        if d.acceptance:
            line += f". **You:** {cite(d.acceptance)}"
        return line

    lines.extend(f"- {labelled(d)}" for d in current)
    lines.extend(["", "**Key decisions and facts:**"])
    for d in decisions:
        label = d.speaker + (" suggested" if d.suggested else "")
        line = f"- **{label}:** {cite(d)}"
        for old in d.replaced:
            line += f". Changed from {cite(old)}"
        if d.acceptance:
            line += f". **You:** {cite(d.acceptance)}"
        lines.append(line)
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
