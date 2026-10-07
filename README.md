# GenLayer Reputation Ledger

A reusable on-chain reputation primitive for GenLayer. Any court, escrow, or
verification contract can register as a source and write outcome events.
Any consumer contract can read a weighted trust score for an address.

---

## Why this exists

Dispute resolution, escrow, and verification contracts each generate signals
about who is trustworthy. Today each project builds its own reputation score
in isolation. This ledger is a shared primitive: one score, many writers,
many readers.

- A marketplace using Agent Dispute Court cannot see that a freelancer
  already proved themselves in AI Freelance Escrow.
- A DAO cannot see that a grant recipient was ruled against in a News
  Fact Checker case.

Reputation Ledger fixes this by giving every project a common place to
record and read trust signals.

---

## Contract

- **Network:** GenLayer Studio
- **Address:** `0x2a15c2169Fcdb7a1954BA84aE2af0168fb06001E`
- **Explorer:** https://explorer-studio.genlayer.com/address/0x2a15c2169Fcdb7a1954BA84aE2af0168fb06001E
- **File:** `reputation_ledgerV01.py`

### Deployment verification

| Type | Method | Status | Consensus |
|---|---|---|---|
| Deploy | (constructor) | FINALIZED | Accepted |
| Call | register_source | FINALIZED | Accepted |
| Call | record_outcome | FINALIZED | Accepted |

Deployed on Oct 8, 2026. All three transactions finalized with
SUCCESS result and validator consensus accepted.

---

## Interface

### Owner-only write methods

| Method | Parameters | Notes |
|---|---|---|
| `register_source(source, label, weight)` | source: str, label: str, weight: int | Weight must be 0-100 |
| `update_weight(source, weight)` | source: str, weight: int | Change weight of registered source |
| `revoke_source(source)` | source: str | Sets weight to 0, marks as revoked |
| `set_half_life(seconds)` | seconds: int | Range 1 hour to 10 years |

### Source-only write methods

| Method | Parameters | Notes |
|---|---|---|
| `record_outcome(subject, kind, delta, context_hash)` | subject: str, kind: str, delta: int, context_hash: str | Caller must be registered source |

### View methods

| Method | Returns |
|---|---|
| `get_counts()` | `{sources, events, half_life}` |
| `get_source(address)` | Source metadata or `{registered: false}` |
| `get_sources()` | Array of all registered sources |
| `get_event(id)` | Full event JSON |
| `get_raw_score(address)` | Scaled integer score |
| `get_score(address)` | `{address, score, raw_scaled, events, half_life}` |

---

## Outcome kinds

Fixed vocabulary so consumers can rely on consistent signals across sources:

| Kind | Meaning |
|---|---|
| `DISPUTE_WIN` | Address won a dispute |
| `DISPUTE_LOSS` | Address lost a dispute |
| `ESCROW_COMPLETED` | Address completed an escrow job |
| `ESCROW_FAILED` | Address failed an escrow job |
| `VERIFICATION_PASSED` | Address passed a verification |
| `VERIFICATION_FAILED` | Address failed a verification |

---

## Scoring model

```
effective   = delta * source_weight * SCALE / 100
capped to   MAX_DELTA
final_score = sum(effective) / SCALE
```

Constants:
- `SCALE = 1000` — integer math, no float drift
- `MAX_DELTA = 100 * SCALE` — caps single-event impact
- `HALF_LIFE = 180 days` — default decay window (configurable)

### Example

- Source has weight 50
- Records `DISPUTE_WIN` with `delta = 10`
- Effective = `10 * 50 * 1000 / 100 = 5000`
- Final score contribution = `5000 / 1000 = 5`

Verified on Studio: after 1 event, `get_score()` returned
`{score: 5, raw_scaled: 5000, events: 1}`.

---

## Usage

### As a source contract

```python
gl.call(
    ledger_address,
    "record_outcome",
    [winner, "DISPUTE_WIN", 10, f"dispute:{dispute_id}"],
)
```

### As a consumer contract

```python
score = gl.call(ledger_address, "get_score", [counterparty])
if score["score"] < 30:
    raise Exception("Counterparty reputation too low.")
```

---

## Design notes

- **Registry pattern.** State keyed by address and event id. One deployment
  serves unlimited sources and subjects.
- **Access control.** Only the owner can register sources. Only registered
  sources can write outcomes. Revocation is immediate.
- **Auditability.** Every event carries a `context_hash` linking back to the
  originating case, so consumers can trace the raw inputs behind any score.
- **Consensus-safe.** State changes only after GenLayer consensus returns.
  Matches the pattern used by Agent Dispute Court.
- **No funds held.** The ledger records reputation; enforcement is left to
  consumer contracts.

---

## Test flow (verified on Studio)

1. Deploy contract.
2. `get_counts()` returns `{sources: 0, events: 0, half_life: 15552000}`.
3. Owner calls `register_source(source_b, "Test Court", 50)` → FINALIZED.
4. `get_sources()` returns the source with weight 50.
5. `source_b` calls `record_outcome(subject, "DISPUTE_WIN", 10, "dispute:1")`
   → FINALIZED, returns event id `0`.
6. `get_score(subject)` returns `{score: 5, raw_scaled: 5000, events: 1}`.

All three transactions on the deployed contract show FINALIZED status with
accepted validator consensus.

---

## Known limitations

- **Timestamp placeholder.** `_now()` currently returns `0` because
  GenLayer's deterministic time API is not yet finalized. Events carry a
  placeholder timestamp; decay is not yet enforced. Scores today are
  cumulative, not time-weighted.
- **No enforcement.** The contract records rulings but does not act on
  them. Enforcement (access gating, collateral, payouts) is up to
  consumer contracts.
- **Sybil resistance depends on source trust.** A malicious registered
  source can inflate or deflate scores until the owner revokes it.
  Governance of the source list is out of scope for V01.

---

## Roadmap

- **V02:** Deterministic timestamp + working exponential decay.
- **V03:** Per-source decay curves and per-kind weights.
- **Project submission:** Frontend dashboard, integration with Agent
  Dispute Court, AI Freelance Escrow, and News Fact Checker.

---

## Repository layout

```
Reputation-ledger/
├── README.md
└── reputation_ledgerV01.py
```

---

## License

MIT