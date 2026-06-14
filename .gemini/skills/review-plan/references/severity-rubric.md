# Severity Rubric

Use this rubric to classify issues found during plan reviews.

| Level | Description | Example |
| :--- | :--- | :--- |
| **P0: Critical** | Fatal flaw that will cause project failure, data loss, or major security breach. Must be fixed before proceeding. | Missing authentication for public API; logic that deletes production database. |
| **P1: Major** | Significant architectural issue or requirement mismatch that will cause substantial rework if not addressed. | Inefficient data model that won't scale; missing error handling in core workflow. |
| **P2: Minor** | Small improvements, edge cases, or stylistic issues. Can be addressed later but recommended to fix now. | Typo in error message; non-idiomatic variable naming; slightly redundant logic. |
| **P3: Cosmetic** | Purely aesthetic or minor documentation improvements. Low priority. | Inconsistent indentation; missing comments in non-critical sections. |
