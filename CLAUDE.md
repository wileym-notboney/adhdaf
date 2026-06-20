# CLAUDE.md — ADHD Productivity System

> Purpose: orient any new Claude session on this project. It explains **what the
> user is trying to do, what has been tried (and abandoned) so far, what was ruled
> out and why, and the open decisions to resolve next.** Read this fully before
> planning or building.

_Last updated: 2026-06-18_

---

## 1. Who I am (the user)

- I have ADHD. My three hardest struggles, in order: **starting tasks**,
  **remembering / follow-through**, and **distraction / focus**.
- I'm a **beginner** with code and technical setup. Explain in plain terms, use
  analogies, don't assume jargon.
- Keep answers **concise and direct**.
- I like documentation captured as clear, indexable docs.

### Design principle that must guide everything
The #1 failure mode for ADHD tools is that *setting them up becomes a new
procrastination project*. Favor the **smallest thing that reduces friction** over
anything elaborate. A plain tool I actually use beats a fancy one I abandon.
Capture must be effortless; the system should come **to** me, not wait to be checked.

---

## 2. The goal

A low-friction loop: **Capture → Clean → Store/See.**

1. **Capture** a messy thought with near-zero effort, from phone or computer.
2. **Clean** it automatically with AI into a clear, manageable task.
3. It lands somewhere I can manage and glance at it.

### Current chosen direction
A **very minimal input system that leverages the Claude API (Haiku model)** to do
the cleaning. Haiku is fast and cheap — well-suited to turning a raw dump into
structured tasks. The **storage backend is being decided and is NO LONGER Notion**
(see §6).

---

## 3. Project history — what's been tried

**Iteration 0 — abandoned.**
Path: `/Users/skeletor/DEV/claude-apps/productivty-tool`
An earlier attempt at this project that was started and then abandoned. _(Its
contents were not reviewed in this session — that folder is not mounted here.
Revisit it directly for any salvageable code, ideas, or lessons before rebuilding.)_

**Iteration 1 — Notion-based (now being moved away from).**
Built in Notion: a `Brain Dump — ADHD Command Center` database with a Kanban board
(workspace + monitor display), a capture Form view, a Cowork "Capture Box" HTML
artifact that cleaned dumps on intake, and a guide page. **Decision: Notion will no
longer be the manager/backend.** These assets still exist (see §7) for reference or
migration only — treat them as deprecated.

**Iteration 2 — current (this workspace).**
Path: `/Users/skeletor/DEV/claude-apps/adhdaf`
Building the minimal Haiku-powered input system with a yet-to-be-decided backend.

---

## 4. Decisions & dead-ends (don't re-pitch)

- **Notion dropped** as the backend / where tasks are managed.
- **Plain browser page reading/writing a cloud app directly** → blocked by browser
  security (CORS). Needs a bridge or a server/API in between.
- **Apple Shortcuts "Ask Claude" action → write to an app** → the action only
  *returns an answer*; it can't run connectors/tools, so it can't file tasks on its
  own. Hands-free "Hey Siri → app" via this action is a dead end.
- **Scheduled nightly "tidy" job** → rejected. Cleaning must happen **on intake**,
  not in a batch.
- **Confirmed working:** the Claude iOS app + a connector reliably writes tasks
  (this is why the Haiku-API path is promising).

---

## 5. Capture operating spec (storage-agnostic structuring rules)

When given a brain dump: **clean it and file it automatically, then report what you
did** (minimal back-and-forth).

- Produce the **smallest number of clear, manageable tasks**. Do **not** shred one
  thought into many tiny tasks.
- **Group related steps into ONE task** with a checklist in the notes; only split
  genuinely unrelated things.
- Short, **action-first titles** (start with a verb); fix typos.
- **Pull out dates/deadlines** into a due-date field (resolve relative dates like
  "Friday", "the 30th", "today" against the current date).
- **Guess priority** from language, urgency, timing, and the risk/impact of missing
  the due date (High / Medium / Low).
- Default status = the backend's equivalent of **"to do."**

Example: *"plan mom's birthday next sat — book restaurant, invite family, order
cake"* → **one** task "Plan Mom's birthday dinner", due that Saturday, with the
three steps as a checklist in notes. Not three+ separate tasks.

---

## 6. Open decisions to resolve next (plan & build)

1. **Backend — where do tasks live now that it's not Notion?** Options on the table:
   a simple **local file** (Markdown/JSON in this workspace), a **custom lightweight
   app** we build, or **another existing app** (Reminders/Things/Todoist/etc.).
   _UNDECIDED._
2. **Display — still want an always-on monitor board/timeline, or just capture + a
   simple list?** _UNDECIDED._
3. **Pipeline:** raw text → Claude API (Haiku) cleans per §5 → write to the chosen
   backend.
4. **Phone path:** given the Shortcut dead end, pick the practical phone capture.
5. **Reminders:** how time-sensitive items nudge me.

Keep each step the smallest viable version. Build, let me use it, then iterate.

---

## 7. Legacy reference — deprecated Notion assets (migration only)

Kept in case we want to pull old tasks out before fully leaving Notion:
- Database: `Brain Dump — ADHD Command Center`
- Database ID: `9415814a37c54729abebe28cf32ed8f3`
- Data source ID: `717cbd15-c3a3-4aad-8ee3-aaead172d66b`
- Schema: `Task` (title), `Status` (To Do / In Progress / Completed / Overdue /
  Archive), `Priority` (High / Medium / Low), `Do date` (date), `Notes` (text),
  `Created` (auto).
- Guide page ID: `3820f81a-9666-8104-bbe9-d0ea52cefcb6`
- Cowork artifact id: `adhd-command-center` (the old Capture Box).
