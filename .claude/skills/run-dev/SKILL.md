---
name: run-dev
description: Start the adhdaf dev server on port 1738 and verify it responds
disable-model-invocation: true
---

# Run Dev Server

Start the adhdaf FastAPI dev server and confirm it's healthy.

## Steps

1. Kill any existing process on port 1738:
   ```bash
   lsof -ti:1738 | xargs kill -9 2>/dev/null; true
   ```

2. Start the dev server in the background:
   ```bash
   cd /Users/skeletor/DEV/claude-apps/adhdaf && uv run fastapi dev --port 1738 &
   ```

3. Wait for it to be ready (poll up to 10 seconds):
   ```bash
   for i in $(seq 1 20); do
     curl -sf http://127.0.0.1:1738/health && break
     sleep 0.5
   done
   ```

4. Report the result:
   - If `/health` responded with `{"status":"ok"}`, the server is running.
   - If it didn't respond after 10 seconds, check the server output for errors.

## Notes

- The server binds to `127.0.0.1:1738` (localhost only).
- Use `lsof -ti:1738 | xargs kill -9` to stop it when done.
- Server logs stream to the background process — use the Monitor tool to watch them if needed.
