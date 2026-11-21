from __future__ import annotations

"""数字华容道核心模型：棋盘校验、可解性判定、可复现洗牌与曼哈顿距离。

棋盘使用一维元组表示，行优先排列，数字 0 表示空格。
例如 3×3 的目标布局为：(1, 2, 3, 4, 5, 6, 7, 8, 0)。
"""

import random
from typing import List, Optional, Tuple

Board = Tuple[int, ...]

# 核心模型支持的最小 / 最大边长，避免为超大棋盘分配过多资源。
MIN_SIZE: int = 2
MAX_SIZE: int = 8

# CLI 允许的边长。
CLI_SIZES: Tuple[int, ...] = (3, 4, 5)

# 洗牌重试上限，防止极端情况下无限循环。
MAX_SHUFFLE_ATTEMPTS: int = 1000


class PuzzleError(ValueError):
    """数字华容道异常：所有非法输入统一抛出此异常。"""


def _require_int(value: object, name: str) -> int:
    """校验 value 为整数（排除 bool），否则抛出中文异常。"""
    if isinstance(value, bool) or not isinstance(value, int):
        raise PuzzleError(f"{name} 必须是整数，收到：{value!r}")
    return value


def _require_size(size: object) -> int:
    """校验棋盘边长是否在支持范围内。"""
    value = _require_int(size, "棋盘边长")
    if value < MIN_SIZE or value > MAX_SIZE:
        raise PuzzleError(
            f"棋盘边长必须在 {MIN_SIZE} 到 {MAX_SIZE} 之间，收到：{value}"
        )
    return value


def goal_board(size: int) -> Board:
    """返回 size×size 的目标棋盘：1..n²-1 顺序排列，0（空格）在最后一格。"""
    n = _require_size(size)
    total = n * n
    return tuple(range(1, total)) + (0,)


def validate_board(board: Board, size: int) -> None:
    """校验棋盘长度与数字集合，非法时抛出 PuzzleError。

    合法条件：长度为 size²，且数字恰好为 0..size²-1 的一个排列。
    """
    n = _require_size(size)
    if not isinstance(board, (tuple, list)):
        raise PuzzleError(f"棋盘必须是元组或列表，收到：{type(board).__name__}")
    expected_len = n * n
    if len(board) != expected_len:
        raise PuzzleError(
            f"棋盘长度应为 {expected_len}，实际为 {len(board)}"
        )
    seen: set[int] = set()
    for position, value in enumerate(board):
        if isinstance(value, bool) or not isinstance(value, int):
            raise PuzzleError(
                f"棋盘第 {position} 个元素必须是整数，收到：{value!r}"
            )
        if value < 0 or value >= expected_len:
            raise PuzzleError(
                f"棋盘数字必须在 0 到 {expected_len - 1} 之间，收到：{value}"
            )
        if value in seen:
            raise PuzzleError(f"棋盘数字重复：{value}")
        seen.add(value)
    if len(seen) != expected_len:
        raise PuzzleError("棋盘数字集合不完整")


def inversions(board: Board) -> int:
    """统计逆序数（忽略空格 0）。"""
    if not isinstance(board, (tuple, list)):
        raise PuzzleError(f"棋盘必须是元组或列表，收到：{type(board).__name__}")
    if len(board) == 0:
        raise PuzzleError("棋盘不能为空")
    values: List[int] = []
    for index, value in enumerate(board):
        if isinstance(value, bool) or not isinstance(value, int):
            raise PuzzleError(
                f"棋盘第 {index} 个元素必须是整数，收到：{value!r}"
            )
        if value < 0:
            raise PuzzleError(f"棋盘数字不能为负数，收到：{value}")
        if value != 0:
            values.append(value)
    count = 0
    for i in range(len(values)):
        for j in range(i + 1, len(values)):
            if values[i] > values[j]:
                count += 1
    return count


