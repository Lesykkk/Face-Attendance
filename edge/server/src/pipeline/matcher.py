"""
Matcher — cosine similarity against known student embeddings.
CooldownFilter — prevents re-reporting the same person/session within cooldown window.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class PersonEmbeddings:
    person_id: int
    embeddings: list[np.ndarray]  # list of 128D normalized vectors


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Both vectors are expected to be L2-normalized → dot product = cosine similarity."""
    return float(np.dot(a, b))


class Matcher:
    def __init__(self, threshold: float) -> None:
        self._threshold = threshold

    def find_match(
        self, probe: np.ndarray, students: list[PersonEmbeddings]
    ) -> tuple[int, float] | None:
        """
        Compares probe embedding against all stored embeddings for all students.
        Returns (person_id, best_confidence) if best similarity > threshold, else None.
        """
        best_person_id: int | None = None
        best_score: float = -1.0

        for student in students:
            for ref_vec in student.embeddings:
                score = _cosine_similarity(probe, ref_vec)
                if score > best_score:
                    best_score = score
                    best_person_id = student.person_id

        logger.debug(
            f"[Matcher] Best score: {best_score:.4f} (threshold: {self._threshold}) "
            f"person_id={best_person_id} → {'MATCH' if best_score >= self._threshold else 'NO MATCH'}"
        )

        if best_score >= self._threshold and best_person_id is not None:
            return best_person_id, best_score

        return None


class CooldownFilter:
    def __init__(self, cooldown_minutes: int) -> None:
        self._cooldown = timedelta(minutes=cooldown_minutes)
        self._last_reported: dict[tuple[int, int], datetime] = {}

    def should_report(self, person_id: int, session_id: int) -> bool:
        key = (person_id, session_id)
        last = self._last_reported.get(key)
        if last is None:
            return True
        return datetime.now(timezone.utc) - last >= self._cooldown

    def mark_reported(self, person_id: int, session_id: int) -> None:
        self._last_reported[(person_id, session_id)] = datetime.now(timezone.utc)
