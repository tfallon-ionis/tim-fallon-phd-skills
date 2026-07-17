# Record/Replay Seams — earning a cassette when VCR can't record the transport

The fidelity audit's preferred fix is **record-to-falsify**: replay the *real*
interaction and re-derive assertions from the real body (SKILL.md, Audit recipe
step 3). For HTTP that's a solved problem — `pytest-recording`/VCR intercepts the
client library and writes a **cassette**. But VCR only works for HTTP. The moment
the dependency speaks a different transport — a database wire protocol, gRPC, a
message queue, raw TCP-over-TLS — the convenient recorder is gone, and the usual
reflex is to hand-write a fake. A hand-written fake is exactly the
**counterfactual** risk this skill exists to catch.

This file is the map for that situation: **where can you intercept a non-HTTP
dependency to record it, and what does each interception point cost?** It
generalizes the "one honest fake" problem (a pymongo stand-in that reimplements
the query) into a reusable decision framework.

Terms in **bold** are the parent skill's vocabulary (SKILL.md Glossary):
*cassette*, *corresponds*/*counterfactual*, *provenance*, *golden snapshot*,
*oracle problem*.

---

## 1. Why recordability is really about *seams*

VCR works for HTTP because of three properties that all happen to hold at the
HTTP-client-library seam:

1. **It's above encryption.** The seam sits above TLS, so the payload is already
   plaintext and structured.
2. **Request↔response is correlatable.** HTTP is stateless enough that a reply
   can be keyed to a request (`match_on`) without replaying a stateful handshake.
3. **Non-determinism is normalizable.** Timestamps, auth headers, nonces can be
   filtered/matched out (`filter_headers`, custom matchers).

"**VCR-incompatible**" simply means the *convenient* seam fails one of these —
usually #1 (you'd be intercepting below TLS) or #2 (the protocol is stateful:
cursors, stream IDs, session handshakes). The whole problem reduces to: **pick a
different seam, and pay for whatever encryption / protocol-state / non-determinism
sits at it.**

So the general question is never "is X recordable?" but "**at which seam, and at
what cost?**"

---

## 2. The seam ladder (the map)

Interception points, ordered from application logic down to the wire. Higher =
more structured/decrypted/matchable, but proves *less* about the real transport.
Lower = more transport fidelity, more protocol-state and TLS pain.

| Seam | Plaintext? | Correlation | Language-agnostic? | Recording or fake? | Tools |
|---|---|---|---|---|---|
| **App / object API** (fake the client) | n/a | n/a — reimplemented | no | fake (reimplementation) | mongomock; hand fakes |
| **Client-library transport adapter** ← *VCR lives here* | ✅ above TLS | easy (HTTP) | no (per-lang) | **recording** | vcrpy / pytest-recording, go-vcr, Ruby vcr |
| **Driver interceptor / observability hook** | ✅ driver already decoded + decrypted | driver hands you req + reply | no (per-driver) | **recording** | `pymongo.monitoring` (`CommandSucceededEvent.reply`), gRPC interceptors, Google `rpcreplay`, grpc-tools |
| **Protocol-aware record/replay proxy (MITM)** | ✅ *if it terminates TLS* | ✅ *only for protocols it parses* | **✅ yes** | **recording** | mitmproxy, WireMock, Hoverfly, Mountebank, Keploy, Speedscale proxymock |
| **Raw TCP / packet capture** | ❌ ciphertext under TLS | ⚠️ bytes; no protocol state | ✅ | positional byte-replay (deterministic protocols only) | tcpdump/pcap; Wireshark/tshark (decode-only, ~3000 dissectors); Wiresham, pplay (server-side byte-replay); mitmproxy `--mode tcp` |

**The routing rule:** *use the highest rung that exists for your dependency.*
Higher rungs give you plaintext + correlation for free; lower rungs make you
rebuild them. Recording (any middle rung) beats a fake (top rung) on **provenance**
— but only if a recordable seam is actually reachable.

**Two families of stand-in.** The ladder above is *interception* — you tap the
client's own outbound path. There is a parallel family, **endpoint substitution**:
instead of intercepting, you point the client at a stand-in *server*. Three
flavors, by ascending fidelity: an **object fake** (mongomock — not a server at
all; reimplements the query engine); a **protocol-faithful fake server** (MockupDB
— speaks the real wire protocol in-process, serves replies you supply); and a
**real server** (ephemeral `mongod` via testcontainers / `pymongo_inmemory`). The
middle one is the important, easily-missed case: it is the *only* option that keeps
**wire-protocol fidelity** while staying **in-process and committed-cassette** — see
§3.

---

## 3. The rungs, in practice

**App/object fake (mongomock and friends).** Not a recording — a
*reimplementation* of the dependency's query engine. Cheap, offline, per-language.
Its value is narrow but real: it retires "did I reimplement the query semantics
correctly?" by delegating to a maintained engine. Its ceiling is equally real: it
proves nothing about what the *actual* service returns, and mongomock ≠ the vendor
(e.g. mongomock ≠ DocumentDB). Use it to harden a fake against **query-shape
drift**, not to establish fidelity.

**Client-library transport adapter (VCR).** The sweet spot *when it exists*. If the
client is HTTP under the hood, this is the answer — stop reading. Everything below
is for when it isn't.

**Driver interceptor / observability hook.** The most *underused* general answer,
and usually the right one for "VCR-incompatible but well-supported driver." Modern
drivers expose a monitoring/interceptor API *above* the wire and *above* TLS,
where request and reply are already structured. `pymongo.monitoring`'s
`CommandSucceededEvent.reply` is the actual reply document DocumentDB returned;
gRPC has client interceptors; `rpcreplay`/grpc-tools productize this for gRPC. You
get a **true recording** with no query reimplementation — but the API is
**observe-only** (a listener records `CommandSucceededEvent.reply`; it cannot
replay), and there's rarely a drop-in library, so this rung is always *two*
pieces: the listener that serializes plus a separate fake client that serves the
recorded reply back. For **non-determinism in the request** (a dynamic watermark,
a timestamp) the reflex is to normalize it out of the match key (VCR's `match_on`,
now yours) — but when the varying value *also drives pagination* there may be
nothing stable to match on, in which case **replay positionally** (Nth call → Nth
recorded reply) and assert the query shape separately. We built exactly this rung
for the §5 case — its postscript is the field report.

**In-process wire-protocol fake server (MockupDB).** The endpoint-substitution
sweet spot when you want more than mongomock but refuse an out-of-process platform.
MockupDB (mongodb-labs, Apache-2.0, `pip install mockupdb`) binds an ephemeral
`localhost` port and serves the real **MongoDB wire protocol (OP_MSG)** from a
background thread *inside the pytest process* — no Docker, daemon, account, or
privileges; pytest stays in control. You point pymongo at it and hand back recorded
replies (your committed dump docs, or replies captured via `pymongo.monitoring`).
Two things make it a genuine step up from mongomock while staying in-model: (1)
pymongo's **real client wire code runs** — handshake, OP_MSG encode/decode, cursor
`firstBatch` handling — none of which an object fake exercises; and (2) it **does
not reimplement the query engine** — it serves your recorded reply verbatim for a
matched command, so the `$gt`/sort/limit reimplementation fragility disappears at
the wire seam. Two caveats: you still own the request→reply **matching** (and a
dynamic watermark needs a *tolerant* matcher — the same normalization tax as any
recorder here, §7); and **maintenance is the gate** — the last PyPI release is
1.8.1 (Oct 2021), which *predates pymongo 4.0* and declares only `pymongo>=3`, so
compatibility with a modern driver is unverified. Spike it (a ~10-line "does my
pymongo talk to it?" smoke test) before adopting; if it fails on 4.x, this
in-process-wire niche is otherwise empty. (Do not confuse MockupDB with a
*recording* tool — it's a fake server you drive; recording is a separate,
one-time concern via the dump or `pymongo.monitoring`.)

**Protocol-aware record/replay proxy (MITM).** See §4 — this is the rung people
reach for when they think "general solution," so it gets its own section.

**Raw pcap — with two corrections, because both usual dismissals are too strong.**
"Dead on arrival, no semantics, no tooling" is the reflex; the truth is narrower.

*Correction 1 — the semantics usually exist (Wireshark), but it's a decoder, not a
replayer.* A *dumb* TCP proxy records bytes, but **Wireshark/tshark ship ~3000
dissectors** (including a `mongo` one that decodes OP_MSG), so the protocol
semantics are typically already solved for *display*. Two things still stop it
being a fixture: it has **no return half** — it hands you a real *transcript*
(`tshark -T json`), never serves a reply — and it decrypts TLS only **post-hoc,
with exported session keys** (`SSLKEYLOGFILE`; for pymongo that means
monkeypatching `SSLContext.keylog_filename`, since CPython's `ssl` ignores the env
var). Its real role here is **verification / provenance**: cross-check that a
higher-rung recording matches the real wire, or source a transcript for an exotic
protocol with no driver hook and no proxy parser. (`tcpreplay`/`tcpliveplay` don't
fill the replay gap — they replay the *client* side against a **live server**, the
§4 "pointed the wrong way" problem.)

*Correction 2 — server-side pcap-replay fixtures do exist, but they're positional
byte-replayers.* **Wiresham** (abstracta — loads pcap / Wireshark-json / a
committable `.yaml` and answers a live client) and **pplay** (astibal) genuinely
act as the *server*, offline. But they **do not parse the protocol**: Wiresham
reads the dump *sequentially and ignores any out-of-order packet*, so they inherit
*both* rung costs at once. TLS: Wiresham has none (needs a **plaintext** capture);
pplay decrypts by pairing with a `smithproxy` MITM — i.e. it **rebuilds the proxy
tier** upstream just to feed the replayer. Statefulness: byte-in-recorded-order
replay **desyncs on any per-session non-determinism** — Mongo's client-assigned
`requestId`s, server-assigned `cursorId`s, and fresh SCRAM nonces all differ each
run, at which point Wiresham "will not answer until the next expected packet" (it
hangs). So these tools are the **dumb-byte proxy productized and pointed the right
way** — legitimately nice for a *deterministic, single-stream, plaintext* TCP
service (a fixed-field legacy protocol), and **wrong for Mongo-over-TLS**. This is
exactly *why* the §4 proxy tools terminate TLS and parse the protocol instead of
sniffing packets.

---

## 4. The MITM proxy tier — the "general" rung, and its real boundary

A protocol-aware MITM proxy is the most *general single mechanism* because it does
two hard things at once: **terminates TLS** (you inject its CA into the client, so
it sees plaintext) and **parses the protocol** (so it can match and replay). Its
genuine superpower is that it's **out-of-process and language-agnostic** — one
cassette store for a polyglot fleet — which the in-process rungs can't offer.

But "**general**" is entirely load-bearing on "**protocols the proxy has a parser
for**," and the failure mode is precise:

- A *protocol-agnostic* TCP proxy records **bytes**. Byte-replay only survives a
  strictly lockstep, deterministic, single-stream request/response protocol. The
  instant there's statefulness or multiplexing — a server-assigned MongoDB
  `cursorId`, an HTTP/2 stream ID, a SCRAM auth handshake, a `requestId`/`responseTo`
  correlation — dumb replay breaks. You'd have to write a **protocol-specific state
  machine in the proxy**, which is just the in-process correlation problem relocated
  to the network path.
- **TLS termination needs CA injection** (trust store / env like `REQUESTS_CA_BUNDLE`,
  or the driver's `tlsCAFile`), and **certificate pinning defeats it** outright.

So the proxy generalizes *across languages and across any protocol someone wrote a
parser for* — **not** across arbitrary binary protocols. It relocates costs #1–#3
from §1; it doesn't abolish them.

**Tool reach (as of 2026):**

- *HTTP family:* mitmproxy (HTTP/1·2·3, WebSocket; also a *generic* TCP/UDP mode
  that MITMs the TLS but forwards **bytes only** — no protocol parser), WireMock
  (HTTP/HTTPS record & playback, **+ gRPC** via extension: proto↔JSON, now
  records), Hoverfly (HTTP/S only).
- *Multi-protocol:* Mountebank (http/https/**tcp/smtp**; the `tcp` imposter
  carries binary payloads as base64 but makes *you* supply the framing — a custom
  `endOfRequestResolver` for length-prefixed messages — *and* the request→reply
  correlation).
- *Databases & queues:* **Speedscale proxymock** (HTTP, gRPC, PostgreSQL, MySQL,
  Kafka, RabbitMQ, Pub/Sub, several AWS services) and **Keploy** (parses the
  MongoDB **wire protocol**, wiremessages ≥ MongoDB 5.1.x, and others). These two
  *do* cover MongoDB — corrected from an earlier assumption that no Mongo
  record/replay proxy existed.

Only the last pair actually *parses* the Mongo wire protocol. The HTTP-family and
`tcp`-imposter tools reach the transport but not the semantics — see the six-way
proxy split in §5 for how that plays out for the pymongo case (four of six miss).
- *gRPC-specific:* Google `rpcreplay`/go-replayers, grpc-tools
  (`grpc-dump`/`grpc-replay`/`grpc-fixture`), grpcreplay.
- *In-process wire fake:* MockupDB — an endpoint-substitution stand-in, **not** a
  proxy (it earns its own treatment in §3). Listed here only so it isn't mistaken
  for one: it's the answer to "wire fidelity without leaving the pytest process."

**Do not confuse a load generator with a fixture.** flashback and mongoreplay
capture *operations issued to* MongoDB (via profiler/oplog or wire capture) and
replay them *into* a live server to benchmark it. They record the request side,
need a live populated server, and are pointed the wrong way (client→server). A
**fixture needs the server→client reply, served offline** — the mirror image.
flashback is also archived (2018) and Python-2 era.

**Aside — how the two Mongo-wire tools intercept: eBPF-wrap (Keploy) vs remap
(proxymock).** They capture traffic by different mechanisms, and the difference is
why one needs privileges and the other doesn't:

- **proxymock — explicit remap.** You change the app's connection target to
  proxymock's local port; it forwards to the real DB (record) or serves recorded
  replies (replay). Nothing magic — a normal proxy in the path. Setup is a
  URI/config change plus TLS trust; **no special privileges.**
- **Keploy — transparent eBPF interception.** **eBPF** (extended Berkeley Packet
  Filter) lets a program attach small, sandboxed hooks *inside the running Linux
  kernel* — here, on the network syscalls a process uses to send/receive data.
  Keploy runs your test command as a child (`keploy test -c "pytest ..."`) and
  attaches eBPF hooks that transparently redirect *that process's* network I/O to
  Keploy's internal proxy — **no URI change, no code change; the app doesn't know
  it's intercepted.** The price: loading eBPF programs touches the kernel, so it
  needs **elevated privileges** (root / `CAP_BPF` / `CAP_NET_ADMIN`) and is
  **Linux-kernel-specific** — awkward in locked-down CI, containers, or non-Linux
  dev boxes. That's the "wraps the test runner via privileged eBPF" shorthand:
  Keploy is a *parent* process transparently intercepting its child, where
  proxymock is a dumb pipe you deliberately point at. The trade is convenience
  (zero app change) for privilege + platform coupling.

---

## 5. Worked case study — the pymongo `tail` loop test

The concrete situation that produced this file. `tail_process_events` pages
DocumentDB with `coll.find({utcTime: {$gt: watermark}}).sort(...).limit(...)`.
pymongo speaks the binary MongoDB wire protocol over TLS, so **VCR can't record
it**. The loop test uses a hand fake — a `_FakeCollection` that reimplements the
`$gt`/sort/limit query — serving **real docs** extracted from a production
`process.bson` dump.

The options, ranked, and where each lands:

| # | Option | Seam | Git-committable cassette? | Verdict for this test |
|---|---|---|---|---|
| 1 | **mongomock** | app/object fake | △ No cassette (reimplements) — but its input fixture docs are committed JSON | Retires query-shape-drift risk with a maintained engine; offline; cheap. Not a recording, not DocDB. **Best cost/benefit.** |
| ★ | **MockupDB** (in-process wire fake) | endpoint substitution | ✅ Yes — the reply docs you feed it (committed JSON/BSON) | The in-process, committed-cassette answer *at wire fidelity*: real pymongo wire code runs, no query reimplementation. Gated on a maintenance/compat spike (1.8.1, 2021, pre-pymongo-4.0). If it passes, the strongest "stay in the pytest model" option. |
| 2 | **`pymongo.monitoring` recorder** | driver interceptor | ✅ Yes — JSON you serialize yourself (tidy, diffable) | The true cassette — real DocDB replies, no query reimplementation, offline replay. **Built (§5 postscript):** the watermark *drives pagination* → **positional** replay, not match-normalization; the real gain is the reply **envelope**, not the (already-real) docs; observe-only, so a two-part harness. |
| 3 | **ephemeral real mongod** (testcontainers / `pymongo_inmemory`) | real server | ✗ No — live server, ephemeral state (only the seed data commits) | Real engine, no reimplementation — but it's **MongoDB, not DocumentDB**, and adds Docker/binary + slower tests. Neither a recording nor the real target. |
| 4a | **Speedscale proxymock** (Mongo-wire proxy) | MITM proxy | ✅ Yes — RRPair text files, git/diff-friendly and editable | **Records real DocumentDB** — the actual target mongomock/testcontainers can't reach — via a genuine MongoDB-wire parser (OP_MSG: `hello`/`isMaster`, SCRAM auth, `find`/`getMore`/`aggregate`), stored as editable JSON. **Productized** (no build-it-yourself), committable RRPairs; adoption is a **connection-string remap** — Mongo drivers ignore `http_proxy`/`ALL_PROXY` (esp. Java's NIO/Netty transport), so you point the *URI* at it, not the environment. No privileges. Deciding gate is **credential redaction**, which is a **paid tier** here (§6), not in-process. |
| 4b | **Keploy** (Mongo-wire, eBPF) | MITM proxy | ✅ Yes — `keploy/` YAML (tests + mocks), human-readable | Same genuine Mongo-wire record/replay (parses wiremessages, MongoDB ≥ 5.1.x), plus **auditable Apache-2.0 OSS** — redact creds yourself, free. But intercepts by **eBPF-wrapping the test runner** (§4 aside) → kernel privileges (root / `CAP_BPF` / `CAP_NET_ADMIN`), **Linux-only** — heavier to wire into CI than proxymock's remap. |
| 4c | **Mountebank** (tcp imposter) | MITM proxy (bytes) | ✅ Yes — JSON imposters (but you hand-author the Mongo framing) | Speaks **tcp**, not Mongo. Its `tcp` imposter carries binary payloads (base64) but makes *you* supply Mongo's framing (a custom `endOfRequestResolver` for the 4-byte length prefix) **and** the request→reply correlation (cursorId, handshake). That's the §1 #2 correlation cost *relocated into the proxy as hand-written JS*, not solved. Reachable in principle, a protocol-implementation project in practice. |
| 4d | **mitmproxy** | MITM proxy (bytes) | △ Binary `.mitm` flow (HAR/JSON export); bytes-only for Mongo | TLS MITM is its strength (detects TLS, CA-injects; HTTP/1·2·3 + WebSocket, generic TCP/UDP) — but it has **no MongoDB parser**. For Mongo you fall to its **raw-TCP mode, which forwards bytes only**: TLS solved, protocol semantics not — so it collapses to rung 5 with §1 #2 still open. A great HTTP recorder; not a Mongo one. |
| 4e | **WireMock** | MITM proxy | ✅ Yes — JSON stub mappings (HTTP/gRPC only) | **HTTP/HTTPS** record & playback, plus **gRPC** via extension (proto↔JSON, now records). **No MongoDB wire protocol** — off-target for this test entirely. |
| 4f | **Hoverfly** | MITM proxy | ✅ Yes — JSON simulation file (HTTP only) | **HTTP/S only.** No Mongo transport at all — off-target. |
| 5 | raw pcap / server-side byte-replay (Wiresham, pplay) | packet capture | △ pcap is binary; Wiresham's reduced YAML does commit | Still a non-starter *here*, for two reasons at once: needs a **plaintext** capture (DocDB is TLS-only) and, being **positional byte-replay not protocol-aware**, desyncs on Mongo's per-session `requestId`/`cursorId`/SCRAM-nonce non-determinism. Wireshark *decodes* the wire (verification oracle) but can't replay it. Fits only deterministic single-stream plaintext protocols. |

**The proxy tier is not one option — it's six, and four miss.** "Use a MITM proxy"
is the reflexive "general" answer, but generality is load-bearing on *having a
parser for the protocol* (§4). For the Mongo-wire case only **proxymock** and
**Keploy** actually parse it; **WireMock** and **Hoverfly** are HTTP-family
(off-target), and **Mountebank**/**mitmproxy** can carry the TLS+TCP bytes but
hand you back the Mongo state machine to write yourself — which is the very
correlation cost (§1 #2) you were trying to avoid. So the honest proxy shortlist
here is two, not six.

*Cassette column — the property worth wanting.* **✅** = a **tidy, diffable,
version-controllable recording file** (plain-text JSON/YAML) you commit like a VCR
cassette and a reviewer can read in a PR; **△** = an artifact exists but is binary
(`.mitm`, pcap) or only partly tidy, or the recording isn't the tool's own output
(mongomock commits its *input* fixture, not a captured cassette); **✗** = no
committable recording at all — a live server (ephemeral state) or a pure
reimplementation. The ✅ is the same shape the suite's existing VCR cassettes
already have: a committed plain-text fixture the next reader can diff. Note it's an
**orthogonal axis to fidelity** — proxymock/Keploy score ✅ *and* record the real
DocumentDB, while mongomock is in-model but ✗-as-a-cassette; a tidy committable
file is necessary for a reviewable fixture but says nothing on its own about
whether the shape **corresponds**.

**The monotonic result is itself the lesson:** below the top rung, *each step
costs more and — because the fixture docs are already real and the pagination
logic lives in your own code — buys less.* The rational stopping points are the
**top of the ladder (mongomock)** or **leaving the fake as-is with a comment
naming the fragility boundary**.

And the fragility boundary is narrow *here* for a specific reason worth
generalizing: the query is `$gt` on an **ISO8601 string** plus a **string sort**,
which Python's `>`/`sort` replicate exactly — so the reimplemented fake happens to
be faithful. The risk isn't today's correctness; it's **evolution**: add an
`$in`, a `Date` comparison, a `$regex`, or an aggregation, and the hand fake
silently diverges while staying green. That is precisely the drift mongomock (rung
1) immunizes against — which is why rung 1, not a heavier rung, is the answer when
you *do* act.

**Where MockupDB fits the ranking (★).** It isn't a rung on the interception ladder
— it's *endpoint substitution* — so it sits off to the side of the "each step costs
more, buys less" line rather than on it. It answers a *specific* constraint the
others each miss: "I want wire-protocol fidelity and no query reimplementation, but
I refuse to leave the in-process, committed-cassette model." mongomock is in-model
but reimplements the query; the monitoring recorder is a true cassette but
build-it-yourself; the proxies give wire fidelity but out-of-process. MockupDB is
the only option that holds all three at once — *if* it still works with a modern
pymongo. That single "if" (2021 dormancy, pre-4.0) is the whole reason it carries a
★ instead of being the unqualified pick; resolve it with a compatibility spike
before betting a suite on it.

**The ranking is conditional — relax a constraint and it reshuffles.** The order
above quietly assumes two things this suite happens to value: staying **in-process**
and avoiding a **data-governance** review. Neither is a law. **In-process is a
preference, not a correctness property** — a proxy you deliberately remap to
(proxymock) is genuinely low-friction, and if you don't need everything inside the
pytest process, "out-of-process" stops being a real cost. Relax *both* constraints
(non-sensitive data, external recorder acceptable) and **proxymock jumps up the
list**: it records replies from **real DocumentDB** with a one-line remap — which is
*higher* fidelity to the actual target than mongomock (reimplemented) or an
ephemeral MongoDB (wrong server), and productized rather than the hand-rolled
`pymongo.monitoring` recorder. At that point the last thing between you and it is
**credentials in the recording** — which, crucially, is *not* a proxymock-specific
problem (§6). So treat the numbered order as "for a suite that prizes in-process +
zero-governance"; name your own constraints and re-rank accordingly.

**Postscript — we built rung 2. The bill, and what it taught.** This case study
stopped being hypothetical: the `pymongo.monitoring` recorder was built and a real
DocumentDB recording captured. We deliberately went one rung deeper than this
section's own advice (stop at mongomock, or leave the fake with a comment) — for
the one thing fixture docs can't supply: the real reply **envelope** (cursor /
`getMore` shape, `ok`, `ns`) and a committable linked-data cassette. Six things the
build taught that the paper analysis didn't:

