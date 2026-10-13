# Product Designer 005 — Onboarding Redesign

**Brief version: 2026-07** · Fixture: `onboarding_sessions.csv`, sha256 `8afd77aa7feb1895cc6e7e0eb8bde35fb518dbea6470e7dbcdb002db52b6428e`

## Written answer

**Core finding.** Onboarding is built around setup, but users stay because they've seen a project. [Observed] In the fixture, 7/9 sessions that reached step 4 (first project) were active on day 14. 0/7 that stopped earlier were. Completion is a weaker signal: [Observed] S-06 and S-12 finished every step and churned, while S-08 and S-15 never finished and stayed. (Source: analyze_sessions.py on onboarding_sessions.csv.) So the redesign moves the project to the front and gives invites and integrations a reason to happen later.

### 1. Problem analysis

**Where the funnel breaks.** [Benchmarked] The brief's funnel loses 43 points at team setup, far more than at any other step. In the fixture's 12 core self-serve, in-ICP sessions, [Observed] non-completers stop at step 2 (S-01, S-10, S-14), per analyze_sessions.py, step 3 (S-04, S-07, S-11), and step 4 (S-08, S-15).

- **Step 2 (invite 3+) is a wall in front of value.** [Observed] "Asked me to invite people before I'd seen a single screen" (S-10). "Wanted to poke around myself first" (S-01). The skip exists but nobody finds it: S-13 found "the tiny link at the bottom", while S-03 believed it was impossible. That's a discoverability failure, not a missing feature.
- **Step 3 fails for three different reasons.** Choice overload (S-04), an SSO policy blocking the admin (S-07), and a keyboard-inaccessible modal (S-11). One redesign doesn't fix all three. Overload is a design problem, accessibility is a bug, and SSO is a routing problem.
- **Step 4 isn't really drop-off.** S-08 and S-15 stopped at step 4 but were active on day 14. They found value and left the wizard. The step counts as "drop-off" only because the metric counts wizard steps.

**Assumptions baked into the current flow:**
1. Users will invite before they believe in the product. Invites are treated as a toll, not an outcome.
2. More integrations at setup means more retention. The brief's 3x claim is correlation. [Observed] In the fixture, everyone with fewer than 2 integrations who reached a project was active on day 14 (4/4).
3. Finishing the wizard means activation. S-06 and S-12 disprove that.
4. Everyone arrives the same way. Invitees (S-02, S-09) join a populated workspace and have a different, easier flow, so they inflate the completion numbers.

### 2. Redesigned flow

See `wireflow.html` (clickable, annotated per screen).

Session references are [Observed] fixture rows.

1. **Sign up.** Unchanged, plus an "SSO required? Talk to us" route for admins (S-07).
2. **Pick a template.** One click, including "just show me around".
3. **Live sample project = first value.** A pre-filled board (S-08: "the sample was the useful part"). An optional 90-second tour replaces the 5-minute end gate, which keeps what S-16 valued without making them earn it. A pinned setup checklist shows there's more to do (S-15).
4. **Invite in context.** "Assign this task to…" turns the invite into a hand-off of real work. No minimum.
5. **One recommended integration,** tied to the template (Slack for client-review alerts), with "see all" behind it (S-04). The dialog is keyboard-accessible (S-11).

**How skipped steps come back:**
- **Invite:** prompted on the first task assignment, on the day-1 email ("your board has 3 unassigned tasks"), and when a 2nd project is created.
- **Integration:** prompted the first time a task hits "Client review", and on the day-2 email.
- **Checklist:** stays pinned until done or dismissed.

**Trade-offs I'm accepting:**
- **Fewer invites in session one,** in exchange for invites that come with real work attached. If invites per new workspace by day 7 drop more than 15% [Assumed], I'd bring back a soft, skippable invite prompt right after first value.
- **A sample project adds sample data people must clear.** I'll offer one-click "clear sample".

### 3. V1 scope (one sprint: 2 engineers, 2 weeks)

**Ship:**
1. Reorder so template and sample project come before invites and integrations.
2. Make invite and integrations skippable with equal-weight "Do this later" buttons.
3. Contextual invite on task assignment.
4. Single recommended integration plus the keyboard-accessibility fix.
5. Setup checklist widget.
6. One day-1 nudge email.

[Estimated] Fits the sprint because steps 1, 2, and 4 reuse existing screens, and the template library already exists (current step 4 offers templates).

**Cut from V1:**
- Personalization beyond template choice.
- An in-product SSO setup flow (V1 is a link to sales).
- A rebuilt tutorial (V1 trims it and moves it).
- A multi-email drip.
- An invitee-specific onboarding flow (already the best-performing path, so leave it).

