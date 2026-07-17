# Test Fidelity Audit — Background & Rationale

The *why* behind `SKILL.md`: the problem, the schools of thought it rests on, the
prior-art landscape (what this skill is and isn't redundant with), the honest
counter-view, and where it sits among sibling skills. Read this when you want the
reasoning or need to defend the approach to a skeptical reviewer.

Sources are cited by author/short-name inline; full citations with URLs resolve
in [references.md](references.md). Terms in **bold** are the skill's canonical
vocabulary — defined in `SKILL.md`'s Glossary, which this rationale builds on
rather than restates (§2 and §5 go deeper on the terms the Glossary points here for).

---

## 1. The problem, precisely

A test double that stands in for an **external service** encodes an assumption
about that service's response **shape**. When the double is typed by hand from
memory of the API, that assumption is **unverified**. The test then proves your code is
consistent with *your belief about* the service — not with the service.

The failure is silent and durable. As one practitioner put it: *"The real API
adds a field, your mock doesn't have it, the test passes anyway, and you ship a
bug that only shows up against production data"* (asmyshlyaev177). The AI-era
version is sharper still: an agent *"writes the function under some implicit
assumption … and then writes tests under the same implicit assumption"* (Boyko) —
the mock and the code share a blind spot, so the suite is green by construction
and validates nothing about reality.

This is orthogonal to *incompleteness*. A counterfactual fixture is finished and
assertion-rich; stub/TODO scanners (e.g. `mock-code-finder_v1`) see nothing wrong.
Two independent axes:

| | corresponds to reality | counterfactual |
|---|---|---|
| **complete** | ✅ recorded/contract-verified test | ❌ the blind spot (a finished lie) |
| **incomplete** | (unfinished) | 🎯 what stub/TODO finders catch |

`mock-code-finder_v1` owns the bottom row (incompleteness). This skill owns the
bottom-*left* cell (fidelity). They compose; neither subsumes the other.

---

## 2. Schools of thought this rests on

**"Don't mock what you don't own."** The load-bearing principle. Originating in
London-school TDD and stated flatly in *Growing Object-Oriented Software, Guided
by Tests* (Freeman & Pryce): mock only interfaces **you** own; for
third-party/external boundaries, wrap them in an adapter you own and verify the
adapter against the real thing. Mocking a type you don't own bakes your *guess*
about its behavior into a green test (Google Testing Blog; Hynek Schlawack;
testdouble wiki).

**The test-double taxonomy** (Meszaros, *xUnit Test Patterns*; popularized by
Fowler). Dummy / Stub / Spy / Mock / **Fake**. Recording changes the *category*
of your double from a hand-set Stub (you specify the canned answer) to a **Fake**
with a real, captured implementation. The fix isn't "a better stub," it's "stop
stubbing an external contract."

**Self-Initializing Fake** — the formal ancestor of VCR/pytest-recording. Fowler
describes a fake that, on first run, calls the real service and records the
responses; on later runs it replays them. A cassette *is* a Self-Initializing
Fake. Naming it this way tells a reviewer the mechanism is 15+ years old and
well-understood, not a novelty.

**Verified fakes / "Fake, don't mock."** A parallel lineage argues you should
build hand-written *fakes* but continuously prove them equivalent to the real
implementation by running the *same* test suite against both (Turner-Trauring's
"verified fakes"; Shai Yallin's "Fake, Don't Mock" + contract tests for memory
fakes). Record-to-falsify is the lightweight cousin: instead of maintaining a
fake + an equivalence suite, you capture the real interaction once and re-derive
your assertions from it.

**Design-away.** Gary Bernhardt's "Boundaries" and the functional-core/
imperative-shell style argue the *best* fix is architectural — push I/O to a thin
shell so most mocking "just goes away." That's complementary: this skill audits
the mocks you already have; "Boundaries" reduces how many you need.

**Contract testing** (consumer-driven contracts / Pact; ThoughtWorks Radar). The
industrial-strength version of the same idea: instead of a one-time recording, a
contract is continuously verified against the *provider* in CI, so drift is
caught when the provider changes, not when your customer does. Record-replay is
the lightweight point on this spectrum; contract testing is the heavyweight
point. Choose by how often the provider changes and whether you control it.

---

## 3. Prior-art landscape — what this skill is (and isn't) redundant with

A five-front adversarial sweep (AI-skill ecosystems, contract/mock-sync tooling,
academic literature, practitioner writing, and static-analysis/test-smell
detectors) tried hard to find an existing artifact that makes this skill
unnecessary. The honest result: **redundant on the *premise*, not on the
*contribution*.**

**The premise is old and well-established — do not claim it as novel.** That
mocks encode unverified assumptions and pass against a fiction is documented
empirically (Spadini et al., *To Mock or Not To Mock?*, who find developers
report keeping a mock faithful to the real class is *hard*) and, for the AI era,
directly (Hora & Robbes, *Are Coding Agents Generating Over-Mocked Tests?*, 2026
— coding agents mock more than humans and the paper explicitly calls for
"guidance on mocking practices in agent configuration files"). External-service
and HTTP response mocking is the single hardest mocking category developers ask
about (Ahmed et al.). The oracle-problem caveat is textbook (Barr et al.).

**The guardrail is standard, not novel.** "Block the network so an un-recorded
call fails loudly" is off-the-shelf (`pytest-socket`, `pytest-recording
--block-network`). The skill *uses* it; it does not claim it.

**The record/replay mechanics are commodity.** VCR/vcrpy/WireMock/MSW/Polly/
Mountebank/Hoverfly all record and replay. Hoverfly even diffs live-vs-stored.
None of this is the skill's contribution.

**What *no* skill, tool, or paper packages — the surviving core:**

| Distinctive move | Closest prior art | Why it doesn't subsume |
|---|---|---|
| **Retroactive audit** of an existing hand-mock suite | Specmatic, Pact, Microcks, Optic, Schemathesis | All are *preventive* (spec-first or contract-first) or replace your mocks with their own server/DSL. None reads *test source* and inventories `MagicMock`/`Stubber`/inline-dict doubles in place. |
| **Four-bucket triage** (service-shape → record / mechanics / unrecordable / pure-logic → keep) | Boyko's one-cut own-vs-external; Khorikov's managed-vs-unmanaged | Everyone stops at a *single* boundary axis. The four-way keep-vs-record decision procedure appears nowhere as a unit. |
| **Record-to-falsify** (record expecting to *disprove* the mock; re-derive assertions from the real body) | Contract recorders; verified fakes | Others record to *codify* a contract or *speed up* isolation. The adversarial framing — record in order to break your own fixture — is unique. |
| **Cassette = golden snapshot → oracle handoff** | Fowler (Self-Initializing Fake) + Barr et al. (oracle) separately | Both halves exist; no source *joins* them to say "record for fidelity, but that only proves shape, so hand off to metamorphic for correctness." |
| Naming **"counterfactual fixture"** | van Deursen; Garousi & Küçük test-smell catalogs | The catalogs' nearest smells (*Mystery Guest*, *Resource Optimism*) are about coupling to real resources, the *inverse* concern. No catalog names "a mock whose response shape was never verified." The skill coins a name for an un-catalogued smell. |

**Three structural reasons the tooling can't close the seam:**

1. **Direction of ground truth.** Contract/conformance tools (Specmatic, Microcks,
   Optic, Schemathesis, Dredd, Prism, MockServer) treat a *spec as ground truth*
   and ask "does the live API conform to the spec?" This skill treats the *real
   API as ground truth* and asks "does this frozen fixture still match what the
   real service returns?" — often with **no spec existing at all**.
2. **Input artifact.** Every competitor needs a machine-readable spec, or a
   running/owned provider, or is a bare record/replay mechanism. None takes an
   existing hand-mocked test suite as its input. Detecting a counterfactual
   fixture *requires ground truth you don't have* — so the skill **manufactures**
   it (records once) rather than assuming a spec or live provider exists.
3. **The unownable-provider case is the skill's home turf.** Contract testing's
   guarantee collapses exactly when you can't run the provider — Pact's and
   PactFlow's own docs list third-party/OAuth/AWS-SDK-style providers as "not a
   good fit," and fall back to "periodically verifying against the live API,"
   which *is* the skill's lightweight re-record point.

**Demand signal.** The field is actively asking for this and no one has shipped
it: a 415-skill QA-skills catalog (qaskills.sh) still ships no skill for checking
mock responses against real service behavior; Hora & Robbes (2026) call for
exactly this guidance; and a 2025–26 genre of posts ("your AI-generated
tests are lying to you"; "pass but don't assert") names the failure mode without
packaging a method. The nearest *tooling* analog, AIMock (2025), automates a
three-way drift check but is a product that stops at shape — no triage, no oracle
framing.

**In short:** the defensible novelty is the *packaged operational audit*
(inventory → triage → record-to-falsify → oracle handoff) and the *four-bucket
triage* — not the premise, the guardrail, or the record/replay mechanics, all of
which are prior art. That framing is both accurate and stronger than a blanket
"nobody does this."

---

## 4. The honest counter-view (when record/replay is the wrong tool)

Record/replay is not free and not always right. Take the critique seriously
(draconianoverlord; Rainsberger on integrated-test overreach):

- **Cassettes go stale too.** A recording captured once and never refreshed is
  just a mock with better provenance; it drifts the moment the provider changes.
  Mitigation: periodic re-record (a scheduled `--record-mode=all` run) or
  graduate to contract testing for fast-moving providers.
- **They can hide intent.** A 50 KB cassette obscures *what* the test asserts.
  Mitigation: assert invariants explicitly; keep the cassette as evidence, not as
  the assertion.
- **Brittleness from over-matching.** Matching on volatile fields (timestamps,
  nonces) makes replays fail spuriously. Mitigation: scope `match_on`; normalize
  or filter volatile fields.
- **Not everything is recordable.** Deterministic faults (3×500), mixed-outcome
  batches, and side-effect assertions ("did it call `terminate`?") cannot be
  recorded and should stay hand-mocked.

This is why the skill's **triage** step exists: recording is the right fix only
for the *service-shape* bucket. The other three buckets keep their mocks by
design, not by omission.

---

## 5. Relationship to sibling skills — the axes of test trust

A test can fail to be trustworthy along two families. Three axes are about
**honesty** — is each check truthful: **incompleteness** (is the code even
finished?), **fidelity** (does the fake match what the real service returns?), and
the **oracle problem** (is the output *correct* when you can't say what correct
is?). A fourth is about **sufficiency** — is the checking enough: **coverage**
(does the suite explore enough of the input domain to surface bugs?), whose other
member is mutation testing (below). Each has its own tool or skill and none
subsumes another; the canonical table lives in `SKILL.md`. What each sibling
catches, and how it composes with this one:

- **`mock-code-finder_v1`** — the incompleteness finder (stubs, TODOs,
  `unimplemented!`, empty bodies, 501s). Use it to *enumerate candidate fakes
  across a repo* and *track resolution*. This skill consumes that candidate list
  and adds the axis it can't see: does the fake correspond to reality?

- **`tdd` / `diagnosing-bugs`** — the feedback-loop skills. Red-green-refactor and
  reproduce-then-fix both trust that when a test goes **green**, the behaviour is
  real; a counterfactual mock breaks that at the root, so the loop runs against a
  fiction and green means nothing. *"The rate of feedback is your speed limit"*
  (Thomas & Hunt, *The Pragmatic Programmer*) — but only when the feedback is
  **true**. This skill runs neither loop; it verifies the mocks their green
  assertions trust. Fake feedback is worse than none — the agent flies blind while
  its instruments read green.

- **`testing-metamorphic_v6`** — owns the **oracle problem** (wrong logic where no
  expected value exists). This skill's "record against the real service" fix
  silently assumes the real response is a *usable test oracle*. When it isn't —
  ML/ranking endpoints, scientific solvers, compilers, anything whose right answer
  is unknown or unstable — a recording is only a **golden snapshot**: it pins
  *what the output was once*, not that it's correct, and it can't validate your
  logic on any other input. Metamorphic testing verifies correctness without an
  oracle by asserting relations across transformed inputs (f(T(x)) vs f(x)). The
  two **compose**: record the real *inputs* for fidelity, then assert metamorphic
  relations on them for oracle-free correctness.

- **property-based testing & fuzzing** (Hypothesis; `hypofuzz`) — the **coverage**
  axis, a different *family* from the three above: they ask whether each check is
  honest, this asks whether you run enough of them. Borrow Hypothesis's **domain
  vs distribution** split and point it at the *response* side: a mock defines the
  **response domain** your code sees. A hand-typed mock collapses that domain to
  one *guessed* point; a single recorded cassette collapses it to one *real* point
  — high fidelity, zero coverage. Fidelity asks *is this point real?*; coverage
  asks *does the double span the domain the real service actually produces* — 200
  **and** 404, full page **and** empty, present field **and** null? Two
  interactions matter:
  - **Fuzzing the inputs does not fix a counterfactual mock — it launders it.**
    Thousands of generated inputs all hit the same canned response: broad *input*
    coverage of your code's reaction to *one fiction*. False confidence squared.
  - **The compose is fidelity-seeded response fuzzing.** Record real responses to
    establish the real response *domain* (this skill), mutate within it — drop a
    field, empty a list, flip 200→404 — to surface where your code breaks on
    plausible-but-unhandled *real* responses (PBT/fuzzing), then check without a
    golden value (`testing-metamorphic_v6`). Record the domain, explore it, check
    it — Hypothesis's domain (yours) + distribution (the engine's), on the response
    side. It is also the answer to Hypothesis's *unknown-unknowns*: the cassette is
    the known response; fuzzing its real domain reaches the ones a hand-typed mock
    never imagined.

### Coverage-family tooling, by language

Representative anchors for the **sufficiency** family, not an exhaustive list —
verify maintenance status before adopting (tool lists rot). Each cell is the tool
you'd actually reach for; the *concepts* they serve are above and in
`references.md`.

| Technique | Python | Rust |
|---|---|---|
| **Property-based** | [Hypothesis](https://hypothesis.readthedocs.io) (domain/distribution) | [proptest](https://github.com/proptest-rs/proptest) (Hypothesis-like, `Strategy`-based) · [quickcheck](https://github.com/BurntSushi/quickcheck) (per-type, simpler) |
| **Fuzzing** | [Atheris](https://github.com/google/atheris) (coverage-guided, OSS-Fuzz) · [HypoFuzz](https://hypofuzz.com) (Hypothesis backend) | [cargo-fuzz](https://github.com/rust-fuzz/cargo-fuzz) (libFuzzer) · [bolero](https://crates.io/crates/bolero) (unified fuzz + property front-end) |
| **Coverage** | [pytest-cov](https://github.com/pytest-dev/pytest-cov) (wraps coverage.py; xdist-aware) | [cargo-llvm-cov](https://crates.io/crates/cargo-llvm-cov) (preferred) · [cargo-tarpaulin](https://crates.io/crates/cargo-tarpaulin) (older, Linux-x86_64) |
| **Mutation** | [mutmut](https://github.com/boxed/mutmut) · [cosmic-ray](https://github.com/sixty-north/cosmic-ray) (CI integration) | [cargo-mutants](https://github.com/sourcefrog/cargo-mutants) |

Rust's presence here isn't hypothetical: the differential-testing boundary below
(Bun-in-Rust, rewrites.bio) is exactly where a rewrite's `proptest` +
`cargo-mutants` + `cargo-fuzz` suite does its work.

### Where cassettes sit: the snapshot/golden-testing lineage

A VCR cassette assertion is a **golden / snapshot / approval test** — the output
is compared to a stored reference captured from a real run. That lineage
(Approval Testing, Falco; characterization tests, Feathers) is powerful for
*fidelity* and for *change detection*, but it shares golden testing's core
limitation: **a snapshot answers "did the output change?", never "is the output
correct?"** When the underlying system has the oracle problem, that gap is
unbridgeable by snapshots alone — which is exactly the seam where metamorphic
testing takes over. Mutation testing (PIT; the pseudo-tested-methods line,
Vera-Pérez et al.) is complementary but does *not* close the fidelity gap: a
mutation-adequate suite can still be built entirely on a fictional mock.

### Boundary case — when you already have an independent oracle

Both this skill (fidelity) and metamorphic testing (oracle) are for when you
*lack* a trustworthy independent check. When you already have one — a
language-independent test suite, or a reference implementation the new code must
match — you need neither: run both against the same inputs and diff them
(**differential testing**; `testing-metamorphic_v6` explicitly routes here when a
reference exists). Jarred Sumner's *Rewriting Bun in Rust* is the clean example:
a TypeScript test suite independent of the runtime's implementation language was
the oracle, and adversarial reviewers verified each ported `.rs` file matched the
original `.zig` behavior — no recorded fixtures and no metamorphic relations
required. The disambiguation for this skill: if a double you were about to record
is really standing in for *your own* reference implementation, that's a
differential-testing job, not a fidelity audit. Record-to-falsify is for the
external service whose real responses are the *only* ground truth you have.

Seqera Labs' *rewrites.bio* (principles for rewriting bioinformatics tools with
AI) applies the same discipline to scientific software — the original tool is the
oracle, and correctness is byte-for-byte or numerical-precision output comparison,
not a recorded double. It also happens to state this skill's *premise* in another
domain: *"synthetic data is … insufficient for validation … real sequencing data
has error patterns … that generators don't replicate."* A hand-typed double is to
a real API response as synthetic reads are to real sequencing data — same
argument, even though rewrites.bio's remedy (differential testing against the
original) differs from this skill's (record the real response).

### Out of scope (upstream): specifying quality requirements

*Specifying* what "quality" means — turning vague -ilities into measurable
acceptance criteria — is requirements engineering, a discipline that sits
*upstream* of this skill (quality-attribute scenarios; arc42's *How to Specify
Quality Requirements*). This skill assumes the requirements already exist and asks
only whether the tests that check them run against reality rather than a fiction.
Noted here to fix the boundary: a fidelity audit is not the place to decide what
to test, only whether the test's stand-ins are real.

---

## 6. Provenance of this skill

Distilled (Track C session-mining, `operationalizing-expertise_v6`) from a real
migration of the `ngs_troubleshooting` CLI test suite: an incompleteness scan
reported "clean," yet recording the mocked HTTP/boto3 calls against the real
services falsified assumptions in 3 of 5 modules — including a live production
bug (an SDK call returning `None` in prod because an API field is a lazy `"..."`
placeholder the mock had faked as a populated list). The operator library and the
RED/GREEN subagent evidence behind the skill live in the session's
`operationalize-vcr-migration/` corpus.

The gap it closes — strong reviewers audit assertion depth, mock realism, and
coverage, but treat the hand-typed response body as ground truth — was confirmed
empirically: baseline agents without the skill missed it 2/2; with the skill they
caught it 2/2 and correctly *kept* the non-service-shape mocks.
