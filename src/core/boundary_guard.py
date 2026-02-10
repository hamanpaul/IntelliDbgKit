from __future__ import annotations


class CoreBoundaryViolation(PermissionError):
    pass


class CoreBoundaryGuard:
    BLOCKED_PATHS = {
        "core.state",
        "memory.long",
    }

    ALLOWED_CHANNELS = {
        "event_bus",
        "workflow_action",
        "evidence_input",
    }

    def assert_allowed_channel(self, channel: str) -> None:
        if channel not in self.ALLOWED_CHANNELS:
            raise CoreBoundaryViolation(f"channel not allowed: {channel}")

    def assert_write_allowed(self, target_path: str) -> None:
        if target_path in self.BLOCKED_PATHS:
            raise CoreBoundaryViolation(f"direct write blocked: {target_path}")
