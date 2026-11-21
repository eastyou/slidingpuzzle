# slidingpuzzle · 数字华容道

[![CI](https://github.com/eastyou/slidingpuzzle/actions/workflows/ci.yml/badge.svg)](https://github.com/eastyou/slidingpuzzle/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)


面向课堂与作品集的数字华容道小工具：只用 Python 标准库，零第三方依赖。

- **可解性判定**：根据逆序数与空格行奇偶性，严格判断任意棋盘能否还原。
- **保证可解洗牌**：`shuffle()` 只返回可解且不等于目标的棋盘，支持随机种子复现。
- **可打印 A4**：一页带行列坐标的棋盘 + 一页编号方块卡片，沿虚线剪下即可拼玩。
- **单文件离线可玩**：点击方块滑动，含步数、计时、重开、打乱，无任何外部资源。
- **中文错误提示**：非法输入统一抛出 `PuzzleError`，CLI 返回约定的退出码。

## 安装

```bash
git clone https://github.com/eastyou/slidingpuzzle.git
cd slidingpuzzle
python -m pip install -e .
```

要求 Python 3.9 及以上。

## 命令行用法

```bash
# 生成 3×3 可打印 A4 页面
slidingpuzzle -o puzzle.html

# 固定随机种子，复现同一套棋盘
slidingpuzzle -o puzzle.html --size 4 --seed 2026

# 同时生成可离线游玩的单文件 HTML（自动加 -play 后缀）
slidingpuzzle -o puzzle.html --size 3 --seed 9 --playable

# 自定义标题
slidingpuzzle -o puzzle.html --title "五年二班 · 数学角"
```

参数说明：

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `-o, --output` | `slidingpuzzle.html` | 可打印 HTML 输出路径 |
| `--size` | `3` | 棋盘边长，支持 3 / 4 / 5 |
| `--seed` | 随机 | 随机种子，用于复现棋盘 |
| `--playable` | 关闭 | 额外生成 `-play` 后缀的可玩 HTML |
| `--title` | `数字华容道` | 页面标题（最长 100 字符） |

退出码：成功 `0`，写文件失败 `1`，参数非法 `2`（错误信息输出到标准错误）。

也可以用模块方式运行：

```bash
python -m slidingpuzzle --size 4 --seed 1 --playable
```

## Python API

```python
from slidingpuzzle import (
    goal_board, is_solvable, shuffle, manhattan, moves, apply_move,
    render_printable, render_playable,
)

board = shuffle(3, seed=42)          # 保证可解、非目标
print(board)                         # 例如 (4, 1, 3, 7, 2, 5, 8, 6, 0)
print(is_solvable(board, 3))         # True
print(manhattan(board, 3))           # 到目标布局的步数下限
print(moves(board, 3))               # [(空格下标, 相邻方块下标), ...]

next_board = apply_move(board, 3, moves(board, 3)[0][1])
html_text = render_playable(next_board, 3, title="数字华容道")
```

### 可解性原理

把棋盘按行优先展平并忽略空格：

- 奇数边长（3×3、5×5）：逆序数为偶数即可解。
- 偶数边长（4×4）：逆序数 + 空格所在行（自上而下从 0 计）为奇数即可解。

`shuffle()` 使用拒绝采样，最多重试 1000 次；依然失败会抛出 `PuzzleError`。

## 打印建议

1. 使用 A4 纵向、实际大小（100%），不要选择“适应页面”。
2. 建议 120g 以上纸张，避免透光。
3. 第一页是棋盘，第二页是编号方块；沿卡片四周虚线剪下。
4. 按卡片上的“第几行 · 第几列”摆放，即可还原洗牌后的初始局面。

## 开发与测试

```bash
python -m unittest discover -s tests -v
```

CI 会在 Ubuntu / macOS / Windows 上覆盖 Python 3.9、3.10、3.13。

## 项目结构

```
slidingpuzzle/
├── slidingpuzzle/
│   ├── __init__.py     # 公开接口
│   ├── __main__.py     # python -m slidingpuzzle
│   ├── model.py        # 校验、可解性、洗牌、曼哈顿距离
│   ├── render.py       # A4 打印页与离线可玩 HTML
│   └── cli.py          # 命令行入口
├── tests/              # unittest 测试
├── examples/           # 生成示例
├── pyproject.toml
├── LICENSE
└── README.md
```

## License

MIT © 2026 eastyou
