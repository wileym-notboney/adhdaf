# Apple Shortcut — Voice Capture

Captures a spoken thought straight into adhdaf. Uses a plain HTTP POST — NOT
the "Ask Claude" action (that one can't reach our API).

## Build the Shortcut

1. Open the **Shortcuts** app → **+** to create a new shortcut.
2. Add action **Dictate Text** (Language: your default).
3. Add action **Get Contents of URL**:
   - URL: `http://<your-server-host>:1738/api/capture`
   - Method: **POST**
   - Headers:
     - `Authorization` = `Bearer <CAPTURE_TOKEN>`
     - `Content-Type` = `application/json`
   - Request Body: **JSON**
     - `raw` = (Magic Variable) **Dictated Text**
     - `source` = `voice`
4. Add action **Show Result** with the **Contents of URL** output (shows the
   capture id so you know it saved).
5. Rename the shortcut to **Brain Dump**.

## Use it

Say **"Hey Siri, Brain Dump"**, speak your thought, and it lands in the
`captures` table with `status=pending`. Slice 2 will clean it into a task.

## Notes

- `<your-server-host>` is the LAN IP or hostname of the machine running adhdaf.
- `<CAPTURE_TOKEN>` is the value from your `.env`.
- A 401/403 means the token is missing or wrong; a 422 means the dictation was
  empty.
