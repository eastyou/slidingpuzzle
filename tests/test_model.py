from __future__ import annotations

"""model.py 单元测试：校验、可解性、洗牌、距离与移动。"""

import unittest

from slidingpuzzle.model import (
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

GOAL3: Board = (1, 2, 3, 4, 5, 6, 7, 8, 0)
GOAL4: Board = tuple(range(1, 16)) + (0,)


class GoalBoardTest(unittest.TestCase):
    def test_goal_board_3(self) -> None:
        self.assertEqual(goal_board(3), GOAL3)

    def test_goal_board_4(self) -> None:
        board = goal_board(4)
        self.assertEqual(len(board), 16)
        self.assertEqual(board[0], 1)
        self.assertEqual(board[-1], 0)
        self.assertEqual(set(board), set(range(16)))

    def test_goal_board_5(self) -> None:
        board = goal_board(5)
        self.assertEqual(len(board), 25)
        self.assertEqual(board[-1], 0)

    def test_goal_board_invalid_size(self) -> None:
        for size in (1, 0, -3, 9):
            with self.subTest(size=size):
                with self.assertRaises(PuzzleError):
                    goal_board(size)

    def test_goal_board_bool_size(self) -> None:
        with self.assertRaises(PuzzleError):
            goal_board(True)


class ValidateBoardTest(unittest.TestCase):
    def test_valid_goal(self) -> None:
        self.assertIsNone(validate_board(GOAL3, 3))

    def test_accepts_list(self) -> None:
        self.assertIsNone(validate_board(list(GOAL4), 4))

    def test_wrong_length(self) -> None:
        with self.assertRaises(PuzzleError):
            validate_board((1, 2, 3, 0), 3)

    def test_duplicate_number(self) -> None:
        with self.assertRaises(PuzzleError):
            validate_board((1, 2, 3, 4, 5, 6, 7, 7, 0), 3)

    def test_missing_number(self) -> None:
        with self.assertRaises(PuzzleError):
            validate_board((1, 2, 3, 4, 5, 6, 7, 8, 8), 3)

    def test_out_of_range(self) -> None:
        with self.assertRaises(PuzzleError):
            validate_board((1, 2, 3, 4, 5, 6, 7, 8, 9), 3)

    def test_negative_number(self) -> None:
        with self.assertRaises(PuzzleError):
            validate_board((1, 2, 3, 4, 5, 6, 7, 8, -1), 3)

    def test_non_integer_value(self) -> None:
        with self.assertRaises(PuzzleError):
            validate_board((1, 2, 3, 4, 5, 6, 7, 8, 0.0), 3)  # type: ignore[arg-type]

    def test_bool_value(self) -> None:
        with self.assertRaises(PuzzleError):
            validate_board((1, 2, 3, 4, 5, 6, 7, 8, True), 3)  # type: ignore[arg-type]

    def test_non_sequence(self) -> None:
        with self.assertRaises(PuzzleError):
            validate_board("123456780", 3)  # type: ignore[arg-type]

    def test_invalid_size(self) -> None:
        with self.assertRaises(PuzzleError):
            validate_board(GOAL3, 4)

    def test_size_bool(self) -> None:
        with self.assertRaises(PuzzleError):
            validate_board(GOAL3, True)


class InversionsTest(unittest.TestCase):
    def test_goal_has_zero(self) -> None:
        self.assertEqual(inversions(GOAL3), 0)
        self.assertEqual(inversions(GOAL4), 0)

    def test_simple_pair(self) -> None:
        self.assertEqual(inversions((2, 1, 0)), 1)

    def test_three_descending(self) -> None:
        self.assertEqual(inversions((3, 1, 2, 0)), 2)

    def test_ignores_blank(self) -> None:
        self.assertEqual(inversions((0, 2, 1)), 1)
        self.assertEqual(inversions((2, 0, 1)), 1)

    def test_empty_board(self) -> None:
        with self.assertRaises(PuzzleError):
            inversions(())

    def test_non_integer(self) -> None:
        with self.assertRaises(PuzzleError):
            inversions((1, "2", 0))  # type: ignore[arg-type]

    def test_negative(self) -> None:
        with self.assertRaises(PuzzleError):
            inversions((1, -2, 0))


class SolvabilityTest(unittest.TestCase):
    def test_goal_3_solvable(self) -> None:
        self.assertTrue(is_solvable(GOAL3, 3))

    def test_goal_4_solvable(self) -> None:
        self.assertTrue(is_solvable(GOAL4, 4))

    def test_goal_5_solvable(self) -> None:
        self.assertTrue(is_solvable(goal_board(5), 5))

    def test_swap_adjacent_3_unsolvable(self) -> None:
        board: Board = (1, 2, 3, 4, 5, 6, 8, 7, 0)
        self.assertFalse(is_solvable(board, 3))

    def test_swap_14_15_4_unsolvable(self) -> None:
        board: Board = tuple(range(1, 14)) + (15, 14, 0)
        self.assertFalse(is_solvable(board, 4))

    def test_blank_moved_3_solvable(self) -> None:
        board: Board = (1, 2, 3, 4, 5, 6, 0, 7, 8)
        self.assertTrue(is_solvable(board, 3))

    def test_blank_moved_4_solvable(self) -> None:
        board = apply_move(GOAL4, 4, 11)
        self.assertTrue(is_solvable(board, 4))

    def test_one_move_from_goal_4_solvable(self) -> None:
        board = apply_move(GOAL4, 4, 14)
        self.assertTrue(is_solvable(board, 4))

    def test_invalid_board(self) -> None:
        with self.assertRaises(PuzzleError):
            is_solvable((1, 2, 3), 3)

    def test_every_single_swap_of_goal_3(self) -> None:
        values = list(GOAL3)
        for i in range(9):
            for j in range(i + 1, 9):
                candidate = values[:]
                candidate[i], candidate[j] = candidate[j], candidate[i]
                if candidate == values:
                    continue
                expected = inversions(tuple(candidate)) % 2 == 0
                with self.subTest(i=i, j=j):
                    self.assertEqual(is_solvable(tuple(candidate), 3), expected)


class ShuffleTest(unittest.TestCase):
    def test_size_3_solvable_and_not_goal(self) -> None:
        board = shuffle(3, seed=1)
        self.assertEqual(len(board), 9)
        self.assertNotEqual(board, GOAL3)
        self.assertTrue(is_solvable(board, 3))

    def test_size_4_solvable_and_not_goal(self) -> None:
        board = shuffle(4, seed=7)
        self.assertEqual(len(board), 16)
        self.assertNotEqual(board, GOAL4)
        self.assertTrue(is_solvable(board, 4))

    def test_size_5_solvable(self) -> None:
        board = shuffle(5, seed=3)
        self.assertTrue(is_solvable(board, 5))

    def test_same_seed_reproducible(self) -> None:
        self.assertEqual(shuffle(4, seed=2026), shuffle(4, seed=2026))

    def test_different_seed_differs(self) -> None:
        self.assertNotEqual(shuffle(3, seed=1), shuffle(3, seed=2))

    def test_seed_none_returns_board(self) -> None:
        board = shuffle(3)
        validate_board(board, 3)
        self.assertNotEqual(board, GOAL3)

    def test_many_seeds_all_solvable(self) -> None:
        for seed in range(40):
            board = shuffle(4, seed=seed)
            with self.subTest(seed=seed):
                self.assertTrue(is_solvable(board, 4))
                self.assertNotEqual(board, GOAL4)

    def test_invalid_size(self) -> None:
        with self.assertRaises(PuzzleError):
            shuffle(9)

    def test_invalid_seed_type(self) -> None:
        with self.assertRaises(PuzzleError):
            shuffle(3, seed=1.5)  # type: ignore[arg-type]

    def test_bool_seed_rejected(self) -> None:
        with self.assertRaises(PuzzleError):
            shuffle(3, seed=True)


class ManhattanTest(unittest.TestCase):
    def test_goal_3_zero(self) -> None:
        self.assertEqual(manhattan(GOAL3, 3), 0)

    def test_goal_4_zero(self) -> None:
        self.assertEqual(manhattan(GOAL4, 4), 0)

    def test_one_move_is_one(self) -> None:
        board = apply_move(GOAL3, 3, 7)
        self.assertEqual(manhattan(board, 3), 1)

    def test_swap_two_tiles(self) -> None:
        board: Board = (2, 1, 3, 4, 5, 6, 7, 8, 0)
        self.assertEqual(manhattan(board, 3), 2)

    def test_invalid_board(self) -> None:
        with self.assertRaises(PuzzleError):
            manhattan((1, 2, 3, 4, 5, 6, 7, 8, 8), 3)


class MovesTest(unittest.TestCase):
    def test_corner_blank_3(self) -> None:
        self.assertEqual(moves(GOAL3, 3), [(8, 5), (8, 7)])

    def test_center_blank_3_has_four(self) -> None:
        board: Board = (1, 2, 3, 4, 0, 5, 6, 7, 8)
        self.assertEqual(len(moves(board, 3)), 4)

    def test_corner_blank_4(self) -> None:
        self.assertEqual(moves(GOAL4, 4), [(15, 11), (15, 14)])

    def test_moves_are_applicable(self) -> None:
        board = shuffle(4, seed=5)
        for blank, target in moves(board, 4):
            with self.subTest(blank=blank, target=target):
                self.assertEqual(board[blank], 0)
                next_board = apply_move(board, 4, target)
                self.assertEqual(next_board[blank], board[target])

    def test_invalid_board(self) -> None:
        with self.assertRaises(PuzzleError):
            moves((0, 1, 2), 3)


class ApplyMoveTest(unittest.TestCase):
    def test_swap_with_blank(self) -> None:
        board = apply_move(GOAL3, 3, 5)
        self.assertEqual(board, (1, 2, 3, 4, 5, 0, 7, 8, 6))

    def test_round_trip(self) -> None:
        board = apply_move(GOAL3, 3, 5)
        self.assertEqual(apply_move(board, 3, 8), GOAL3)

    def test_non_adjacent(self) -> None:
        with self.assertRaises(PuzzleError):
            apply_move(GOAL3, 3, 0)

    def test_out_of_range(self) -> None:
        for index in (-1, 9):
            with self.subTest(index=index):
                with self.assertRaises(PuzzleError):
                    apply_move(GOAL3, 3, index)

    def test_blank_itself(self) -> None:
        with self.assertRaises(PuzzleError):
            apply_move(GOAL3, 3, 8)

    def test_non_integer_index(self) -> None:
        with self.assertRaises(PuzzleError):
            apply_move(GOAL3, 3, 5.0)  # type: ignore[arg-type]

    def test_invalid_board(self) -> None:
        with self.assertRaises(PuzzleError):
            apply_move((1, 2, 3), 3, 0)


class ParseSizeTest(unittest.TestCase):
    def test_allowed_values(self) -> None:
        self.assertEqual(parse_size("3"), 3)
        self.assertEqual(parse_size("4"), 4)
        self.assertEqual(parse_size("5"), 5)

    def test_strips_whitespace(self) -> None:
        self.assertEqual(parse_size("  4  "), 4)

    def test_unsupported_value(self) -> None:
        for raw in ("2", "6", "9", "0"):
            with self.subTest(raw=raw):
                with self.assertRaises(PuzzleError):
                    parse_size(raw)

    def test_non_numeric(self) -> None:
        for raw in ("abc", "3.0", "3a", "-3"):
            with self.subTest(raw=raw):
                with self.assertRaises(PuzzleError):
                    parse_size(raw)

    def test_empty(self) -> None:
        with self.assertRaises(PuzzleError):
            parse_size("   ")

    def test_non_string(self) -> None:
        with self.assertRaises(PuzzleError):
            parse_size(3)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
