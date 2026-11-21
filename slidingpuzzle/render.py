from __future__ import annotations

"""HTML 渲染：A4 可打印棋盘 / 方块页，以及单文件离线可玩页面。"""

import html
import json
from typing import List

from .model import Board, PuzzleError, goal_board, manhattan, validate_board

# A4 页面基础样式，打印时去掉屏幕背景与外边距。
_BASE_CSS: str = """
@page { size: A4; margin: 0 }
* { box-sizing: border-box }
html, body { margin: 0; padding: 0 }
body {
  font-family: "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "Noto Sans CJK SC", sans-serif;
  color: #1d1d1f;
  background: #ececec;
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
}
.page {
  width: 210mm;
  min-height: 297mm;
  padding: 12mm;
  box-sizing: border-box;
  overflow: hidden;
  background: #fff;
  margin: 0 auto 8mm;
  display: flex;
  flex-direction: column;
  gap: 6mm;
}
.page h1 { margin: 0; font-size: 9mm; letter-spacing: 1mm; }
.page .sub { margin: 2mm 0 0; font-size: 4mm; color: #666; }
.note { margin: 0; font-size: 4mm; line-height: 1.7; color: #333; }
.board {
  display: grid;
  gap: 1.2mm;
  width: min(150mm, 100%);
  margin: 2mm auto 0;
  padding: 1.2mm;
  background: #1d1d1f;
  border: 2.5px solid #1d1d1f;
}
.corner { background: #fff; }
.col-label, .row-label {
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fff;
  color: #777;
  font-size: 3.4mm;
}
.cell {
  aspect-ratio: 1 / 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fff;
  font-weight: 700;
  color: #111;
}
.cell.blank { background: #f2f2f2; }
.cards {
  display: grid;
  gap: 3mm;
  width: 100%;
  margin-top: 2mm;
}
.card {
  position: relative;
  aspect-ratio: 1 / 1;
  border: 1px dashed #555;
  background: #fff;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1mm;
  page-break-inside: avoid;
  break-inside: avoid;
}
.card::before {
  content: "";
  position: absolute;
  inset: 1.5mm;
  border: 0.4mm solid #e2e2e2;
  border-radius: 1mm;
}
.card .num { font-size: 14mm; font-weight: 700; line-height: 1; }
.card .pos { font-size: 3.2mm; color: #888; }
.hint { margin: 0; font-size: 3.8mm; color: #666; }
.footer { margin-top: auto; font-size: 3.2mm; color: #999; }
@media print {
  body { background: #fff; }
  .page { margin: 0; page-break-after: always; break-after: page; }
  .page:last-child { page-break-after: auto; break-after: auto; }
}
"""


def _clean_title(title: str) -> str:
    """校验并清理标题，非法时抛出 PuzzleError。"""
    if not isinstance(title, str):
        raise PuzzleError(f"标题必须是字符串，收到：{type(title).__name__}")
    text = title.strip()
    if text == "":
        raise PuzzleError("标题不能为空")
    if len(text) > 100:
        raise PuzzleError(f"标题长度不能超过 100 个字符，收到：{len(text)}")
    for char in text:
        if ord(char) < 32 or ord(char) == 127:
            raise PuzzleError("标题不能包含控制字符")
    return text


def _cell_font_size(size: int) -> str:
    """按棋盘边长给出合适的数字字号（毫米）。"""
    return {3: "16mm", 4: "12mm", 5: "9mm"}.get(size, "8mm")


