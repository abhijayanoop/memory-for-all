# extension-local-link

Type: grilling
Status: resolved
Blocked by: -

## Question

How does the extension talk to the local program, and how is that connection kept safe from other websites?

## Answer

- **Connection:** the local program listens on a private local address (127.0.0.1) only your computer can reach; no native messaging in v1.
- **Security:** a one-time pairing step creates a secret key that the extension stores; the program rejects any request without it, so other websites cannot use the address.
- **Starting it:** the user starts the program with one command in v1; the extension shows "app not running, start it with this command" when it cannot connect. Auto-start at login comes later.
- **Sync handshake:** the extension sends a list of chat IDs and update times, the program replies with which ones it needs, and the extension fetches and uploads only those. The program owns what is already saved.
- **Context Pack request:** the extension sends the Request and the target Platform; the program returns the whole pack with Match Score and sources in one response, and the extension shows a "working" indicator meanwhile.
- **Browsers:** Chrome and Chrome-based browsers (Edge, Brave) in v1.
- **When sync runs:** the Readers run inside an open ChatGPT or Claude tab, so sync happens only while a tab of that Platform is open; the extension says "open claude.ai to sync Claude" when none is.
