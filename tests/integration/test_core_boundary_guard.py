from __future__ import annotations

import unittest

from src.core.boundary_guard import CoreBoundaryGuard
from src.core.boundary_guard import CoreBoundaryViolation


class CoreBoundaryGuardTest(unittest.TestCase):
    def test_boundary_guard_blocks_direct_core_state_write(self) -> None:
        guard = CoreBoundaryGuard()
        with self.assertRaises(CoreBoundaryViolation):
            guard.assert_write_allowed("core.state")

    def test_boundary_guard_blocks_direct_long_memory_write(self) -> None:
        guard = CoreBoundaryGuard()
        with self.assertRaises(CoreBoundaryViolation):
            guard.assert_write_allowed("memory.long")

    def test_boundary_guard_allows_event_bus_channel(self) -> None:
        guard = CoreBoundaryGuard()
        guard.assert_allowed_channel("event_bus")


if __name__ == "__main__":
    unittest.main()
