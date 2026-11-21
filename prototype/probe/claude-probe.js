// PROTOTYPE probe. Paste into the DevTools console on claude.ai while logged in. Runs only in your browser; sends nothing anywhere.
(async () => {
  const get = async (u) => { const r = await fetch(u, { credentials: "include", headers: { Accept: "application/json" } }); return { status: r.status, retry: r.headers.get("retry-after"), body: r.ok ? await r.json() : null }; };
  const orgs = await get("/api/organizations");
  const org = orgs.body?.[0]?.uuid;
  console.log("orgs", orgs.status, "count", orgs.body?.length);
  const list = await get(`/api/organizations/${org}/chat_conversations`);
  const items = list.body ?? [];
  console.log("list status", list.status, "| count", items.length, "| item keys", Object.keys(items[0] ?? {}));
  console.log("has updated_at on list items:", "updated_at" in (items[0] ?? {}));
  const one = items[0] && await get(`/api/organizations/${org}/chat_conversations/${items[0].uuid}?tree=True&rendering_mode=messages&render_all_tools=true`);
  console.log("one chat status", one?.status, "| keys", Object.keys(one?.body ?? {}), "| message keys", Object.keys(one?.body?.chat_messages?.[0] ?? {}));
})();
