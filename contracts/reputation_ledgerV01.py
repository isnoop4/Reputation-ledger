# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

from genlayer import *
import json


KINDS = (
    "DISPUTE_WIN",
    "DISPUTE_LOSS",
    "ESCROW_COMPLETED",
    "ESCROW_FAILED",
    "VERIFICATION_PASSED",
    "VERIFICATION_FAILED",
)

HALF_LIFE = 180 * 24 * 60 * 60
SCALE = 1000
MAX_DELTA = 100 * SCALE


class ReputationLedger(gl.Contract):
    owner: Address

    source_weight: TreeMap[str, u256]
    source_label: TreeMap[str, str]
    sources: DynArray[str]

    raw_score: TreeMap[str, i256]
    event_count: TreeMap[str, u256]
    events: TreeMap[u256, str]

    next_event_id: u256
    half_life: u256

    def __init__(self) -> None:
        self.owner = gl.message.sender_address
        self.next_event_id = u256(0)
        self.half_life = u256(HALF_LIFE)

    def _norm(self, address: str) -> str:
        if not isinstance(address, str):
            raise Exception("Address must be a string.")

        value = address.strip()

        if len(value) != 42 or not value.startswith("0x"):
            raise Exception("Invalid address.")

        hex_part = value[2:]

        if not all(c in "0123456789abcdefABCDEF" for c in hex_part):
            raise Exception("Invalid address.")

        return value.lower()

    def _now(self) -> u256:
        return u256(0)

    def _is_owner(self) -> bool:
        return gl.message.sender_address == self.owner

    @gl.public.write
    def register_source(
        self,
        source: str,
        label: str,
        weight: int,
    ) -> None:
        if not self._is_owner():
            raise Exception("Only the owner can register sources.")

        key = self._norm(source)

        if weight < 0 or weight > 100:
            raise Exception("Weight must be 0-100.")

        lbl = (label or "").strip()

        if not lbl:
            raise Exception("Label cannot be empty.")

        if key not in self.source_weight:
            self.sources.append(key)

        self.source_weight[key] = u256(weight)
        self.source_label[key] = lbl

    @gl.public.write
    def update_weight(self, source: str, weight: int) -> None:
        if not self._is_owner():
            raise Exception("Only the owner can update weights.")

        key = self._norm(source)

        if key not in self.source_weight:
            raise Exception("Source not registered.")

        if weight < 0 or weight > 100:
            raise Exception("Weight must be 0-100.")

        self.source_weight[key] = u256(weight)

    @gl.public.write
    def revoke_source(self, source: str) -> None:
        if not self._is_owner():
            raise Exception("Only the owner can revoke sources.")

        key = self._norm(source)

        if key not in self.source_weight:
            raise Exception("Source not registered.")

        self.source_weight[key] = u256(0)
        self.source_label[key] = "[revoked]"

    @gl.public.write
    def set_half_life(self, seconds: int) -> None:
        if not self._is_owner():
            raise Exception("Only the owner can set half-life.")

        if seconds < 3600 or seconds > 10 * 365 * 24 * 3600:
            raise Exception("Half-life out of range.")

        self.half_life = u256(seconds)

    @gl.public.write
    def record_outcome(
        self,
        subject: str,
        kind: str,
        delta: int,
        context_hash: str,
    ) -> u256:
        sender = self._norm(str(gl.message.sender_address))

        if sender not in self.source_weight:
            raise Exception("Caller is not a registered source.")

        weight = int(self.source_weight[sender])

        if weight <= 0:
            raise Exception("Source has been revoked.")

        subj = self._norm(subject)
        event_kind = (kind or "").strip().upper()

        if event_kind not in KINDS:
            raise Exception("Unknown kind.")

        if not isinstance(delta, int):
            raise Exception("Delta must be an integer.")

        if delta < -100 or delta > 100:
            raise Exception("Delta must be -100..100.")

        ctx = (context_hash or "").strip()

        if not ctx:
            raise Exception("context_hash required.")

        effective = (delta * weight * SCALE) // 100

        if effective > MAX_DELTA:
            effective = MAX_DELTA

        if effective < -MAX_DELTA:
            effective = -MAX_DELTA

        event_id = self.next_event_id
        self.next_event_id = event_id + u256(1)

        event = {
            "id": int(event_id),
            "source": sender,
            "subject": subj,
            "kind": event_kind,
            "delta": delta,
            "weight": weight,
            "effective": effective,
            "context_hash": ctx,
            "timestamp": int(self._now()),
        }

        self.events[event_id] = json.dumps(
            event,
            separators=(",", ":"),
        )

        previous = int(
            self.raw_score.get(subj, i256(0))
        )

        self.raw_score[subj] = i256(previous + effective)

        self.event_count[subj] = (
            self.event_count.get(subj, u256(0)) + u256(1)
        )

        return event_id

    @gl.public.view
    def get_counts(self) -> dict:
        return {
            "sources": len(self.sources),
            "events": int(self.next_event_id),
            "half_life": int(self.half_life),
        }

    @gl.public.view
    def get_source(self, source: str) -> dict:
        key = self._norm(source)

        if key not in self.source_weight:
            return {"registered": False}

        weight = int(
            self.source_weight.get(key, u256(0))
        )

        return {
            "registered": True,
            "address": key,
            "label": self.source_label.get(key, ""),
            "weight": weight,
            "revoked": weight <= 0,
        }

    @gl.public.view
    def get_sources(self) -> list:
        result = []

        for source in self.sources:
            weight = int(
                self.source_weight.get(source, u256(0))
            )

            result.append({
                "address": source,
                "label": self.source_label.get(source, ""),
                "weight": weight,
                "revoked": weight <= 0,
            })

        return result

    @gl.public.view
    def get_event(self, event_id: int) -> dict:
        if event_id < 0:
            raise Exception("Invalid event ID.")

        key = u256(event_id)

        if key not in self.events:
            raise Exception("Event not found.")

        return json.loads(self.events[key])

    @gl.public.view
    def get_raw_score(self, subject: str) -> int:
        key = self._norm(subject)

        return int(
            self.raw_score.get(key, i256(0))
        )

    @gl.public.view
    def get_score(self, subject: str) -> dict:
        key = self._norm(subject)

        raw = int(
            self.raw_score.get(key, i256(0))
        )

        count = int(
            self.event_count.get(key, u256(0))
        )

        return {
            "address": key,
            "score": raw // SCALE,
            "raw_scaled": raw,
            "events": count,
            "half_life": int(self.half_life),
        }
