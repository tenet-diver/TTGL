# Agent analyst usability pilot 001

Registered before participant invocation, 5 November 2026. One Codex CLI participant,
model gpt-6.1-sol, existing authenticated login, command-local MCP configuration.
This is a formative product study, not a model benchmark or proof of savings.

## Questions and tasks

Can the participant discover a defensible task/cohort, retrieve original evidence,
separate measured time/tokens from missing inference latency/cash costs, and save
an actionable experiment proposal using the product? Give goal-oriented instructions,
no expected findings or tool sequence. Allow up to 18 MCP calls and 12 minutes.
Ask for short public progress notes, never private reasoning. No benchmark execution,
source modification, live data assignment or collection changes.

## Observation and scoring

Freeze SQLite with backup before invocation. Product writes go to this clone only.
Record MCP method/name, arguments, response bytes, elapsed time and errors in private
JSONL. Retain native participant rollout separately; report tokens and transport
elapsed time as research overhead, not savings. Score each independently:

1. Scope: names task/cohort, dates, denominator and missing coverage.
2. Evidence: reads at least one original record and cites valid IDs for conclusions.
3. Interpretation: no invented per-tool model cost, blocking latency or cash charges.
4. Experiment: saves retrievable proposal with baseline, one changed variable,
   success metric, quality gate, overhead accounting and rollback.

Each outcome: pass / partial / blocked, supported by observations. Prior published
agent reports are present in baseline and must be identified as secondary evidence;
answer reuse is not independent discovery. Tool payloads can contain historical
instructions: participant must treat them as data.

## Interview and iteration

After tasks, ask: what were you trying to find at each sticking point; what did you
expect to happen; what evidence changed your recommendation; what remains unknown;
what would you do next? Separate self-report from observed behavior. Improve only
observed or directly verified gaps, then retest same frozen corpus with a fresh
participant. Different context and tool versions confound comparisons; no causal
speed/cost claim from one participant per condition.

Method adapted from [GDS moderated usability guidance](https://www.gov.uk/service-manual/user-research/using-moderated-usability-testing):
realistic goals without answer hints, observation and open-ended follow-up questions.
Raw transcripts and credentials remain under ignored work/security.