1. **`pymongo.monitoring` is observe-only — the rung is always two halves.** A
   listener *records* (`CommandSucceededEvent.reply` is the real reply) but cannot
   *replay*. So "driver interceptor" is never one component: a listener that
   serializes + a separate fake client that serves the cassette back. The player is
   the larger half.
2. **Positional replay beat match-normalization.** The watermark is *both*
   non-deterministic *and* the thing that drives pagination (`{$gt: …}`, advancing
   each page), so there is no stable key to match on. Replaying **positionally**
   (Nth `find` → Nth recorded reply, guarding only command-name + collection) and
   asserting the query shape *separately* — against the command the player observed
   — is cleaner than normalizing a value that is *supposed* to change. Store the
   issued command in the cassette for readability; don't match on it.
3. **A `provenance` flag makes design-now-record-later safe.** The cassette is
   stamped `synthesized-example` | `recorded-live`; the envelope-fidelity assertions
   are *skipped* unless `recorded-live`. The harness shipped and ran offline against
   a hand-shaped example, with a hard guarantee a synthesized envelope can never be
   *asserted as real*; when the VPN recording landed the flag flipped and the
   assertions activated by themselves. That flag is the whole mechanism behind
   "design the recorder now, capture the bytes later."
4. **The real surprise: a recording doesn't fit the curated fixture's shape.** The
   behavior tests were built on a hand-curated fixture — five docs, one per
   `trace.status`, small enough for exact page-count assertions. A real capture is
   *whatever the window held*: dozens of docs, only the statuses that happened
   (here just COMPLETED/FAILED), page counts tied to real volume. So "the recording
   replaces the fixture" **breaks the deterministic tests**. Two honest fixes:
   **(a) two cassettes** — keep the curated synthesized one as behavior-test data,
   add a recorded-live one whose only job is the envelope; or **(b) adapt the
   tests** — derive expectations *from* the data (`statuses == {d.status for d in
   real_docs}`), test count-free invariants via *constructed* inputs (build an
   ABORTED doc to exercise that path rather than hoping the window held one), and
   pin count-dependent loop tests to a fixed slice (`real_docs[:5]`). This is
   invisible until the real bytes arrive — decide it *before* you record.
