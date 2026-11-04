WITH cohorts AS (
 SELECT 'before' AS arm, :baseline_profile AS profile, :before_start AS lo, :before_end AS hi
 UNION ALL
 SELECT 'after', :treatment_profile, :after_start, :after_end
), selected AS (
 SELECT c.arm, t.* FROM cohorts c JOIN comparison_tool_calls t
 ON t.effective_profile_hash=c.profile AND t.started_at>=c.lo AND t.started_at<c.hi
 WHERE t.repo_id=:repo_id AND t.tool_key=:tool_key AND t.operation=:operation
 AND t.exposure_verified=1
), stats AS (
 SELECT c.arm, COUNT(s.id) AS eligible_calls,
 COUNT(s.model_facing_payload_tokens_estimate) AS known_payload_calls,
 COUNT(s.duration_ms) AS known_duration_calls,
 COUNT(s.success) AS known_outcome_calls,
 SUM(CASE WHEN s.success=0 THEN 1 ELSE 0 END) AS failures,
 SUM(s.model_facing_payload_tokens_estimate) AS known_payload_total,
 AVG(s.model_facing_payload_tokens_estimate) AS mean_payload_tokens,
 AVG(s.duration_ms) AS mean_duration_ms
 FROM cohorts c LEFT JOIN selected s ON c.arm=s.arm GROUP BY c.arm
), wide AS (
 SELECT b.eligible_calls AS before_calls, a.eligible_calls AS after_calls,
 b.known_payload_calls AS before_known_payload, a.known_payload_calls AS after_known_payload,
 b.known_duration_calls AS before_known_duration, a.known_duration_calls AS after_known_duration,
 b.known_outcome_calls AS before_known_outcome, a.known_outcome_calls AS after_known_outcome,
 b.failures AS before_failures, a.failures AS after_failures,
 b.known_payload_total AS before_payload_total, a.known_payload_total AS after_payload_total,
 b.mean_payload_tokens AS before_mean_payload, a.mean_payload_tokens AS after_mean_payload,
 b.mean_duration_ms AS before_mean_duration_ms, a.mean_duration_ms AS after_mean_duration_ms
 FROM stats b JOIN stats a ON b.arm='before' AND a.arm='after'
)
SELECT *, before_mean_payload-after_mean_payload AS absolute_payload_reduction_per_call,
 CASE WHEN before_mean_payload>0 THEN (before_mean_payload-after_mean_payload)*1.0/before_mean_payload END AS payload_reduction_fraction,
 CASE WHEN before_mean_duration_ms>0 THEN (before_mean_duration_ms-after_mean_duration_ms)*1.0/before_mean_duration_ms END AS duration_reduction_fraction
FROM wide;
