from __future__ import annotations

"""支持 python -m slidingpuzzle 直接运行。"""

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
