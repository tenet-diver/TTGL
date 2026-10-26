# Pre-inference software validation

The complete Docker-enabled suite ran 143 tests: 141 passed, one optional test
skipped, and one test failed because its fake Python process did not finish
startup within five seconds on the loaded host. Both subtests passed. The four
real container integration tests passed, including rejection of changed source
and preservation of ignored compiled dependencies after mode normalization.

The standard-library-only fake usage server now starts Python with `-S` to avoid
unrelated site-package loading. The full usage-collector module then passed all
15 tests, including the original bounded timeout and sanitized error checks.
The complete run and follow-up logs/JUnit reports are retained separately.
No scored benchmark assignments had started at either check.