def _board_page(board: Board, size: int, title: str) -> str:
    """生成第一页：带行列坐标的棋盘。"""
    font_size = _cell_font_size(size)
    columns = f"10mm repeat({size}, 1fr)"
    parts: List[str] = []
    parts.append('<section class="page">')
    parts.append(
        f'<header><h1>{html.escape(title)}</h1>'
        f'<p class="sub">{size}×{size} 数字华容道 · 可打印棋盘</p></header>'
    )
    parts.append(
        f'<div class="board" style="grid-template-columns: {columns}; '
        f'font-size: {font_size};">'
    )
    parts.append('<div class="corner"></div>')
    for col in range(1, size + 1):
        parts.append(f'<div class="col-label">{col}</div>')
    for row in range(size):
        parts.append(f'<div class="row-label">{row + 1}</div>')
        for col in range(size):
            value = board[row * size + col]
            if value == 0:
                parts.append('<div class="cell blank"></div>')
            else:
                parts.append(f'<div class="cell">{value}</div>')
    parts.append("</div>")
    last = size * size - 1
    parts.append(
        '<p class="note"><strong>目标布局：</strong>'
        f"从左到右、从上到下依次为 1 到 {last}，最后一个格子为空格。</p>"
    )
    parts.append(
        '<p class="note"><strong>玩法：</strong>'
        "每次只能把与空格相邻的数字方块滑入空格，直到恢复顺序排列。</p>"
    )
    parts.append(
        '<p class="footer">slidingpuzzle · 打印建议：A4 纵向 · 实际大小（100%），不要缩放。</p>'
    )
    parts.append("</section>")
    return "\n".join(parts)


def _cards_page(board: Board, size: int, title: str) -> str:
    """生成第二页：按棋盘顺序排列的编号方块卡片。"""
    parts: List[str] = []
    parts.append('<section class="page">')
    parts.append(
        f'<header><h1>方块 · {html.escape(title)}</h1>'
        '<p class="sub">沿虚线剪下，按棋盘顺序摆放即可拼玩</p></header>'
    )
    parts.append(
        f'<div class="cards" style="grid-template-columns: repeat({size}, 1fr);">'
    )
    total = size * size
    for index in range(total):
        value = board[index]
        if value == 0:
            continue
        row, col = divmod(index, size)
        parts.append(
            '<div class="card">'
            f'<span class="num">{value}</span>'
            f'<span class="pos">第 {row + 1} 行 · 第 {col + 1} 列</span>'
            "</div>"
        )
    parts.append("</div>")
    parts.append(
        '<p class="hint">剪切线为卡片四周的虚线，请沿虚线剪下；'
        "建议使用 120g 以上纸张，避免透光。</p>"
    )
    parts.append('<p class="footer">slidingpuzzle · 共 '
                 f"{total - 1} 张数字卡片 + 1 个空格。</p>")
    parts.append("</section>")
    return "\n".join(parts)


def render_printable(board: Board, size: int, title: str = "数字华容道") -> str:
    """渲染 A4 可打印 HTML：第一页棋盘，第二页编号方块。"""
    validate_board(board, size)
    clean_title = _clean_title(title)
    body = "\n".join(
        [
            _board_page(board, size, clean_title),
            _cards_page(board, size, clean_title),
        ]
    )
    return (
        "<!DOCTYPE html>\n"
        '<html lang="zh-CN">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{html.escape(clean_title)}</title>\n"
        f"<style>{_BASE_CSS}</style>\n"
        "</head>\n<body>\n"
        f"{body}\n"
        "</body>\n</html>\n"
    )


def _json_for_script(data: object) -> str:
    """将数据序列化为可安全嵌入 <script> 的 JSON 文本。"""
    text = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    # 防止 </script> 提前闭合脚本标签，并转义 JS 字符串中的行分隔符。
    return (
        text.replace("</", "<\\/")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )


