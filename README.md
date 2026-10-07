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
- **File:** `contracts/reputation_ledgerV01.py`

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
