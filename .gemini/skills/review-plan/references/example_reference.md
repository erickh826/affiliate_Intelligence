# Review Checklist Reference

Use this reference when creating or executing a review plan.

## 1) Correctness
- Validate happy path and edge cases.
- Check boundary values, null/empty handling, and time/date assumptions.
- Confirm acceptance criteria match actual behavior.

## 2) Security
- Verify authN/authZ boundaries.
- Validate input sanitization and output encoding.
- Check secrets handling and sensitive logging.

## 3) Data and State Safety
- Review writes, deletes, migrations, and idempotency.
- Confirm transactional safety and rollback strategy.
- Validate cache invalidation and eventual consistency behavior.

## 4) Compatibility
- Check API contract changes.
- Review feature flags, defaults, and migration paths.
- Confirm backward compatibility with existing clients.

## 5) Reliability and Operability
- Inspect error handling and retry logic.
- Verify metrics, logs, tracing, and alert coverage.
- Confirm fail-safe behavior for dependency outages.

## 6) Testing
- Map each high-risk item to at least one validation method.
- Prefer deterministic tests for regressions.
- Record test gaps with owner and mitigation.
