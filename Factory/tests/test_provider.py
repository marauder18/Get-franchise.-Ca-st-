from __future__ import annotations

import unittest

from provider import OfflineOnlyError, OfflineProvider


class ProviderTests(unittest.TestCase):
    def test_offline_provider_refuses_external_completion_without_leaking_input(self) -> None:
        with self.assertRaises(OfflineOnlyError) as raised:
            OfflineProvider().complete("secret-should-not-appear")
        self.assertNotIn("secret-should-not-appear", str(raised.exception))
        self.assertIn("offline-only", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
