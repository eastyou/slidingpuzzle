from __future__ import annotations

"""render.py 单元测试：打印页结构、方块卡片、离线可玩页与转义安全。"""

import unittest

from slidingpuzzle.model import Board, PuzzleError, shuffle
from slidingpuzzle.render import (
    render_document,
    render_playable,
    render_printable,
)


class PrintableRenderTest(unittest.TestCase):
    def setUp(self) -> None:
        self.board: Board = shuffle(3, seed=4)
        self.html: str = render_printable(self.board, 3, "数字华容道")

    def test_doctype_and_lang(self) -> None:
        self.assertTrue(self.html.startswith("<!DOCTYPE html>"))
        self.assertIn('<html lang="zh-CN">', self.html)

    def test_two_pages(self) -> None:
        self.assertEqual(self.html.count('<section class="page">'), 2)

    def test_a4_css(self) -> None:
        self.assertIn("@page { size: A4; margin: 0 }", self.html)
        self.assertIn("width: 210mm", self.html)
        self.assertIn("min-height: 297mm", self.html)

    def test_cell_count(self) -> None:
        self.assertEqual(self.html.count('class="cell'), 9)

    def test_exactly_one_blank_cell(self) -> None:
        self.assertEqual(self.html.count('class="cell blank"'), 1)
        self.assertIn('<div class="cell blank"></div>', self.html)

    def test_all_tile_numbers_printed(self) -> None:
        for value in range(1, 9):
            with self.subTest(value=value):
                self.assertIn(f'<div class="cell">{value}</div>', self.html)

    def test_coordinate_labels(self) -> None:
        self.assertEqual(self.html.count('class="col-label"'), 3)
        self.assertEqual(self.html.count('class="row-label"'), 3)

    def test_target_description(self) -> None:
        self.assertIn("目标布局", self.html)
        self.assertIn("1 到 8", self.html)

    def test_card_count(self) -> None:
        self.assertEqual(self.html.count('class="card"'), 8)

    def test_cut_line_hint(self) -> None:
        self.assertIn("剪切线", self.html)
        self.assertIn("dashed", self.html)

    def test_cards_follow_board_order(self) -> None:
        first_value = next(value for value in self.board if value != 0)
        first_card = self.html.index('class="card"')
        first_number = self.html.index(f'>{first_value}</span>')
        self.assertLess(first_card, first_number)

    def test_title_is_escaped(self) -> None:
        html = render_printable(self.board, 3, "<数字&华容道>")
        self.assertIn("&lt;数字&amp;华容道&gt;", html)
        self.assertNotIn("<数字&华容道>", html)

    def test_size_4_cells_and_cards(self) -> None:
        board = shuffle(4, seed=2)
        html = render_printable(board, 4)
        self.assertEqual(html.count('class="cell'), 16)
        self.assertEqual(html.count('class="card"'), 15)

    def test_invalid_board(self) -> None:
        with self.assertRaises(PuzzleError):
            render_printable((1, 2, 3), 3)

    def test_empty_title(self) -> None:
        with self.assertRaises(PuzzleError):
            render_printable(self.board, 3, "   ")

    def test_too_long_title(self) -> None:
        with self.assertRaises(PuzzleError):
            render_printable(self.board, 3, "长" * 101)


class PlayableRenderTest(unittest.TestCase):
    def setUp(self) -> None:
        self.board: Board = shuffle(3, seed=11)
        self.html: str = render_playable(self.board, 3)

    def test_controls_and_stats(self) -> None:
        self.assertIn("步数", self.html)
        self.assertIn("计时", self.html)
        self.assertIn("重开", self.html)
        self.assertIn("打乱", self.html)

    def test_no_external_resources(self) -> None:
        lowered = self.html.lower()
        self.assertNotIn("http", lowered)
        self.assertNotIn("<link", lowered)
        self.assertNotIn(" src=", lowered)
        self.assertNotIn("href=", lowered)

    def test_board_data_injected(self) -> None:
        self.assertIn('"size":3', self.html)
        self.assertIn('"board":[', self.html)
        self.assertIn('"goal":[1,2,3,4,5,6,7,8,0]', self.html)

    def test_size_4_data(self) -> None:
        html = render_playable(shuffle(4, seed=6), 4)
        self.assertIn('"size":4', html)
        self.assertIn('"goal":[1,2,3', html)

    def test_script_injection_escaped(self) -> None:
        html = render_playable(self.board, 3, "</script><script>alert(1)</script>")
        self.assertEqual(html.count("</script>"), 1)
        self.assertIn("<\\/script>", html)
        self.assertNotIn("</script><script>alert(1)", html)
        self.assertIn("&lt;/script&gt;", html)

    def test_steps_hint(self) -> None:
        self.assertIn("参考步数下限", self.html)

    def test_invalid_board(self) -> None:
        with self.assertRaises(PuzzleError):
            render_playable((1, 2, 3), 3)

    def test_empty_title(self) -> None:
        with self.assertRaises(PuzzleError):
            render_playable(self.board, 3, "")


class RenderDocumentTest(unittest.TestCase):
    def setUp(self) -> None:
        self.board: Board = shuffle(3, seed=8)

    def test_printable_document(self) -> None:
        html = render_document(self.board, 3, False)
        self.assertIn("目标布局", html)
        self.assertNotIn("步数：", html)

    def test_playable_document(self) -> None:
        html = render_document(self.board, 3, True)
        self.assertIn("步数：", html)
        self.assertNotIn("目标布局", html)

    def test_playable_must_be_bool(self) -> None:
        with self.assertRaises(PuzzleError):
            render_document(self.board, 3, 1)  # type: ignore[arg-type]

    def test_invalid_board(self) -> None:
        with self.assertRaises(PuzzleError):
            render_document((1, 2, 3), 3, True)


if __name__ == "__main__":
    unittest.main()
