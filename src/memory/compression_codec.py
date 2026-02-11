from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.memory.lexicon import CompressionLexicon


@dataclass(frozen=True, slots=True)
class CompressionStepResult:
    run_id: str
    step: str
    input_count: int
    output_count: int
    lossless: bool
    roundtrip_ok: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "step": self.step,
            "input_count": self.input_count,
            "output_count": self.output_count,
            "lossless": self.lossless,
            "roundtrip_ok": self.roundtrip_ok,
        }


class CompressionCodec:
    def __init__(self, lexicon: CompressionLexicon | None = None) -> None:
        self.lexicon = lexicon or CompressionLexicon()

    @staticmethod
    def _dedup_segments(lines: list[str]) -> list[dict[str, Any]]:
        if not lines:
            return []
        segments: list[dict[str, Any]] = []
        current_line = lines[0]
        current_count = 1
        for line in lines[1:]:
            if line == current_line:
                current_count += 1
                continue
            segments.append({"line": current_line, "count": current_count})
            current_line = line
            current_count = 1
        segments.append({"line": current_line, "count": current_count})
        return segments

    @staticmethod
    def _aggregate_keys(lines: list[str]) -> dict[str, int]:
        counts: dict[str, int] = {}
        for line in lines:
            token = line.split(" ", 1)[0] if " " in line else line
            counts[token] = counts.get(token, 0) + 1
        return counts

    def compress(self, run_id: str, raw_lines: list[str]) -> dict[str, Any]:
        segments = self._dedup_segments(raw_lines)
        dedup_lines = [item["line"] for item in segments]
        aggregate_counts = self._aggregate_keys(dedup_lines)
        summary_lines = [f"{key} x {count}" for key, count in sorted(aggregate_counts.items())]
        semantic_lines = [self.lexicon.encode_line(line) for line in summary_lines]
        decoded_summary = [self.lexicon.decode_line(line) for line in semantic_lines]
        semantic_roundtrip_ok = decoded_summary == summary_lines
        raw_roundtrip_ok = self.decompress({"dedup_segments": segments}) == raw_lines

        steps = [
            CompressionStepResult(
                run_id=run_id,
                step="dedup",
                input_count=len(raw_lines),
                output_count=len(dedup_lines),
                lossless=True,
                roundtrip_ok=raw_roundtrip_ok,
            ),
            CompressionStepResult(
                run_id=run_id,
                step="aggregate",
                input_count=len(dedup_lines),
                output_count=len(aggregate_counts),
                lossless=True,
                roundtrip_ok=raw_roundtrip_ok,
            ),
            CompressionStepResult(
                run_id=run_id,
                step="summary",
                input_count=len(aggregate_counts),
                output_count=len(summary_lines),
                lossless=True,
                roundtrip_ok=raw_roundtrip_ok,
            ),
            CompressionStepResult(
                run_id=run_id,
                step="semantic",
                input_count=len(summary_lines),
                output_count=len(semantic_lines),
                lossless=True,
                roundtrip_ok=semantic_roundtrip_ok and raw_roundtrip_ok,
            ),
        ]

        payload: dict[str, Any] = self.lexicon.bundle()
        payload["run_id"] = run_id
        payload["dedup_segments"] = segments
        payload["dedup_lines"] = dedup_lines
        payload["aggregate_counts"] = aggregate_counts
        payload["summary_lines"] = summary_lines
        payload["semantic_lines"] = semantic_lines
        payload["step_results"] = [step.to_dict() for step in steps]
        return payload

    @staticmethod
    def decompress(payload: dict[str, Any]) -> list[str]:
        output: list[str] = []
        for item in payload.get("dedup_segments", []):
            line = str(item.get("line", ""))
            count = int(item.get("count", 0))
            if count <= 0:
                continue
            output.extend([line] * count)
        return output
