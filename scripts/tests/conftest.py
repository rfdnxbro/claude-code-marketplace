"""
pytest設定
"""

import sys
from pathlib import Path

# scriptsディレクトリをパスに追加
scripts_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(scripts_dir))
