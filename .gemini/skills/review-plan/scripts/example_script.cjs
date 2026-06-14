#!/usr/bin/env node

function esc(input) {
  return String(input ?? "").trim();
}

function main() {
  const change = esc(process.argv.slice(2).join(" ")) || "Unnamed change";

  const output = `# Review Plan: ${change}

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
`;

  process.stdout.write(output);
}

main();
