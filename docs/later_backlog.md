# Later Backlog — adhdaf

Features deferred past v0. Not planned, not promised — just captured so good
ideas don't get lost. Pull from here when v0 is stable and actually in use.

---

## Kanban Board (Slice 4)

- Upgrade `board.html` to full kanban columns with drag-drop via SortableJS
- Status change + reorder endpoints (`POST /api/tasks/reorder`)
- Snooze action (task hidden from board, visible in search/all)
- Archive action
- Dark theme CSS

## Reminders / Nudges (Slice 5)

- Nudge detection: overdue, due soon (24h), stale (3+ days), waiting followup (2+ days)
- `remind_at` triggers separate from `due_at`
- Apprise integration via `APPRISE_URLS` env var
- Background asyncio task in lifespan (acceptable for single-user)
- Idempotency via `condition_hash` — don't resend identical nudge
- Cooldown tracking via `sent_at`
- Nudges expire via `expires_at`
- Runs every 15 minutes, gentle factual tone
- Manual "send test notification" endpoint for setup

## Polish (Slice 6)

- Keyboard shortcuts on board
- Mobile-responsive CSS refinements
- Offline capture queue in service worker (complex — defer until app is stable)
- Shell alias packaging
- Import/export: `uv run adhdaf export > backup.json`
- Deployment guide for homelab (Proxmox LXC, systemd service)
- DB backup command: `uv run adhdaf backup` (SQLite backup API, keep 30 daily)

---

## Dead Ends (don't revisit)

- **Notion as backend** — dropped. Legacy assets exist for migration only.
- **Apple Shortcuts "Ask Claude" action** — can't run connectors/tools, only
  returns an answer. Use plain HTTP POST instead.
- **Scheduled nightly "tidy" job** — cleaning must happen on intake, not batch.
- **Plain browser page hitting cloud API directly** — blocked by CORS. Needs
  a server in between.

## Legacy Notion Assets (migration reference only)

- Database: `Brain Dump — ADHD Command Center`
- Database ID: `9415814a37c54729abebe28cf32ed8f3`
- Data source ID: `717cbd15-c3a3-4aad-8ee3-aaead172d66b`
- Schema: `Task` (title), `Status` (To Do / In Progress / Completed / Overdue /
  Archive), `Priority` (High / Medium / Low), `Do date` (date), `Notes` (text),
  `Created` (auto).
- Guide page ID: `3820f81a-9666-8104-bbe9-d0ea52cefcb6`
- Cowork artifact id: `adhd-command-center` (the old Capture Box)
