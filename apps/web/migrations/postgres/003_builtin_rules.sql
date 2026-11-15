INSERT INTO observatory.steering_rules(id,name,kind,mode,builtin,config,message) VALUES
('builtin-break','Prompt after a break','break','warn',true,'{"minutes":60}','A long break can rebuild the prompt cache. Consider a fresh focused session.'),
('builtin-task-budget','Task budget','task_budget','ask',true,'{"amount":5}','The reported task cost reached its next budget threshold. Review the task before continuing.'),
('builtin-daily-budget','Daily budget','daily_budget','warn',true,'{"amount":100}','The reported daily API-equivalent cost reached its budget threshold.'),
('builtin-main-checkout','No checkout in a main folder','command','warn',true,'{"check":"main-checkout"}','Use an isolated worktree before changing branches in an explicitly reported main folder.'),
('builtin-public-registry','No public npm registry','command','warn',true,'{"check":"public-registry"}','This command refers to a public npm registry. Check the configured dependency policy.'),
('builtin-attribution','No Claude attribution','command','warn',true,'{"check":"claude-attribution"}','Review the requested commit attribution before creating the commit.'),
('builtin-external-writes','Writes to external records','command','warn',true,'{"check":"external-writes"}','Review this external record write before executing it.'),
('builtin-shell-exploration','Shell file exploration','command','warn',true,'{"check":"shell-exploration"}','Prefer bounded file reads and targeted searches. Preserve useful diagnostics.'),
('builtin-context','Large context','context','warn',true,'{"tokens":200000}','Context reached 200,000 reported tokens. Consider compaction or a focused handoff.'),
('builtin-failures','Same call keeps failing','failure_loop','warn',true,'{"count":3}','The same call failed three times. Reassess the cause before repeating it.'),
('builtin-checks','Edits after the last check','stop_check','warn',true,'{}','Edits followed the last successful check, or no successful check was recorded.')
ON CONFLICT(id) DO NOTHING;
