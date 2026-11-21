from __future__ import annotations

"""cli.py 单元测试：退出码、错误输出与文件生成。"""

import contextlib
import io
import os
import tempfile
import unittest
from typing import List, Optional, Tuple

from slidingpuzzle.cli import main


class CliTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmpdir: str = self._tmp.name
        self._old_cwd: str = os.getcwd()

    def tearDown(self) -> None:
        os.chdir(self._old_cwd)
        self._tmp.cleanup()

    def _run(self, argv: List[str], cwd: Optional[str] = None) -> Tuple[int, str, str]:
        """在指定目录运行 CLI，返回 (退出码, stdout, stderr)。"""
        stdout = io.StringIO()
        stderr = io.StringIO()
        os.chdir(cwd if cwd is not None else self.tmpdir)
        try:
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                code = main(argv)
        finally:
            os.chdir(self._old_cwd)
        return code, stdout.getvalue(), stderr.getvalue()

    def _path(self, name: str) -> str:
        return os.path.join(self.tmpdir, name)

    def test_default_output(self) -> None:
        code, out, err = self._run(["--seed", "1"])
        self.assertEqual(code, 0)
        self.assertEqual(err, "")
        self.assertTrue(os.path.isfile(self._path("slidingpuzzle.html")))
        self.assertIn("已生成 slidingpuzzle.html", out)
        self.assertIn("3×3", out)
        self.assertIn("步数下限", out)

    def test_explicit_output(self) -> None:
        target = self._path("board.html")
        code, out, _ = self._run(["-o", target, "--seed", "2"])
        self.assertEqual(code, 0)
        self.assertTrue(os.path.isfile(target))
        self.assertIn("已生成", out)
        with open(target, "r", encoding="utf-8") as handle:
            content = handle.read()
        self.assertIn("<!DOCTYPE html>", content)
        self.assertIn("数字华容道", content)

    def test_playable_creates_two_files(self) -> None:
        target = self._path("puzzle.html")
        code, out, _ = self._run(
            ["-o", target, "--size", "3", "--seed", "9", "--playable"]
        )
        self.assertEqual(code, 0)
        play_path = self._path("puzzle-play.html")
        self.assertTrue(os.path.isfile(target))
        self.assertTrue(os.path.isfile(play_path))
        self.assertIn("puzzle-play.html", out)
        with open(play_path, "r", encoding="utf-8") as handle:
            playable = handle.read()
        self.assertIn("步数", playable)
        self.assertNotIn("http", playable.lower())

    def test_playable_without_extension(self) -> None:
        target = self._path("puzzle")
        code, _, _ = self._run(["-o", target, "--seed", "4", "--playable"])
        self.assertEqual(code, 0)
        self.assertTrue(os.path.isfile(self._path("puzzle-play.html")))

    def test_size_4(self) -> None:
        code, out, _ = self._run(["-o", self._path("s4.html"), "--size", "4"])
        self.assertEqual(code, 0)
        self.assertIn("4×4", out)

    def test_size_5(self) -> None:
        code, out, _ = self._run(["-o", self._path("s5.html"), "--size", "5"])
        self.assertEqual(code, 0)
        self.assertIn("5×5", out)

    def test_invalid_size(self) -> None:
        code, _, err = self._run(["-o", self._path("bad.html"), "--size", "6"])
        self.assertEqual(code, 2)
        self.assertIn("错误", err)
        self.assertIn("边长", err)
        self.assertFalse(os.path.exists(self._path("bad.html")))

    def test_non_numeric_size(self) -> None:
        code, _, err = self._run(["--size", "abc"])
        self.assertEqual(code, 2)
        self.assertIn("边长", err)

    def test_invalid_seed(self) -> None:
        code, _, err = self._run(["--seed", "abc"])
        self.assertEqual(code, 2)
        self.assertIn("随机种子", err)

    def test_empty_title(self) -> None:
        code, _, err = self._run(["--title", "   "])
        self.assertEqual(code, 2)
        self.assertIn("标题", err)

    def test_empty_output(self) -> None:
        code, _, err = self._run(["-o", "   "])
        self.assertEqual(code, 2)
        self.assertIn("输出路径", err)

    def test_write_failure_returns_one(self) -> None:
        code, _, err = self._run(["-o", self.tmpdir, "--seed", "1"])
        self.assertEqual(code, 1)
        self.assertIn("无法写入", err)

    def test_creates_parent_directories(self) -> None:
        target = os.path.join(self.tmpdir, "nested", "deep", "board.html")
        code, _, _ = self._run(["-o", target, "--seed", "3"])
        self.assertEqual(code, 0)
        self.assertTrue(os.path.isfile(target))

    def test_same_seed_reproducible(self) -> None:
        first = self._path("a.html")
        second = self._path("b.html")
        self._run(["-o", first, "--seed", "42"])
        self._run(["-o", second, "--seed", "42"])
        with open(first, "r", encoding="utf-8") as handle:
            first_text = handle.read()
        with open(second, "r", encoding="utf-8") as handle:
            second_text = handle.read()
        self.assertEqual(first_text, second_text)

    def test_different_seed_differs(self) -> None:
        first = self._path("a.html")
        second = self._path("b.html")
        self._run(["-o", first, "--seed", "1"])
        self._run(["-o", second, "--seed", "2"])
        with open(first, "r", encoding="utf-8") as handle:
            first_text = handle.read()
        with open(second, "r", encoding="utf-8") as handle:
            second_text = handle.read()
        self.assertNotEqual(first_text, second_text)

    def test_custom_title_rendered(self) -> None:
        target = self._path("titled.html")
        code, _, _ = self._run(["-o", target, "--title", "数学角"])
        self.assertEqual(code, 0)
        with open(target, "r", encoding="utf-8") as handle:
            self.assertIn("数学角", handle.read())

    def test_unknown_argument(self) -> None:
        code, _, err = self._run(["--nope"])
        self.assertEqual(code, 2)
        self.assertIn("错误", err)

    def test_help_returns_zero(self) -> None:
        code, out, _ = self._run(["-h"])
        self.assertEqual(code, 0)
        self.assertIn("usage", out)

    def test_missing_output_value(self) -> None:
        code, _, err = self._run(["-o"])
        self.assertEqual(code, 2)
        self.assertIn("错误", err)


if __name__ == "__main__":
    unittest.main()
