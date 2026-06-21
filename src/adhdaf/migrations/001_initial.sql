-- ABOUTME: Initial database schema — creates captures, tasks, and nudges tables.
-- ABOUTME: Includes a partial unique index enforcing one focus task at a time.
CREATE TABLE IF NOT EXISTS captures (
    id TEXT PRIMARY KEY,
    raw_text TEXT NOT NULL,
    source TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    error TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    processed_at DATETIME
);

CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    capture_id TEXT REFERENCES captures(id),
    title TEXT NOT NULL,
    notes TEXT,
    checklist JSON,
    status TEXT NOT NULL DEFAULT 'inbox',
    priority TEXT DEFAULT 'medium',
    area TEXT,
    tags JSON DEFAULT '[]',
    source TEXT NOT NULL DEFAULT 'capture',
    position INTEGER NOT NULL DEFAULT 0,
    is_focus BOOLEAN NOT NULL DEFAULT 0,
    due_at DATETIME,
    remind_at DATETIME,
    snoozed_until DATETIME,
    completed_at DATETIME,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS one_focus_task
ON tasks(is_focus)
WHERE is_focus = 1 AND status NOT IN ('done', 'archived');

CREATE TABLE IF NOT EXISTS nudges (
    id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL REFERENCES tasks(id),
    type TEXT NOT NULL,
    message TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    condition_hash TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    sent_at DATETIME,
    dismissed_at DATETIME,
    expires_at DATETIME
)