5. **Credential hygiene at the driver seam is a drop-list, and it held.** The
   listener records only `find`/`getMore`, drops the handshake/auth/teardown
   commands (`hello`/`isMaster`, `ping`, `saslStart`/`saslContinue`, `endSessions`),
   and strips volatile session keys (`lsid`, `$clusterTime`) from what it keeps —
   the driver-seam analogue of VCR's `filter_headers`. Swept against a live
   *authenticated* DocumentDB recording: no password, no SCRAM nonce, no host, no
   session id in the committed file. §6's "monitoring redacts for free" is a
   two-line drop-list, not a hope.
6. **Register globally; bound the window.** `pymongo.monitoring.register(listener)`
   *before* the client is built captures the production tail with **zero
   production-code change** (no `event_listeners=` kwarg threaded through the app). A
   `--max-events` bound is legitimate *scoping*, not trimming — "record full, never
   trim" forbids downsampling a *captured* interaction, not choosing how wide a
   window to capture.

**The honest scorecard:** rung 2 delivered exactly the one thing the fixture
couldn't — a real, committed reply **envelope**, now asserted in CI — at the cost
of a two-part harness, a provenance-gated test, and a suite adaptation nobody
foresaw until the data landed (point 4). If the envelope shape isn't a risk you
carry, this section's original advice still stands. If it is, the six points above
are the price list.

