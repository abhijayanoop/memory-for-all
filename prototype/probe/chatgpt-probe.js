// PROTOTYPE probe. In DevTools console on chatgpt.com (logged in): type `allow pasting`, Enter, then paste this. Runs only in your browser; sends nothing anywhere.
(async () => {
  try {
    const t = (await (await fetch("/api/auth/session")).json()).accessToken;
    console.log("PROBE token found:", !!t);
    const h = { Authorization: `Bearer ${t}` };
    const get = async (u) => { const r = await fetch(u, { headers: h }); return { url: u, status: r.status, retry: r.headers.get("retry-after"), body: r.ok ? await r.json() : null }; };
    let a;
    for (const base of ["/backend-api", "/api"]) { a = await get(`${base}/conversations?offset=0&limit=5`); console.log("PROBE list", a.url, a.status); if (a.body) break; }
    const base = a.url.split("/conversations")[0];
    const items = a.body?.items ?? [];
    console.log("PROBE base", base, "| total", a.body?.total, "| item keys", Object.keys(items[0] ?? {}));
    const b = await get(`${base}/conversations?offset=0&limit=5&order=updated`);
    console.log("PROBE order=updated status", b.status, "| same order as default:", JSON.stringify(b.body?.items?.map(i => i.id)) === JSON.stringify(items.map(i => i.id)));
    console.log("PROBE update_times", items.map(i => i.update_time));
    const one = items[0] && await get(`${base}/conversation/${items[0].id}`);
    console.log("PROBE one chat", one?.status, "| keys", Object.keys(one?.body ?? {}), "| nodes", Object.keys(one?.body?.mapping ?? {}).length);
  } catch (e) { console.log("PROBE ERROR", e); }
})();
