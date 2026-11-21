"""PROTOTYPE (throwaway): turn downloaded ChatGPT/Claude .json chats in data-real/ into the Markdown the pipeline reads (data-real/md/). Newlines inside a message are flattened (shortcut: fine for judging Chunk cuts)."""
import glob, json, os, re
H = os.path.dirname(__file__); out = f"{H}/data-real/md"; os.makedirs(out, exist_ok=True)
flat = lambda s: re.sub(r"[ \t]+", " ", re.sub(r"\s*\n\s*", " ⏎ ", s.strip()))  # keep paragraph breaks as a marker
for p in glob.glob(f"{H}/data-real/*.json"):
    j = json.load(open(p, encoding="utf8")); name = os.path.basename(p)[:-5]; msgs = []
    if name.startswith("chatgpt"):  # walk the tree from the active leaf back to the root
        n = j["current_node"]; path = []
        while n: path.append(j["mapping"][n]); n = j["mapping"][n].get("parent")
        for node in reversed(path):
            m = node.get("message")
            if m and m["author"]["role"] in ("user", "assistant"):
                t = " ".join(x for x in m["content"].get("parts", []) if isinstance(x, str))
                if t.strip(): msgs.append(("User" if m["author"]["role"] == "user" else "Assistant", flat(t)))
        date, title = (j.get("create_time") or 0), j.get("title")
        date = __import__("datetime").datetime.fromtimestamp(date).date() if isinstance(date, (int, float)) else str(date)[:10]; plat = "chatgpt"
    else:
        for m in sorted(j["chat_messages"], key=lambda m: m["index"]):
            t = m.get("text") or " ".join(b.get("text", "") for b in m.get("content", []) if b.get("type") == "text")
            if t.strip(): msgs.append(("User" if m["sender"] == "human" else "Assistant", flat(t)))
        date, title, plat = j["created_at"][:10], j["name"], "claude"
    open(f"{out}/{name}.md", "w", encoding="utf8").write(f"platform: {plat}\ndate: {date}\ntitle: {flat(title or 'untitled')}\n\n" + "\n".join(f"**{r}:** {t}" for r, t in msgs) + "\n")
    print(name, len(msgs), "messages")
