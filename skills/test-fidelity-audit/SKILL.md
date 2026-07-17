---
name: test-fidelity-audit
description: Use when reviewing mock-heavy or fixture-heavy tests, or when a suite passes green yet real bugs still ship. Audits test-double fidelity — does a fake's shape match what the real service actually returns — the counterfactual blind spot that stub/TODO scanners can't catch.
---

# Test Fidelity Audit

## Overview

**Complete ≠ correct.** A test can be finished, assertion-rich, and free of TODO/stub markers yet still be **counterfactual** — the hand-written mock it depends on encodes a response shape the real service never returns. The test then validates behavior against a fiction and passes forever.

Incompleteness scanners (TODO/stub/`unimplemented!`/empty-body finders) are blind to this: the fixture *is* complete. Assertion count doesn't help either — counterfactual fixtures are assertion-*rich*. This is an orthogonal axis:

```
                COMPLETE                INCOMPLETE
CORRESPONDS     real recorded test     (unfinished)
COUNTERFACTUAL  THE BLIND SPOT         stub/TODO finders catch these
                (a finished lie)
```

**Complementary axes of test trust** (use together, none subsumes another):

| Axis | Question | Tool / skill |
|------|----------|-------|
| **incompleteness** | Is the code even finished? | [`mock-code-finder_v1`](https://jeffreys-skills.md/skills/mock-code-finder) (stubs/TODOs) |
| **fidelity** | Does the fake match what the real service returns? | **this skill** |
| **oracle problem** | Is the output *correct* when you can't say what correct is? | [`testing-metamorphic_v6`](https://jeffreys-skills.md/skills/testing-metamorphic) |
| **coverage** | Does the suite explore enough of the input domain to surface bugs? | property-based testing / fuzzing (Hypothesis, hypofuzz) |

The first three ask *is each check honest?* — **coverage** asks *is the checking sufficient?*, a different family (mutation testing is its other member; see [background.md](background.md) §5). All four compose; none subsumes another.

This skill operationalizes the classic principle **"don't mock what you don't
own"** and Fowler's **Self-Initializing Fake** (the formal name for
record-then-replay). Run `mock-code-finder_v1` for breadth, this for whether
fakes match reality — and see the triage note below for when to hand off to
`testing-metamorphic_v6` instead. It also guards the **green** that `tdd`'s
red-green loop trusts (background.md §5). Rationale, schools of thought, the prior-art
landscape, and the honest counter-view: [background.md](background.md); full
citations: [references.md](references.md).

## Glossary

Use these terms precisely — a repeatable audit depends on not letting them drift.