def is_solvable(board: Board, size: int) -> bool:
    """判断棋盘是否可还原为目标布局。

    奇数边长：逆序数为偶数即可解。
    偶数边长：逆序数 + 空格所在行（自上而下从 0 计）为奇数即可解。
    """
    n = _require_size(size)
    validate_board(board, n)
    total_inversions = inversions(board)
    blank_index = board.index(0)
    blank_row = blank_index // n
    if n % 2 == 1:
        return total_inversions % 2 == 0
    return (total_inversions + blank_row) % 2 == 1


def shuffle(size: int, seed: Optional[int] = None) -> Board:
    """随机生成一个可解且不等于目标布局的棋盘。

    使用 random.Random(seed) 保证同 seed 结果可复现。
    """
    n = _require_size(size)
    if seed is not None:
        seed = _require_int(seed, "随机种子")
    rng = random.Random(seed)
    goal = goal_board(n)
    for _ in range(MAX_SHUFFLE_ATTEMPTS):
        values = list(range(n * n))
        rng.shuffle(values)
        candidate: Board = tuple(values)
        if candidate != goal and is_solvable(candidate, n):
            return candidate
    raise PuzzleError(
        f"洗牌失败：尝试 {MAX_SHUFFLE_ATTEMPTS} 次后仍未得到可解且非目标的棋盘"
    )


def manhattan(board: Board, size: int) -> int:
    """计算当前棋盘到目标布局的总曼哈顿距离。"""
    n = _require_size(size)
    validate_board(board, n)
    distance = 0
    for index, value in enumerate(board):
        if value == 0:
            continue
        target_index = value - 1
        current_row, current_col = divmod(index, n)
        target_row, target_col = divmod(target_index, n)
        distance += abs(current_row - target_row) + abs(current_col - target_col)
    return distance


def moves(board: Board, size: int) -> List[Tuple[int, int]]:
    """返回空格可交换的下标对 (空格下标, 相邻方块下标)。"""
    n = _require_size(size)
    validate_board(board, n)
    blank_index = board.index(0)
    row, col = divmod(blank_index, n)
    result: List[Tuple[int, int]] = []
    if row > 0:
        result.append((blank_index, blank_index - n))
    if row < n - 1:
        result.append((blank_index, blank_index + n))
    if col > 0:
        result.append((blank_index, blank_index - 1))
    if col < n - 1:
        result.append((blank_index, blank_index + 1))
    return result


def apply_move(board: Board, size: int, index: int) -> Board:
    """将空格与 index 处的方块交换，返回新棋盘；非法下标抛出异常。"""
    n = _require_size(size)
    validate_board(board, n)
    target = _require_int(index, "方块下标")
    total = n * n
    if target < 0 or target >= total:
        raise PuzzleError(f"方块下标必须在 0 到 {total - 1} 之间，收到：{target}")
    blank_index = board.index(0)
    if target == blank_index:
        raise PuzzleError("不能与空格自身交换")
    target_row, target_col = divmod(target, n)
    blank_row, blank_col = divmod(blank_index, n)
    if abs(target_row - blank_row) + abs(target_col - blank_col) != 1:
        raise PuzzleError("只能交换与空格相邻的方块")
    values = list(board)
    values[blank_index], values[target] = values[target], values[blank_index]
    return tuple(values)


def parse_size(raw: str) -> int:
    """解析命令行边长参数，仅允许 3、4、5。"""
    if not isinstance(raw, str):
        raise PuzzleError(f"边长参数必须是字符串，收到：{type(raw).__name__}")
    text = raw.strip()
    if text == "":
        raise PuzzleError("边长参数不能为空")
    if not text.isdigit():
        raise PuzzleError(f"边长必须是数字，收到：{raw!r}")
    value = int(text)
    if value not in CLI_SIZES:
        allowed = "、".join(str(item) for item in CLI_SIZES)
        raise PuzzleError(f"边长只支持 {allowed}，收到：{value}")
    return value
