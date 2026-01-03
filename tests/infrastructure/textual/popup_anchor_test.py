import pytest
from textual.geometry import Offset, Size
from simple_agent.infrastructure.textual.autocomplete.geometry import PopupAnchor

def test_popup_anchor_create_at_column_calculates_correctly():
    # Arrange
    cursor_offset = Offset(x=10, y=5)
    screen_size = Size(width=80, height=24)

    current_col = 20
    anchor_col = 15 # Word started 5 chars ago

    # Act
    # Logic: anchor_x = cursor_x - (current_col - anchor_col) = 10 - (20 - 15) = 5
    anchor = PopupAnchor.create_at_column(cursor_offset, screen_size, anchor_col, current_col)

    # Assert
    assert isinstance(anchor, PopupAnchor)
    assert anchor.cursor_offset.x == 5
    assert anchor.cursor_offset.y == 5
    assert anchor.screen_size == screen_size

def test_popup_anchor_create_at_column_clamps_negative_x():
    # Arrange
    cursor_offset = Offset(x=2, y=5)
    screen_size = Size(width=80, height=24)

    current_col = 20
    anchor_col = 15 # Word started 5 chars ago, but screen x is only 2

    # Act
    # Logic: anchor_x = 2 - (5) = -3 -> Clamped to 0
    anchor = PopupAnchor.create_at_column(cursor_offset, screen_size, anchor_col, current_col)

    # Assert
    assert anchor.cursor_offset.x == 0