_PLAY_CSS: str = """
* { box-sizing: border-box }
html, body { height: 100% }
body {
  margin: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(160deg, #eef2f7, #dfe7f1);
  font-family: "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "Noto Sans CJK SC", sans-serif;
  color: #1d1d1f;
}
.app {
  width: min(92vw, 460px);
  padding: 22px;
  background: #fff;
  border-radius: 18px;
  box-shadow: 0 18px 50px rgba(17, 34, 68, 0.14);
}
h1 { margin: 0 0 14px; font-size: 21px; text-align: center; letter-spacing: 1px; }
.stats { display: flex; justify-content: space-between; margin-bottom: 12px; font-size: 15px; color: #444; }
.stats b { color: #0b63ce; font-variant-numeric: tabular-nums; }
.board {
  display: grid;
  gap: 6px;
  padding: 6px;
  background: #1d1d1f;
  border-radius: 10px;
  touch-action: manipulation;
  user-select: none;
  -webkit-user-select: none;
}
.tile {
  aspect-ratio: 1 / 1;
  border: 0;
  border-radius: 8px;
  background: #fff;
  color: #111;
  font: inherit;
  font-size: clamp(22px, 9vw, 40px);
  font-weight: 700;
  cursor: default;
  transition: background .12s ease, transform .08s ease;
}
.tile.adjacent { background: #eaf2ff; cursor: pointer; }
.tile.adjacent:hover { background: #dbe9ff; }
.tile.adjacent:active { transform: scale(.96); }
.blank { background: #1d1d1f; }
.controls { display: flex; gap: 10px; margin-top: 16px; }
.controls button {
  flex: 1;
  padding: 10px 14px;
  font: inherit;
  font-size: 15px;
  border-radius: 10px;
  border: 1px solid #c9d3e0;
  background: #f7f9fc;
  color: #1d1d1f;
  cursor: pointer;
}
.controls button:hover { background: #eef3fa; }
.status { min-height: 20px; margin: 12px 0 0; text-align: center; font-size: 14px; color: #0b7a3b; }
"""

_PLAY_JS: str = """
(function () {
  "use strict";
  var DATA = __DATA__;
  var SIZE = DATA.size;
  var GOAL = DATA.goal;
  var INITIAL = DATA.board.slice();
  var state = INITIAL.slice();
  var moveCount = 0;
  var elapsed = 0;
  var timerId = null;
  var finished = false;

  var boardEl = document.getElementById("board");
  var movesEl = document.getElementById("moves");
  var timerEl = document.getElementById("timer");
  var statusEl = document.getElementById("status");

  function formatTime(seconds) {
    var m = Math.floor(seconds / 60);
    var s = seconds % 60;
    return (m < 10 ? "0" + m : String(m)) + ":" + (s < 10 ? "0" + s : String(s));
  }

  function updateStats() {
    movesEl.textContent = String(moveCount);
    timerEl.textContent = formatTime(elapsed);
  }

  function stopTimer() {
    if (timerId !== null) {
      clearInterval(timerId);
      timerId = null;
    }
  }

  function startTimer() {
    if (timerId !== null) {
      return;
    }
    timerId = setInterval(function () {
      elapsed += 1;
      timerEl.textContent = formatTime(elapsed);
    }, 1000);
  }

  function resetStats() {
    stopTimer();
    moveCount = 0;
    elapsed = 0;
    finished = false;
    statusEl.textContent = "";
    updateStats();
  }

  function indexAt(row, col) {
    return row * SIZE + col;
  }

  function adjacentIndex(blankIndex, tileIndex) {
    var blankRow = Math.floor(blankIndex / SIZE);
    var blankCol = blankIndex % SIZE;
    var row = Math.floor(tileIndex / SIZE);
    var col = tileIndex % SIZE;
    return Math.abs(blankRow - row) + Math.abs(blankCol - col) === 1;
  }

  function blankIndex() {
    return state.indexOf(0);
  }

  function isSolved() {
    for (var i = 0; i < state.length; i += 1) {
      if (state[i] !== GOAL[i]) {
        return false;
      }
    }
    return true;
  }

  function render() {
    var blank = blankIndex();
    boardEl.textContent = "";
    for (var i = 0; i < state.length; i += 1) {
      var value = state[i];
      if (value === 0) {
        var empty = document.createElement("div");
        empty.className = "blank";
        empty.setAttribute("aria-hidden", "true");
        boardEl.appendChild(empty);
        continue;
      }
      var tile = document.createElement("button");
      tile.type = "button";
      tile.className = "tile" + (adjacentIndex(blank, i) ? " adjacent" : "");
      tile.textContent = String(value);
      tile.setAttribute("aria-label", "方块 " + value);
      tile.dataset.index = String(i);
      tile.addEventListener("click", onTileClick);
      boardEl.appendChild(tile);
    }
  }

  function onTileClick(event) {
    var tile = event.currentTarget;
    var index = Number(tile.dataset.index);
    var blank = blankIndex();
    if (!adjacentIndex(blank, index)) {
      return;
    }
    state[blank] = state[index];
    state[index] = 0;
    moveCount += 1;
    if (!finished) {
      startTimer();
    }
    updateStats();
    render();
    if (isSolved()) {
      finished = true;
      stopTimer();
      statusEl.textContent = "完成！共 " + moveCount + " 步，用时 " + formatTime(elapsed);
    }
  }

  function resetTo(values) {
    state = values.slice();
    resetStats();
    render();
  }

  function shuffleBoard() {
    var values = GOAL.slice();
    var blank = values.indexOf(0);
    var attempts = 0;
    do {
      for (var step = 0; step < SIZE * SIZE * 30; step += 1) {
        var row = Math.floor(blank / SIZE);
        var col = blank % SIZE;
        var options = [];
        if (row > 0) { options.push(indexAt(row - 1, col)); }
        if (row < SIZE - 1) { options.push(indexAt(row + 1, col)); }
        if (col > 0) { options.push(indexAt(row, col - 1)); }
        if (col < SIZE - 1) { options.push(indexAt(row, col + 1)); }
        var pick = options[Math.floor(Math.random() * options.length)];
        values[blank] = values[pick];
        values[pick] = 0;
        blank = pick;
      }
      attempts += 1;
    } while (isSame(values, GOAL) && attempts < 20);
    resetTo(values);
  }

  function isSame(left, right) {
    for (var i = 0; i < left.length; i += 1) {
      if (left[i] !== right[i]) {
        return false;
      }
    }
    return true;
  }

  document.getElementById("restart").addEventListener("click", function () {
    resetTo(INITIAL);
  });
  document.getElementById("shuffle").addEventListener("click", shuffleBoard);

  boardEl.style.gridTemplateColumns = "repeat(" + SIZE + ", 1fr)";
  resetTo(INITIAL);
})();
"""


