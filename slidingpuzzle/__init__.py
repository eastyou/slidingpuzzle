from __future__ import annotations

"""slidingpuzzle：数字华容道核心能力的公开接口。"""

from .model import (
    Board,
    PuzzleError,
    apply_move,
    goal_board,
    inversions,
    is_solvable,
    manhattan,
    moves,
    parse_size,
    shuffle,
    validate_board,
)
from .render import render_document, render_playable, render_printable

__version__ = "0.1.0"

__all__ = [
    "Board",
    "PuzzleError",
    "apply_move",
    "goal_board",
    "inversions",
    "is_solvable",
    "manhattan",
    "moves",
    "parse_size",
    "shuffle",
    "validate_board",
    "render_document",
    "render_playable",
    "render_printable",
]
