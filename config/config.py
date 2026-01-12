import argparse
import pathlib
from pathlib import Path

env = "development"
if env == "production":
    from config.production_config import parser
else:
    from config.develop_config import parser


work_space = pathlib.Path(__file__).parent.parent
parser.add_argument("--work-space", type=pathlib.Path, default=work_space, help="工作目录")

params = parser.parse_args()


