from textual.geometry import Offset

from simple_agent.infrastructure.textual.smart_input.autocomplete.popup import (
    CompletionSeed,
)


def test_completion_seed_initialization():
    # Arrange
    location = Offset(x=10, y=5)
    text = "hello"

    # Act
    seed = CompletionSeed(location, text)

    # Assert
    assert seed.location == location
    assert seed.text == text


def test_completion_seed_width_calculation():
    # Arrange
    location = Offset(x=10, y=5)
    text = "hello"
    seed = CompletionSeed(location, text)

    # Act & Assert
    assert seed.width == 5


def test_completion_seed_width_empty():
    # Arrange
    seed = CompletionSeed(Offset(0, 0), "")

    # Act & Assert
    assert seed.width == 0
