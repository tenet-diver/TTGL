PRAGMA foreign_keys = ON;
CREATE TABLE optimization_history (
 id TEXT PRIMARY KEY,
 proposal_version INTEGER NOT NULL CHECK(proposal_version>0),
 decision TEXT NOT NULL CHECK(decision IN ('pending','accepted','declined','deferred','withdrawn')),
 implementation TEXT NOT NULL CHECK(implementation IN ('not_started','applying','applied_unverified','implemented','failed','rolled_back','superseded')),
 evaluation TEXT NOT NULL CHECK(evaluation IN ('not_planned','baseline_ready','collecting','ready','complete','inconclusive','invalidated')),
 outcome TEXT CHECK(outcome IN ('better','worse','mixed','no_detected_change','inconclusive')),
 tool_key TEXT NOT NULL, recipe_id TEXT NOT NULL, scope_repo TEXT NOT NULL
);
CREATE TABLE optimization_events (
 event_id TEXT PRIMARY KEY,
 optimization_id TEXT NOT NULL REFERENCES optimization_history(id),
 event_type TEXT NOT NULL, occurred_at TEXT NOT NULL, observed_at TEXT NOT NULL,
 idempotency_key TEXT NOT NULL UNIQUE, payload_json TEXT NOT NULL
);
CREATE INDEX optimization_events_case_time ON optimization_events(optimization_id,occurred_at);
CREATE TABLE comparison_tool_calls (
 id TEXT PRIMARY KEY, repo_id TEXT NOT NULL, tool_key TEXT NOT NULL,
 operation TEXT NOT NULL, started_at TEXT NOT NULL,
 effective_profile_hash TEXT, exposure_verified INTEGER NOT NULL CHECK(exposure_verified IN (0,1)),
 model_facing_payload_tokens_estimate INTEGER CHECK(model_facing_payload_tokens_estimate>=0),
 duration_ms REAL CHECK(duration_ms>=0), success INTEGER CHECK(success IN (0,1))
);
CREATE INDEX comparison_calls_scope ON comparison_tool_calls(repo_id,tool_key,operation,effective_profile_hash,started_at);
