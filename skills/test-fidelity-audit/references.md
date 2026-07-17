# Test Fidelity Audit — References

Annotated bibliography for `SKILL.md` and [background.md](background.md).
Grouped by role; each entry notes what it contributes.

---

## Empirical studies of mocking & AI-generated tests

- Spadini, Aniche, Bruntink, Bacchelli — **"To Mock or Not To Mock? An Empirical Study on Mocking Practices"** (MSR 2017). <https://sback.it/publications/msr2017b.pdf> · extended as **"Mock objects for testing Java systems"**, *Empirical Software Engineering* 24:1461–1498 (2019). <https://doi.org/10.1007/s10664-018-9663-0> — canonical empirical study; developers report keeping a mock faithful to the real class is *hard*. The premise anchor.
- Andre Hora & Romain Robbes — **"Are Coding Agents Generating Over-Mocked Tests? An Empirical Study"** (arXiv:2602.00409, 2026). <https://arxiv.org/abs/2602.00409> — agents mock more than humans; explicitly calls for "guidance on mocking practices in agent configuration files." The strongest "the field is asking for exactly this" citation.
- Ahmed, Opu, Roy, Suhi, Chowdhury — **"Exploring Challenges in Test Mocking: Developer Questions and Insights from StackOverflow"** (arXiv:2505.08300, 2025). <https://arxiv.org/abs/2505.08300> — external-service & HTTP response mocking are the hardest, most persistent mocking categories.
- Zhu et al. — **"Understanding and Characterizing Mock Assertions in Unit Tests"** (arXiv:2503.19284, 2025). <https://arxiv.org/abs/2503.19284> — analyzes mock-assertion structure/value; notably does *not* touch whether the mocked shape is faithful (the fidelity axis is unaddressed even here).

## The oracle problem & metamorphic testing

- Barr, Harman, McMinn, Shahbaz, Yoo — **"The Oracle Problem in Software Testing: A Survey"** (*IEEE TSE* 41(5), 2015). <https://earlbarr.com/publications/testoracles.pdf> — authoritative framing; positions metamorphic testing and contract-driven development as responses to oracle-less systems.
- Chen, Cheung & Yiu — **"Metamorphic Testing: a new approach for generating next test cases"** (1998); Segura et al. survey (2016). See the `testing-metamorphic_v6` skill for the operational method.
- Jarred Sumner — **"Rewriting Bun in Rust"** (Bun blog, 8 Jul 2026). <https://bun.com/blog/bun-in-rust> — *disambiguating example, not a source for the method.* A language-independent TypeScript test suite (plus the original Zig as reference implementation) served as the oracle for the Zig→Rust port, so it needed **differential testing**, not fidelity recording or metamorphic relations. Marks the boundary of this skill: when you already have an independent oracle, don't record.
- Seqera Labs — **"rewrites.bio: Principles for rewriting bioinformatics tools with AI"** (2026). <https://rewrites.bio> · <https://github.com/seqeralabs/rewrites.bio> — *disambiguating example (same differential-testing boundary), with a domain echo of the fidelity premise:* its "test with real data, not synthetic — real sequencing data has error patterns generators don't replicate" principle mirrors this skill's "record the real response, don't hand-type a fixture." Remedy is output-comparison against the original tool (the oracle), not a recorded double.

## Test-double vocabulary & the load-bearing principle

- Freeman & Pryce — *Growing Object-Oriented Software, Guided by Tests* (2009) — origin of "don't mock what you don't own."
- Gerard Meszaros — *xUnit Test Patterns* (2007). <http://xunitpatterns.com> — origin of the Dummy/Stub/Spy/Mock/Fake taxonomy.
- Vladimir Khorikov — *Unit Testing Principles, Practices, and Patterns* (2020). <https://www.manning.com/books/unit-testing-principles-practices-and-patterns> — managed vs unmanaged dependencies; mock only the unmanaged (external, out-of-process) ones.
- Google Testing Blog — **"Don't Mock Types You Don't Own"** (2020). <https://testing.googleblog.com/2020/07/testing-on-toilet-dont-mock-types-you.html>
- Hynek Schlawack — **"'Don't Mock What You Don't Own' in 5 Minutes."** <https://hynek.me/articles/what-to-mock-in-5-mins/>
- testdouble/contributing-tests wiki — **"Don't mock what you don't own."** <https://github.com/testdouble/contributing-tests/wiki/Don't-mock-what-you-don't-own>
- Martin Fowler — **Test Double** <https://martinfowler.com/bliki/TestDouble.html> · **Mocks Aren't Stubs** <https://martinfowler.com/articles/mocksArentStubs.html>

