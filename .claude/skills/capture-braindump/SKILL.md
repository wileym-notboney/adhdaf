---
name: capture-braindump
description: Send a test brain dump to the local capture endpoint and show the cleaned result. Use when testing the capture→clean→store pipeline.
disable-model-invocation: true
---

# Capture Brain Dump

Send a raw thought to `POST /api/capture` and display what came back.

## Arguments

The user's message after `/capture-braindump` is the brain dump text. If empty, prompt for it.

## Steps

1. Read `CAPTURE_TOKEN` from the project `.env` file:
   ```bash
   grep '^CAPTURE_TOKEN=' /Users/skeletor/DEV/claude-apps/adhdaf/.env | cut -d= -f2-
   ```

2. Check the dev server is running:
   ```bash
   curl -sf http://127.0.0.1:1738/health
   ```
   If it's not responding, tell the user to run `/run-dev` first. Do NOT start it yourself.

3. POST the brain dump:
   ```bash
   curl -s -X POST http://127.0.0.1:1738/api/capture \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"raw": "<brain dump text>", "source": "cli"}'
   ```

4. Display the response:
   - Show the capture ID and status
   - If tasks were created, show their titles, priorities, and due dates
   - If cleaning failed, show the error and note that the raw capture is still saved

## Notes

- The endpoint must exist (Slice 1+). If it 404s, tell the user the capture route isn't built yet.
- Never hardcode the token — always read it from `.env`.
- The `source` field should be `"cli"` for this skill.