**Expected impact.** [Estimated] Roughly 58–66% sign-up to first value. Math: [Benchmarked] 95% get past account creation × [Assumed] ~85% pick a template × [Assumed] ~75–80% move a task in the sample project.

**Success metrics:**
- **Primary:** % of new self-serve workspaces with a task moved in a project within 24h (first value). This is not wizard completion.
- **Leading, visible within days:**
  - Time to first task moved
  - Template-step abandonment
  - Checklist items done in the first session
- **Guardrails:**
  - Invites per new workspace by day 7
  - Share of signups coming from invites
  - % of workspaces with 1+ integration by day 7
- **Outcome:** day-14 active rate for new workspaces.
- **Falsifier:** first value rises but day-14 activity doesn't move. That would mean the sample project is a toy, not value. Run as a 50/50 split for 2 weeks [Assumed]. 2,000 teams means a few hundred new signups per window at most [Estimated], so look for big effects only.

### Not acting at face value

All rows below are in onboarding_sessions.csv.

1. **S-05 is probably S-01 again.** Same persona, 35 employees, organic search, "second try after abandoning last week". Counting both double-counts one person.
2. **S-03 and S-13 are freelancers,** outside the 10–100 ICP. I use their contradiction about the skip link, but not their completion rates.
3. **S-02 and S-09 joined via invite.** That's a different flow, and it flatters completion.
4. **S-14 wants more hand-holding.** One voice against the rest of the data. I offer a demo link, but I'm not redesigning around it.
5. **S-11 is n=1 but a defect.** Accessibility gets fixed regardless of frequency. This is the opposite call to S-14, on purpose.
6. **S-07 (SSO) is real but enterprise-specific.** I route it to sales rather than reshaping self-serve around it.
7. **The brief's 3x integration retention** is confounded with reaching value. Treat it as a guardrail, not a reason to gate.
8. **What I won't conclude:** with n=16, the percentages are direction only. The 7/9 vs 0/7 split is the one strong enough to design around.

## Operating artifact

- `my-submissions/product-designer-005/wireflow.html`: clickable, annotated wireflow (open in any browser, no login).
- `my-submissions/product-designer-005/analyze_sessions.py` and `analysis_output.txt`: the segment and funnel analysis behind every number above.

```
$ python3 my-submissions/product-designer-005/analyze_sessions.py challenges/product-designer-005/fixtures/onboarding_sessions.csv
```

## Evidence log

| Claim | Tier | Where to check |
|---|---|---|
| [Observed] Reaching a project predicts d14 activity (7/9 vs 0/7) | Tier 3 | analyze_sessions.py → analysis_output.txt |
| Completion ≠ value (S-06, S-12 vs S-08, S-15) | Tier 3 | analysis_output.txt, fixture rows |
| Redesigned flow and per-screen rationale | Tier 2 | wireflow.html |
| Integration-retention claim is confounded | Tier 3 (n=16, weak) | analysis_output.txt |
| 58–66% projection | Tier 0 (estimate) | math in section 3 |
| > **[FILL IN, optional]** an onboarding change you shipped, with before/after | Tier 4 | link |

## Number source labels

Brief funnel figures are [Benchmarked] (given). Fixture counts are [Observed] and reproducible (analyze_sessions.py, output in analysis_output.txt). The projection is [Estimated]. The 15% invite guardrail, the 2-week test window, and step-conversion inputs are [Assumed].

## AI usage disclosure

> **[FILL IN, honestly].** Example: "I used Claude to help write the analysis script, the wireflow HTML, and a first draft. I chose the 'project-first' thesis, the S-11 vs S-14 calls, and the V1 cut line, re-checked every session ID against the CSV, and edited the text."

## What breaks it

- Thresholds here are [Assumed].
- **The sample project could become a demo people admire and abandon.** Detect: first value up, d14 flat. Fix: make the sample editable into the user's real first client project.
- **Invites could fall without the wall.** Detect: the day-7 invites guardrail. Fix: a soft prompt right after first value.
- **One recommended integration could be the wrong one** for some templates. Detect: low connect rate per template. Fix: per-template recommendation.
- **Sprint risk:** the contextual invite touches permissions. If it slips, ship the reorder and skip-buttons alone. They target the 43-point drop.

## What stays human

Choosing what "first value" means and changing that definition. The invite-vs-activation trade-off if the guardrail trips. Accessibility acceptance (tested by a person using a keyboard and a screen reader, not only an automated checker). Reading verbatims for meaning; AI can cluster them but shouldn't decide which single voice matters (S-11 yes, S-14 no).

## Artifact access

All files are in `my-submissions/product-designer-005/`. Open `wireflow.html` locally in a browser. The script needs only Python 3 stdlib.