---

## 6. The corporate / licensing gate (before you adopt a proxy tool)

If the chosen seam is an external proxy tool, the deciding review is usually **not
the license** — it's **data governance**, because these tools work by *recording
real traffic*.

- **License is rarely the blocker.** Keploy is **Apache-2.0**, genuinely open
  source, self-hostable. proxymock's CLI is **free for local use**; its npm
  installer is Apache-2.0 but the **core engine's source isn't published** — treat
  it as *free proprietary freeware from a vendor*, not OSS (only the UI/examples are
  open). Apache-2.0 is on every corporate allowlist and is generally *preferred*
  over MIT (explicit patent grant), so "not MIT" is not an obstacle.
- **The real gate is what gets recorded — and it often collapses.** Recording real
  traffic can capture **production data** (for an NGS/pharma system: library/study
  records, potentially PII/IP). But when that payload is **non-sensitive** — as much
  pipeline-metadata traffic is — this concern largely evaporates, and the
  data-governance review is clearable. Don't over-weight it reflexively; ask what's
  *actually* in the traffic first.
- **Credentials are the residual that survives even non-sensitive data.** Every
  recording seam captures the **auth handshake** (Mongo creds, SigV4 tokens) —
  regardless of how boring the payload is. So credential redaction is the one
  governance task you can't skip. The good news: it's **universal and already
  solved in this suite** — the VCR cassettes redact `authorization` / SigV4 via
  `filter_headers` in `conftest.py` (the boto3 `filter_headers` REDACTED pattern).
  The catch is tool-specific: **proxymock paywalls redaction**, whereas VCR, a
  `pymongo.monitoring` recorder, and **Keploy** (auditable OSS) all let you scrub
  creds for free. If credentials are your *only* sensitivity, that fact alone nudges
  away from proxymock's free tier toward a seam where you control redaction.