- **fidelity** — whether a mock's response matches what the real service actually returns; the property this skill audits. _Avoid_: realism, accuracy — those describe the *request* or the client library, not the response.
- **mock** — this skill's everyday umbrella for any hand-authored stand-in the code treats as a real dependency (`MagicMock`, an inline response dict, a `Stubber` response), matching sibling `mock-code-finder`'s vocabulary. Strictly it's *one* category of the formal **test double** taxonomy (dummy / stub / spy / mock / **fake**); that precise taxonomy — and how recording turns a hand-set stub into a captured fake — is in [background.md](background.md) §2.
- **shape** — the whole response *contract* a mock must match: status code, body structure, field names, types, envelope, error format — not just the JSON keys.
- **counterfactual** — a mock whose shape the real service never returns, so the test validates a fiction and passes forever. _Avoid_: "wrong mock" / "bad fixture" — those name a symptom, not the fact that the shape was never verified.
- **corresponds** — the opposite of counterfactual: a shape the real service actually returns (recorded or contract-verified).
- **provenance** — where a mock's shape came from: hand-typed from memory (unverified) vs. recorded from the real service (verified). The first thing to check.
- **record-to-falsify** — record the real interaction *expecting to disprove* the mock, then re-derive the assertions from the real body; never copy the mock's assumed shape.
- **cassette** — a recorded-then-replayed interaction (Fowler's *Self-Initializing Fake*); the output of recording.
- **oracle problem** — when you can't state what the *correct* output is (ML/ranking, solvers, compilers). Recording proves shape, never correctness — hand off to `testing-metamorphic_v6`. _Avoid_: bare "oracle" — it collides with Oracle the database.
- **golden snapshot** — what a recording actually proves: the output's shape *was once real*, not that it's *right*. The ceiling of record/replay under the oracle problem.

The four triage **buckets** — service-shape / client-mechanics / unrecordable / pure-logic — are defined where they're applied, in Audit recipe step 2.

## The one question this skill forces

For every mock standing in for an **external service** response (HTTP body/status, SDK/boto3 response, DB rows, RPC/GraphQL reply):

> **Where did this shape come from — and would the real service actually return it?**

If the shape was typed by hand from memory of the API, it is unverified. "Make the mock behave more like `requests`" and "assert the request URL" do NOT answer this — they check the *request* and the *client library*, never whether the *response shape* is real.

## Audit recipe

1. **Find service-shape mocks.** For a repo-wide inventory of *all* fakes and
   stubs, run **`mock-code-finder_v1`** first — it does the multi-method
   ripgrep/ast-grep enumeration (and, for many findings, resolution tracking via
   its Phase 2b beads workflow). This skill then filters that inventory to the
   fidelity-relevant subset: any test that (a) builds a stand-in for an external
   response — `MagicMock` with `.status_code`/`.json`/`.text`, a mocked `Session`,
   botocore `Stubber.add_response`, or an inline response dict/HTML/JSON — AND
   (b) asserts on a *field of that response* (not merely that a call happened).

   ```bash
   rg -n "MagicMock\([^)]*(status_code|json|text)|spec=requests\.Session|Stubber\(|\.add_response\(|\.json\.return_value" tests/
   rg -n "cassette|vcr|recorded|captured live" tests/   # provenance present = good; its absence on the above = flag
   ```

2. **Triage each flagged mock** into one bucket; only the first is a finding:

   | Bucket | Test is about… | Action |
   |--------|----------------|--------|
   | **service-shape** | fields *of the response* the code parses | **RECORD** against the real service |
   | **client-mechanics** | caching / retry / URL-building / refresh (body is a don't-care) | keep the mock |
   | **unrecordable** | 3×500, mixed-outcome batch, or a side-effect assert ("did it call `terminate`?") | keep the mock |
   | **pure-logic** | literals fed to a pure parser | already real; keep |

   A test can touch more than one bucket — a pagination-mechanics test that also
   asserts a response field. Classify by its **primary intent** (what it chiefly
   exists to prove), not by every line it contains — a judgment call, not a
   mechanical rule. When that intent genuinely is the response body, it's a
   service-shape finding.

   **Oracle-problem check before you record.** "RECORD against the real service"
   assumes the real response is a *usable test oracle*. If the service is oracle-less (ML/
   ranking, a solver, a compiler — no knowable "correct"), or correctness lives in
   your own post-processing, a recording only pins a **golden snapshot** — real
   *shape*, not *right output*. Hand off to **`testing-metamorphic_v6`**; the two
   compose (record real inputs for fidelity, assert metamorphic relations for
   oracle-free correctness). Full rationale: [background.md](background.md) §5.

3. **Record-to-falsify** the service-shape ones. Record the real interaction *expecting to disprove the mock*, then **re-derive the assertions from the real body** — do not copy the mock's assumed shape. Recording routinely exposes real bugs (a field that's a lazy `"..."` placeholder not a list; a 404+JSON where the mock assumed 200+plaintext).

4. **Assert invariants, not exact values** (counts, ids) so full-fidelity re-records don't churn tests.

**Coverage floor check.** Steps 1–4 *own* fidelity; the recipe already routes the other non-owned axes — incompleteness (step 1 → `mock-code-finder_v1`) and the oracle problem (step 2 → `testing-metamorphic_v6`). Give the fourth axis the same floor: a suite that calculates **no coverage at all** (`pytest-cov` / `cargo-llvm-cov` absent from config or CI) **fails the audit** — a green run says nothing about lines no test ever executes. Screen-and-route to the tools ([background.md](background.md) §5); this skill flags that coverage *exists*, not whether it's *sufficient* — that judgment is the tools' and yours, not the audit's.

## Migrating to recorded-real (pytest-recording / VCR)

- Add `@pytest.mark.vcr`; drop the injected fake; let the real client run so VCR intercepts. Commit the **full** cassette — never trim to a "representative" slice.
- **Guardrail:** `--block-network` on by default so an un-recorded call fails loudly. Do **not** set `record_mode` in `vcr_config` — it silently overrides the `--record-mode` CLI flag; leave it unset (defaults to `none`). Recording is an explicit `--record-mode=all` run.
- **boto3 works too** (VCR patches botocore). Three knobs: `filter_headers` to redact SigV4 secrets; `match_on` **including `body`** (AWS json protocol POSTs every op to the same URL — URL-only matching serves the wrong response to out-of-order callers); and static dummy creds on replay only (keyed off `--record-mode`, never a credential probe — that hits IMDS and trips `--block-network`).
- **boto3 isolation trap when a module mixes `Stubber` + VCR-`*_live` tests** — the seam this skill pushes toward (`Stubber` for unrecordable paths, VCR for the live shape). Build the `Stubber`'s client from an **explicit `boto3.session.Session(aws_access_key_id="testing", ...)`**. The global `DEFAULT_SESSION` caches a credential-provider chain on first touch; a later `*_live` test inherits it and resolves creds over the network — failing **ordering-dependently**, masked when xdist splits the two tests across workers so the suite reads green. Green-by-worker-luck is the false trust this skill exists to catch.

## Common mistakes

- **Clean-because-finished** — reporting a suite clean because it has no stubs/TODOs. Check fixture *provenance*, not just completeness.
- **Mock-realism ≠ real-recording** — making a mock raise like real `requests`, or asserting the request URL, while the *response shape* is still invented.
- **Convert-everything** — VCR-ing mechanics/side-effect/pure-logic tests. Loses control (unrecordable sequences) and adds zero fidelity. Only service-shape mocks get recorded.
- **Trimmed cassettes** — discarding real data a future investigation needs. Storage is cheap.
- **Golden-snapshot as correctness proof** — a recorded cassette proves the response *shape is real*, not that the output is *right*. If you can't state what the correct output should be, that's the oracle problem — recording won't solve it; reach for metamorphic testing (`testing-metamorphic_v6`).
- **Fuzzing launders a counterfactual mock** — property-based/fuzz tests over your *inputs*, run against a hand-typed external mock, generate thousands of cases that all hit one canned response: broad input coverage of a *single fiction*, not fidelity. Fix the mock's provenance first (record it), then fuzz — and fuzz the *response* domain (drop/empty/flip the recorded shape), not only the inputs. See [background.md](background.md) §5.

## Real-world impact

Applied to an internal CLI's test suite, an incompleteness scan reported "clean." This audit found service-shape fictions in 5 modules; recording falsified assumptions in 3, including a live production bug (an SDK call that returns `None` in prod because the API field is a lazy placeholder, which the mock had faked as populated).

## Background & further reading

- **[background.md](background.md)** — rationale, the two-axis model, schools of
  thought ("don't mock what you don't own", test-double taxonomy,
  Self-Initializing Fake, verified fakes, contract testing), the **prior-art
  landscape** (what this skill is and isn't redundant with), and the honest
  counter-view on when record/replay is the *wrong* tool.
- **[references.md](references.md)** — annotated bibliography.
