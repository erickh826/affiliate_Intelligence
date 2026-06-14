---
name: review-plan
description: Build a risk-first review plan for specs, pull requests, and system changes. Use when the user asks for review planning, review strategy, readiness checks, or wants a structured checklist before implementation or merge.
disable-model-invocation: true
---

# Review Plan

## Overview

Create a practical, risk-first plan before code review or implementation review starts. Focus on correctness, regressions, security, data integrity, and test confidence.

## When To Use

Use this skill when the user asks to:
- make a review plan or review checklist
- define review scope before coding or merge
- evaluate risk for a spec, PR, or architecture change
- produce a test plan tied to changed areas

## Required Inputs

Collect these first:
1. Change target (spec, files, module, PR, or feature)
2. Critical user paths affected
3. Known risky areas (auth, payments, data writes, migrations, integrations)
4. Constraints (deadline, environment, available tests)

If any are missing, state assumptions clearly.

## Review Workflow

### Step 1: Scope and Risk Map

Define:
- In scope
- Out of scope
- Highest-risk components (rank high/medium/low)

Prioritize areas with irreversible side effects, security impact, or user-visible regressions.

### Step 2: Evidence Plan

For each risky area, define:
- What to inspect (files, logic paths, configs, infra contracts)
- What to run (unit/integration/e2e/manual tests)
- What signals indicate failure (logs, metrics, functional symptoms)

Prefer specific evidence over generic checks.

### Step 3: Review Questions

Create concrete questions per area:
- Correctness: Does behavior match spec and edge cases?
- Safety: Can this introduce data loss, privilege bypass, or leakage?
- Compatibility: Will existing clients/workflows break?
- Operability: Are monitoring, fallback, and error paths adequate?

### Step 4: Deliverable

Output a markdown plan using this structure:

```markdown
# Review Plan: <change>

## Scope
- In scope:
- Out of scope:

## Risk Ranking
- High:
- Medium:
- Low:

## Review Checklist
- [ ] Logic correctness and edge cases
- [ ] Security and permission boundaries
- [ ] Data integrity and migration safety
- [ ] Backward compatibility
- [ ] Error handling and observability
- [ ] Test coverage and gaps

## Validation Plan
- Automated:
- Manual:
- Rollback/Fallback:

## Exit Criteria
- [ ] Blocking risks resolved
- [ ] Required tests pass
- [ ] Known gaps documented with owner
```

## Quality Rules

- Keep plan concise and execution-oriented.
- Flag blockers explicitly.
- Separate must-fix issues from follow-up improvements.
- Do not invent evidence; mark unknowns as unknown.

## Resources

- Detailed checklist: [references/review-checklist.md](references/review-checklist.md)
- Template asset: [assets/review-plan-template.md](assets/review-plan-template.md)
- Optional scaffold tool: `node scripts/generate_review_plan.cjs "<change title>"`