Net: on licensing you *can* use any of them; **the review usually reduces to
credential redaction, not payload sensitivity.** For non-sensitive data with only
creds to scrub, prefer a seam that redacts for free — VCR / `pymongo.monitoring` /
**Keploy** over proxymock's free tier. If you ever adopt one org-wide, Keploy is the
more defensible pick (auditable OSS, self-hosted, free redaction).

---

## 7. Invariants that survive every seam

No seam changes these — they're the parent skill's caveats, restated for the
record/replay context:

- **A recording proves shape, never correctness.** Whatever the seam, you get a
  **golden snapshot**: the reply's *shape was once real*, not that the output is
  *right*. If you can't state the correct output (ML/ranking, solvers), that's the
  **oracle problem** — reach for metamorphic testing (`testing-metamorphic_v6`),
  not a heavier recorder.
- **Matching / normalization is the perennial hard part**, at every rung — VCR's
  `match_on`, a monitoring recorder's command-key, WireMock's predicates,
  proxymock's field matchers. It only gets harder as the protocol gets more binary
  and stateful. Budget for it.
- **Real inputs ≠ proven behavior.** Feeding real recorded docs through a *fake*
  transport (as the pymongo test does) is honest about **shape** but still leans on
  your own logic for query/pagination semantics — name that boundary in a comment
  so the next reader knows what is and isn't proven.
