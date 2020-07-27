from ..helpers import meters_to_ly, meters_to_au, EveEntityNameResolver
from ..utils import NoSocketsTestCase


class TestHelpers(NoSocketsTestCase):
    def test_meters_to_ly(self):
        self.assertEqual(meters_to_ly(9_460_730_472_580_800), 1)
        self.assertEqual(meters_to_ly(0), 0)
        with self.assertRaises(ValueError):
            meters_to_ly("invalid")

    def test_meters_to_au(self):
        self.assertEqual(meters_to_au(149_597_870_691), 1)
        self.assertEqual(meters_to_au(0), 0)
        with self.assertRaises(ValueError):
            meters_to_au("invalid")


class TestEveEntityNameResolver(NoSocketsTestCase):
    def test_to_name(self):
        resolver = EveEntityNameResolver({1: "alpha", 2: "bravo", 3: "charlie"})
        self.assertEqual(resolver.to_name(2), "bravo")
        self.assertEqual(resolver.to_name(4), "")
