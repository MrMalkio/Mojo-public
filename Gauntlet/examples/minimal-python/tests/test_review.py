import json
from pathlib import Path
import unittest

from review import EditableReview, ReadonlyReview, ReviewStore

INPUTS = Path(__file__).resolve().parents[1] / "inputs"


def fixture(name):
    return json.loads((INPUTS / name).read_text())


class EditableReviewTests(unittest.TestCase):
    def setUp(self):
        self.store = ReviewStore(fixture("state-before.json"))
        self.surface = EditableReview(self.store)

    def test_render_shows_saved_review_state(self):
        self.assertEqual(self.surface.render("r1"), {"review_id": "r1", "reviewed": False, "can_toggle": True})

    def test_toggle_changes_only_reviewed_field(self):
        result = self.surface.toggle("r1")
        self.assertTrue(result["reviewed"])
        self.assertEqual(self.store.snapshot(), fixture("state-after-allowed.json"))

    def test_toggle_round_trip_preserves_records(self):
        self.surface.toggle("r1")
        self.surface.toggle("r1")
        self.assertEqual(self.store.snapshot(), fixture("state-before.json"))

    def test_missing_review_does_not_mutate_store(self):
        before = self.store.snapshot()
        with self.assertRaises(KeyError):
            self.surface.toggle("missing")
        self.assertEqual(self.store.snapshot(), before)


class ReadonlyReviewTests(unittest.TestCase):
    def setUp(self):
        self.store = ReviewStore(fixture("state-before.json"))
        self.surface = ReadonlyReview(self.store)

    def test_render_shows_saved_review_state(self):
        self.assertEqual(self.surface.render("r1"), {"review_id": "r1", "reviewed": False, "can_toggle": False})

    def test_toggle_refuses_without_mutation(self):
        before = self.store.snapshot()
        with self.assertRaises(PermissionError):
            self.surface.toggle("r1")
        self.assertEqual(self.store.snapshot(), before)


class StoreTests(unittest.TestCase):
    def test_rejects_non_boolean_without_mutation(self):
        store = ReviewStore(fixture("state-before.json"))
        before = store.snapshot()
        with self.assertRaises(ValueError):
            store.set_reviewed("r1", "true")
        self.assertEqual(store.snapshot(), before)

    def test_snapshot_is_isolated_from_caller_mutation(self):
        store = ReviewStore(fixture("state-before.json"))
        snapshot = store.snapshot()
        snapshot["r1"]["title"] = "changed outside store"
        self.assertEqual(store.snapshot(), fixture("state-before.json"))


if __name__ == "__main__":
    unittest.main()
