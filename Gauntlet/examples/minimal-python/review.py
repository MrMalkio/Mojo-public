"""Synthetic review capability with editable and read-only implementations."""
from copy import deepcopy


class ReviewStore:
    def __init__(self, records):
        self._records = deepcopy(records)

    # @coord:review.store.snapshot
    def snapshot(self):
        return deepcopy(self._records)

    # @coord:review.store.set-reviewed
    def set_reviewed(self, review_id, value):
        if not isinstance(value, bool):
            raise ValueError("reviewed must be a boolean")
        self._records[review_id]["reviewed"] = value


class EditableReview:
    def __init__(self, store):
        self.store = store

    # @coord:review.editable.render
    def render(self, review_id):
        record = self.store.snapshot()[review_id]
        return {"review_id": review_id, "reviewed": record["reviewed"], "can_toggle": True}

    # @coord:review.editable.toggle
    def toggle(self, review_id):
        before = self.store.snapshot()[review_id]["reviewed"]
        self.store.set_reviewed(review_id, not before)
        return self.render(review_id)


class ReadonlyReview:
    def __init__(self, store):
        self.store = store

    # @coord:review.readonly.render
    def render(self, review_id):
        record = self.store.snapshot()[review_id]
        return {"review_id": review_id, "reviewed": record["reviewed"], "can_toggle": False}

    # @coord:review.readonly.toggle
    def toggle(self, review_id):
        raise PermissionError("This review surface is read-only")
