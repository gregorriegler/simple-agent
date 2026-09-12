from enum import Enum


class OnComplete(str, Enum):
    HUMAN_REVIEW = "human_review"
    CLOSE = "close"

    def __str__(self) -> str:
        return self.value
