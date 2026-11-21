// PROTOTYPE. Paste in DevTools console on chatgpt.com or claude.ai (logged in; `allow pasting` first).
// Downloads your N most recent chats as .json files to your Downloads folder. Nothing is sent anywhere.
// Review the files and delete any you don't want to share before moving them to prototype/data-real/.
(async () => {
  const N = 6;
  const save = (name, obj) => { const a = document.createElement("a"); a.href = URL.createObjectURL(new Blob([JSON.stringify(obj)], { type: "application/json" })); a.download = name; a.click(); };
  const wait = (ms) => new Promise(r => setTimeout(r, ms));
  try {
    if (location.host.includes("chatgpt.com")) {
      const t = (await (await fetch("/api/auth/session")).json()).accessToken, h = { Authorization: `Bearer ${t}` };
      const list = (await (await fetch(`/backend-api/conversations?offset=0&limit=${N}`, { headers: h })).json()).items;
      for (const c of list) { save(`chatgpt-${c.id}.json`, await (await fetch(`/backend-api/conversation/${c.id}`, { headers: h })).json()); await wait(500); }
      console.log("DOWNLOAD done", list.length, "chatgpt chats");
    } else {
      const orgs = await (await fetch("/api/organizations", { credentials: "include" })).json();
      let best = [], org;
      for (const o of orgs) { const l = await (await fetch(`/api/organizations/${o.uuid}/chat_conversations`, { credentials: "include" })).json(); if (l.length > best.length) { best = l; org = o.uuid; } }
      const recent = best.sort((a, b) => b.updated_at.localeCompare(a.updated_at)).slice(0, N);
      for (const c of recent) { save(`claude-${c.uuid}.json`, await (await fetch(`/api/organizations/${org}/chat_conversations/${c.uuid}?tree=True&rendering_mode=messages&render_all_tools=true`, { credentials: "include" })).json()); await wait(500); }
      console.log("DOWNLOAD done", recent.length, "claude chats");
    }
  } catch (e) { console.log("DOWNLOAD ERROR", e); }
})();