## Record/replay & the Self-Initializing Fake lineage

- Martin Fowler — **Self Initializing Fake** <https://martinfowler.com/bliki/SelfInitializingFake.html> — the formal ancestor of VCR-style cassettes.
- Ruby **VCR** (Myron Marston) <https://github.com/vcr/vcr> — coined the "cassette" metaphor; ports followed in most languages.
- Draconian Overlord — **"Skepticism About Record/Replay Tests"** (2018). <https://www.draconianoverlord.com/2018/06/20/skepticism-about-record-replay-tests.html> — the honest counter-view (staleness, silent corruption on re-record).

## Verified fakes / "Fake, don't mock"

- Itamar Turner-Trauring — **"Fast tests for slow services: verified fakes."** <https://pythonspeed.com/articles/verified-fakes/> — contract-test your fake against the real impl; a decision framework for when fakes are worth it.
- Shai Yallin — **"Fake, Don't Mock"** <https://www.shaiyallin.com/post/fake-don-t-mock/> · **"Contract Tests for reliable memory fakes"** <https://www.shaiyallin.com/post/using-contract-tests-for-reliable-memory-fakes>

## Design-away & the integration-vs-mock tension

- Gary Bernhardt — **"Boundaries"** (functional core / imperative shell). <https://www.destroyallsoftware.com/talks/boundaries>
- J.B. Rainsberger — **"Integrated Tests Are A Scam"** <https://blog.thecodewhisperer.com/permalink/clearing-up-the-integrated-tests-scam> · talk <https://vimeo.com/80533536>

## Contract testing & mock-reality-sync tooling

- **Pact** / consumer-driven contracts <https://docs.pact.io> · consumer guide <https://docs.pact.io/consumer> · **PactFlow** <https://pactflow.io> — the heavyweight preventive point; its own docs flag third-party/OAuth/AWS-SDK providers as "not a good fit."
- **Specmatic** <https://specmatic.io> · docs <https://docs.specmatic.io> — contract-as-executable; stub and provider-test share one OpenAPI source. Preventive/spec-first; does not audit existing hand mocks in place.
- **Microcks** <https://microcks.io> — mocks + conformance from one artifact.
- **Optic** <https://github.com/opticdev/optic> — API diff from real traffic (archived Jan 2026).
- **Schemathesis** <https://schemathesis.readthedocs.io> · **Dredd** <https://dredd.org> — does the live API conform to its spec (needs a spec + live API).
- **Prism** (Stoplight) <https://stoplight.io/open-source/prism> · **WireMock** record/playback <https://wiremock.org/docs/record-playback> · **Mountebank** <https://mbtest.org> · **MSW** <https://mswjs.io> · **Hoverfly** <https://docs.hoverfly.io> · **Polly.js** <https://netflix.github.io/pollyjs> · **MockServer** <https://www.mock-server.com> — mock/record-replay mechanisms.
- ThoughtWorks Technology Radar — **Consumer-Driven Contract Testing.** <https://www.thoughtworks.com/radar/techniques/consumer-driven-contract-testing>
- Georg-Daniel Schwarz — **"Ensuring Syntactic Interoperability Using Consumer-Driven Contract Testing"** (*STVR*, Wiley, 2025). <https://doi.org/10.1002/stvr.70006>

## Test smells (and the gap this skill names)

- van Deursen, Moonen, van den Bergh, Kok — **"Refactoring Test Code"** (2001) — origin of *Mystery Guest*, *Resource Optimism*.
- Garousi & Küçük — **"Smells in software test code: A survey of knowledge in industry and academia"** (*JSS* 138, 2018). <https://doi.org/10.1016/j.jss.2017.12.013> — 196 smells; none names "a mock whose response shape was never verified." "Counterfactual fixture" fills that gap.

## Golden / approval / characterization testing

- ApprovalTests (Llewellyn Falco) <https://approvaltests.com> — approval/golden testing.
- Michael Feathers — *Working Effectively with Legacy Code* — characterization tests. A snapshot answers "did the output change?", never "is it correct?"

## Mutation testing (weak-mock detection — complementary, not equivalent)

