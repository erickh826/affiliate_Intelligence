---
name: review-plan
description: Multi-model adversarial review of current phase plan. Use before executing any phase.
---

# Review Plan Skill

## Steps

1. **Locate plan file**
   - Default: `.claude/phases/phase-{N}/plan.md` (ask user for N if unclear)
   - Also load: `.claude/spec/system-spec.md` 同 `.claude/context/learnings.md`

2. **Run parallel reviews** (用 Bash tool 並行 call)

   ```bash
   # Gemini: 長 context review，睇埋 spec
   gemini -p "You are reviewing a phase plan against the system spec. 
   Find gaps, missing edge cases, integration risks. 
   Spec: $(cat .claude/spec/system-spec.md)
   Plan: $(cat .claude/phases/phase-$N/plan.md)
   Past learnings: $(cat .claude/context/learnings.md)
   Output: markdown with sections: Critical / Recommended / Nitpick" \
   > /tmp/gemini-review.md

   # Codex: 技術角度 critique
   codex exec "Technical critique of this plan. Focus on: architecture 
   smells, missing error handling, testability issues. 
   $(cat .claude/phases/phase-$N/plan.md)" \
   > /tmp/codex-review.md

   # DeepSeek (adversarial): via aider or direct
   aider --model deepseek/deepseek-reasoner --message \
   "Act as a senior engineer rejecting this plan. List top 5 fatal flaws 
   with reasoning: $(cat .claude/phases/phase-$N/plan.md)" \
   --no-auto-commits > /tmp/deepseek-review.md


3.  Synthesize

讀三個 review output
De-duplicate issues（同一個問題唔同 model 提就 merge）
按 severity 分類：Critical / Recommended / Nitpick
輸出 .claude/phases/phase-{N}/review-report.md
4. Verdict
最後 append:
```
## Verdict: [GO | CONDITIONAL GO | NO-GO]
Rationale: ...
Must-fix before execution: ...
```

5.Report back to user

總結 critical issues（3-5 點）
問用家：要唔要我直接 update plan.md？定係你自己改？
yaml

---

## 你整個 workflow 變成一條 command chain

最後你可以做一個 meta-skill `/run-phase` 一次過串埋：
run-phase 3
→ /review-plan 3 (gate: 要 GO 先繼續)
→ /execute-phase 3
→ /generate-qa 3
→ /run-qa 3 (透過 MCP call Copilot/Cursor)
→ /reflect-phase 3 (update learnings.md, propose phase 4 adjustments)