def render_playable(board: Board, size: int, title: str = "数字华容道") -> str:
    """渲染单文件离线可玩 HTML，所有资源内联，无任何外部链接。"""
    validate_board(board, size)
    clean_title = _clean_title(title)
    payload = {
        "size": size,
        "board": list(board),
        "goal": list(goal_board(size)),
        "title": clean_title,
    }
    script = _PLAY_JS.replace("__DATA__", _json_for_script(payload))
    steps_hint = manhattan(board, size)
    body = f"""<main class="app">
  <h1>{html.escape(clean_title)}</h1>
  <div class="stats">
    <span>步数：<b id="moves">0</b></span>
    <span>计时：<b id="timer">00:00</b></span>
  </div>
  <div id="board" class="board" role="grid" aria-label="{size}×{size} 数字华容道棋盘"></div>
  <div class="controls">
    <button id="restart" type="button">重开</button>
    <button id="shuffle" type="button">打乱</button>
  </div>
  <p class="status" id="status" aria-live="polite">点击与空格相邻的方块开始滑动。参考步数下限：{steps_hint}</p>
</main>"""
    return (
        "<!DOCTYPE html>\n"
        '<html lang="zh-CN">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{html.escape(clean_title)}</title>\n"
        f"<style>{_PLAY_CSS}</style>\n"
        "</head>\n<body>\n"
        f"{body}\n"
        f"<script>{script}</script>\n"
        "</body>\n</html>\n"
    )


def render_document(
    board: Board,
    size: int,
    playable: bool,
    title: str = "数字华容道",
) -> str:
    """按 playable 选择可玩页或可打印页，返回完整 HTML 文档。"""
    if not isinstance(playable, bool):
        raise PuzzleError(f"playable 必须是布尔值，收到：{type(playable).__name__}")
    if playable:
        return render_playable(board, size, title)
    return render_printable(board, size, title)