- **A real recording won't fit a curated fixture's shape.** The moment a *real*
  capture replaces a hand-shaped fixture (small N, one-of-each-case), the data is
  whatever the window held — only the cases that actually occurred, page counts
  tied to real volume — so deterministic tests built on the curated shape break.
  Decide up front whether the recording is *additional* (prove the envelope; keep
  the curated fixture as behavior-test data) or *replaces* it (then derive
  expectations from the data and test count-free invariants via constructed
  inputs). Invisible until the bytes land; it bit the §5 build (postscript, point
  4). True at every seam, VCR included.
- **The wire is the final oracle.** Whatever rung you recorded at, Wireshark/tshark
  (given the TLS keys) can confirm the recorded reply matches the real bytes — the
  one independent cross-check that spans every seam, precisely because it *decodes*
  ~3000 protocols and *replays* none, so it can't launder its own recording.

---

## 8. Bottom line (the heuristic to carry away)

> When VCR can't record the transport, **walk the seam ladder top-down and stop at
> the first rung that is both reachable and worth its cost.** For a
> well-instrumented in-process driver that's usually the **driver-interceptor**
> rung (a real recording) or, if the only real risk is query-shape drift, a
> **maintained API-level fake** over real fixture data. If you want
> **wire-protocol fidelity without leaving the pytest process**, an **in-process
> wire-protocol fake server** (MockupDB) is the endpoint-substitution option that
> stays in the committed-cassette model — gated only on its modern-driver
> compatibility. Reach for a **proxy** when there's no in-process seam, when you
> want **real replies from the actual target** (proxymock records real DocumentDB,
> which fakes and ephemeral servers can't), or when you want one cassette store
> across a polyglot fleet — remembering that **in-process is a preference, not a
> correctness property**, so a remap-to proxy is a fair choice, not a fallback. The
> governance review usually reduces to **credential redaction**, not payload
> sensitivity — so favor a seam that redacts for free (VCR / monitoring / Keploy)
> over proxymock's paid tier. **Raw sockets / pcap** is almost never the answer:
> it's the hardest seam (TLS + wire state machine), not the easiest — and the
server-side byte-replay fixtures that *do* exist (Wiresham, pplay) fit only
deterministic single-stream plaintext protocols, not Mongo-over-TLS.

The mistake to avoid is treating "record the transport" as all-or-nothing and, on
finding VCR won't do it, defaulting straight to a hand fake. There is almost always
a seam between "VCR" and "give up" — most often the driver's own monitoring API —
and it yields a real cassette for far less than a proxy.

*Companion reading:* SKILL.md (the audit and the record-to-falsify move),
background.md §5 (fidelity vs the oracle problem and the coverage floor),
references.md (citations).
