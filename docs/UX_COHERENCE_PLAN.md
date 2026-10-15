# UX coherence plan

Three open pull requests each add a way to guide a first-time reader. They
overlap, and taking them as they stand would put more than one greeting and more
than one instruction strip on the same window. This note records the agreed role
of each piece and the order in which to land them, so the window ends up with
one start screen and one contextual coach rather than a stack of competitors.

## The pieces

| Piece | Where | What it is | Role |
| --- | --- | --- | --- |
| `guide_panel.py` | on `main` | a four-step strip above the workspace, always on until the workflow is done | the incumbent; its four steps repeat the workflow a second time |
| `welcome_view.py` | PR #65 (`ux/full-overhaul`) | a full-window start screen in a `QStackedWidget`, shown until a capture is open | **the start screen** |
| `start_screen.py` | PR #63 (`ux/empty-state`) | a second full-window start screen with the same "Open example / Open file" buttons | a duplicate of #65's screen |
| `guided.py` (`GuidedPanel`) | PR #66 (`ux/guided-mode`) | a five-stage plain-language coach shown above the workspace | **the contextual coach** |

## The concept

A reader meets exactly one of each:

1. **Before a capture is open — one start screen.** A title, one question and
   two ways to answer it: *Open the example* and *Open a file…*. This is PR #65's
   `welcome_view` (equivalently #63's `start_screen`; they are the same idea, so
   only one is kept). Nothing else is on screen: no guide strip, no coach.

2. **After a capture is open — one contextual coach.** A single strip above the
   workspace naming the current step and the next action in plain words, which
   hides itself once the workflow is finished and can be switched off for good
   from Settings. This is PR #66's `GuidedPanel`.

3. **The incumbent `GuidePanel` is retired.** It says the same four steps the
   coach already says, so keeping both is the duplicate-panel problem. Its useful
   bits — the workflow state machine and the "step done / next / todo" marks —
   live on in the coach and the start screen.

## Why #65 wins the start screen over #63

Both build a start screen from the same idea; they are not both needed.

* #65 is **MERGEABLE / CLEAN** on the current `main`; #63 is **CONFLICTING**
  against a base three merges old (`d156a77`), so #63 needs a rebase before it
  can land at all.
* #65 already carries the matching English catalogue and a corpus dialog; #63
  does not.
* #63 does carry one thing worth taking: its `set_progress(capture, session,
  rule)` signature is a tidy contract for the start screen. #65's
  `set_progress(*, capture, session, rule)` is equivalent.

Decision: keep **#65**; close #63 as superseded, or rebase it only to lift any
detail #65 lacks (none was found).

## Why the coach replaces the strip, not sits beside it

PR #66 adds `GuidedPanel` but leaves `GuidePanel` wired, so the window shows
**both** at once (measured: the coach, ~124 px, plus the strip, ~86 px, together
~210 px of a 768 px window). That is the exact "duplicate instruction panels"
outcome to avoid. #66 should drop `GuidePanel` from the central layout when the
coach is present.

## Landing order (no mechanical merge)

The integration was carried out on `ux/integration`, built from `ux/full-overhaul`
(PR #65) with PR #67 (`ux/overhaul`) merged in. #67 had already adopted the coach
and removed `guide_panel`, so it stands in for the "#66 rebased on #65" step
described above; the wording of #66 survives inside `guided.py`.

1. **#65 first** (start screen + corpus dialog + extended rule builder + English
   catalogue). It was clean on `main` and gives the first-run screen.
2. **#67 merged on top**, keeping its five-stage coach, its Settings toggle and
   its runnable-rule fixes, and dropping the old `GuidePanel` strip so only one
   instruction panel remains.
3. **#63 stays open** until a reviewer approves closing it: its `start_screen.py`
   is the same idea as #65's `WelcomeView`, on an older base, without the English
   catalogue or the corpus dialog, so it is superseded. Do not close it without
   that approval.
4. The audit's own follow-ups (D1 runnable rule, D3 applied state) are covered
   here by #67's rule-flow rework plus the `tests/ui/test_rule_build_flow.py`
   regression tests; D2 (hint language) is covered by the empty-state rebuild on
   a language change.

The coach's step number is derived from what is open (capture, session, rule,
applied), not from a click history, so it always matches real progress — that is
`MainWindow._guided_index`, and it is the behaviour to keep.
