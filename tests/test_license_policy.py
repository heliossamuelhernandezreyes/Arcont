import unittest

from tools.license_policy import classify, is_auto_ingestible, normalize_license_name


class LicensePolicyTests(unittest.TestCase):
    def test_cc0_is_green_and_auto_ingestible(self):
        policy = classify("Creative Commons CC0")
        self.assertIsNotNone(policy)
        self.assertEqual(policy.tier, "green")
        self.assertTrue(policy.portable_commercial_default)
        self.assertTrue(is_auto_ingestible("CC0"))

    def test_public_domain_is_green(self):
        policy = classify("Public Domain")
        self.assertIsNotNone(policy)
        self.assertEqual(policy.tier, "green")
        self.assertFalse(policy.attribution_required)

    def test_cc_by_is_conditional_not_auto_ingestible(self):
        policy = classify("CC-BY 3.0")
        self.assertIsNotNone(policy)
        self.assertEqual(policy.tier, "conditional")
        self.assertTrue(policy.attribution_required)
        self.assertFalse(is_auto_ingestible("CC-BY 3.0"))

    def test_share_alike_is_restricted(self):
        policy = classify("CC-BY-SA 4.0")
        self.assertIsNotNone(policy)
        self.assertEqual(policy.tier, "restricted")
        self.assertTrue(policy.share_alike)
        self.assertFalse(is_auto_ingestible("CC-BY-SA 4.0"))

    def test_gpl_is_restricted(self):
        self.assertEqual(classify("GPL 3.0").tier, "restricted")
        self.assertFalse(is_auto_ingestible("GPL 3.0"))

    def test_unknown_license_is_never_guessed(self):
        self.assertIsNone(normalize_license_name("Super Free No Rules License"))
        self.assertIsNone(classify("Super Free No Rules License"))
        self.assertFalse(is_auto_ingestible("Super Free No Rules License"))


if __name__ == "__main__":
    unittest.main()
