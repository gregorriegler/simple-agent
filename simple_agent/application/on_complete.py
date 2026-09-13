from enum import Enum


class OnComplete(str, Enum):
    HUMAN_REVIEW = "human_review"
    STOP_AND_WAIT = "stop_and_wait"
    CLOSE = "close"

    def __str__(self) -> str:
        return self.value
