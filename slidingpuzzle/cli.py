from __future__ import annotations

"""命令行入口：生成可打印棋盘，可选同时生成离线可玩 HTML。"""

import argparse
import os
import sys
from typing import Optional, Sequence

from .model import PuzzleError, manhattan, parse_size, shuffle
from .render import render_document

DEFAULT_OUTPUT: str = "slidingpuzzle.html"
DEFAULT_SIZE: str = "3"
DEFAULT_TITLE: str = "数字华容道"


class _WriteError(Exception):
    """内部异常：文件写入失败，CLI 据此返回退出码 1。"""


class _ArgumentParser(argparse.ArgumentParser):
    """参数错误时抛出中文异常，而不是让 argparse 直接退出。"""

    def error(self, message: str) -> None:
        raise PuzzleError("参数错误：无法解析命令行参数，请使用 -h 查看帮助")


def _validate_output(raw: str) -> str:
    """校验输出路径。"""
    if not isinstance(raw, str):
        raise PuzzleError(f"输出路径必须是字符串，收到：{type(raw).__name__}")
    path = raw.strip()
    if path == "":
        raise PuzzleError("输出路径不能为空")
    if "\x00" in path:
        raise PuzzleError("输出路径不能包含空字符")
    if len(path) > 4096:
        raise PuzzleError("输出路径过长（超过 4096 个字符）")
    return path


def _validate_title(raw: str) -> str:
    """校验标题文本。"""
    if not isinstance(raw, str):
        raise PuzzleError(f"标题必须是字符串，收到：{type(raw).__name__}")
    title = raw.strip()
    if title == "":
        raise PuzzleError("标题不能为空")
    if len(title) > 100:
        raise PuzzleError(f"标题长度不能超过 100 个字符，收到：{len(title)}")
    for char in title:
        if ord(char) < 32 or ord(char) == 127:
            raise PuzzleError("标题不能包含控制字符")
    return title


def _parse_seed(raw: Optional[str]) -> Optional[int]:
    """校验并解析随机种子。"""
    if raw is None:
        return None
    if not isinstance(raw, str):
        raise PuzzleError(f"随机种子必须是字符串，收到：{type(raw).__name__}")
    text = raw.strip()
    if text == "":
        raise PuzzleError("随机种子不能为空")
    body = text[1:] if text[0] in "+-" else text
    if not body.isdigit():
        raise PuzzleError(f"随机种子必须是整数，收到：{raw!r}")
    value = int(text)
    if value < -(2 ** 63) or value > 2 ** 63 - 1:
        raise PuzzleError("随机种子超出 64 位整数范围")
    return value


def _playable_path(output: str) -> str:
    """按 -play 后缀推导可玩版输出路径。"""
    root, ext = os.path.splitext(output)
    if ext:
        return f"{root}-play{ext}"
    return f"{output}-play.html"


def _write_text(path: str, content: str) -> None:
    """写入 UTF-8 文本，失败时转换为 _WriteError。"""
    parent = os.path.dirname(os.path.abspath(path))
    try:
        os.makedirs(parent, exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
    except OSError as exc:
        reason = exc.strerror if exc.strerror else str(exc)
        raise _WriteError(f"无法写入 {path}：{reason}") from exc


def _build_parser() -> argparse.ArgumentParser:
    """构建命令行参数解析器。"""
    parser = _ArgumentParser(
        prog="slidingpuzzle",
        description="生成数字华容道：可打印 A4 棋盘，或单文件离线可玩 HTML。",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=DEFAULT_OUTPUT,
        help=f"输出 HTML 路径（默认：{DEFAULT_OUTPUT}）",
    )
    parser.add_argument(
        "--size",
        default=DEFAULT_SIZE,
        help="棋盘边长，支持 3 / 4 / 5（默认：3）",
    )
    parser.add_argument(
        "--seed",
        default=None,
        help="随机种子，用于复现同一套棋盘",
    )
    parser.add_argument(
        "--playable",
        action="store_true",
        help="额外生成可离线游玩的单文件 HTML（文件名自动加 -play 后缀）",
    )
    parser.add_argument(
        "--title",
        default=DEFAULT_TITLE,
        help=f"页面标题（默认：{DEFAULT_TITLE}）",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    """命令行主函数，返回进程退出码：成功 0、写文件失败 1、参数非法 2。"""
    parser = _build_parser()
    try:
        args = parser.parse_args(list(argv) if argv is not None else None)
    except PuzzleError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else 2

    try:
        size = parse_size(args.size)
        seed = _parse_seed(args.seed)
        title = _validate_title(args.title)
        output = _validate_output(args.output)
        board = shuffle(size, seed)
        lower_bound = manhattan(board, size)
        _write_text(output, render_document(board, size, False, title))
        print(f"已生成 {output}（{size}×{size}，步数下限 {lower_bound}）")
        if args.playable:
            play_path = _playable_path(output)
            _write_text(play_path, render_document(board, size, True, title))
            print(f"已生成 {play_path}（{size}×{size}，步数下限 {lower_bound}）")
        return 0
    except PuzzleError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2
    except _WriteError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1