- **PIT / pitest** <https://pitest.org> — mutation testing.
- Vera-Pérez, Danglot, Monperrus, Baudry — **"A comprehensive study of pseudo-tested methods"** (*EMSE*, 2019). <https://dl.acm.org/doi/abs/10.1007/s10664-018-9653-2> — detects decorative/assertion-free tests, but a mutation-adequate suite can still run entirely on a fictional mock.

## Property-based testing & fuzzing (the coverage axis)

- **Hypothesis** — *"Domain and distribution."* <https://hypothesis.readthedocs.io/en/latest/explanation/domain.html> — you own the **domain** (inputs that should be generatable), the library owns the **distribution** (tuned to find bugs, not to be realistic); use the most-general domain or you exclude the bug-triggering values. Reframed onto the *response* side, it names the coverage gap a recorded double leaves: a cassette is one real point in a response domain the real service samples far more widely. Also the source of the *known-unknowns vs unknown-unknowns* framing.
- **HypoFuzz** <https://hypofuzz.com> — coverage-guided fuzzing backend for Hypothesis; runtime feedback reshapes the distribution to trigger new behaviours. The engine behind "explore the recorded response domain," and the practical route to the unknown-unknowns.

## Tooling used by the skill

- **vcrpy** <https://github.com/kevin1024/vcrpy> · **pytest-recording** <https://github.com/kiwicom/pytest-recording> — recording engine + `--block-network` guardrail.
- **pytest-socket** <https://github.com/miketheman/pytest-socket> — "block the network, fail loud on an un-recorded call" (standard practice, not novel to this skill).

## AI-era practitioner writing & tooling (the 2025–26 frontier)

- Nazar Boyko — **"AI For Test Generation: Where It Helps And Where It Lies."** <https://dev.to/nazar-boyko/ai-for-test-generation-where-it-helps-and-where-it-lies-jhm> — nearest single practitioner analog: boundary triage + "fixture from a real captured response, not the AI's guess" + the shared-blindness mechanism.
- asmyshlyaev177 — **"Record real responses instead of writing mocks."** <https://medium.com/@asmyshlyaev177/testing-next-js-ssr-with-playwright-record-real-responses-instead-of-writing-mocks-fb56310aff6b> — the clearest statement of the core premise.
- **AIMock** (CopilotKit) — <https://www.copilotkit.ai/blog/aimock-one-tool-to-mock-your-entire-ai-stack> — nearest *tooling* analog: three-way drift detection (SDK types vs real API vs mock). Stops at shape; no triage, no oracle framing.
- "Your AI-Generated Tests Are Lying to You" <https://singhpr.medium.com/your-ai-generated-tests-are-lying-to-you-and-what-to-do-about-it-57fb0e5f2783> · "AI-generated tests pass but don't assert" <https://getautonoma.com/blog/ai-generated-tests-pass-but-dont-assert> — the failure-mode genre.
- qaskills.sh — Claude Code QA skills catalog (415 skills). <https://qaskills.sh/agents/claude-code> — a large curated QA-skill directory that still ships no skill for validating mock responses against real service behavior (the gap this skill fills).

## Engineering fundamentals (sibling-skill framing)

- David Thomas & Andrew Hunt — *The Pragmatic Programmer* (20th Anniversary ed., 2019). <https://pragprog.com/titles/tpp20/the-pragmatic-programmer-20th-anniversary-edition/> — *"The rate of feedback is your speed limit."* Frames why a counterfactual mock is worse than a missing test: it corrupts the feedback loop that `tdd` (red-green-refactor) and `diagnosing-bugs` (reproduce-then-fix) depend on — the green reads true while validating a fiction. Anchors this skill's place among the feedback-loop siblings (background.md §5).

## Out of scope (noted for boundary-drawing)

- arc42 quality portal — **"How to Specify Quality Requirements."** <https://quality.arc42.org/articles/specify-quality-requirements> — requirements engineering: turning vague -ilities into measurable acceptance criteria / quality-attribute scenarios. *Upstream* of this skill and deliberately out of scope (deciding *what* to test, not whether a test's stand-ins are real). Recorded here to document the boundary decision, not as a method source.

## Sibling skills

`mock-code-finder_v1` (incompleteness axis) and `testing-metamorphic_v6` (oracle
axis) are cross-linked once, from the three-axis table in `SKILL.md`.
