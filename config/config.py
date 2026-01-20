import pathlib
import logging
import sys 

env = "production"
if env == "production":
    from config.production_config import parser
else:
    from config.develop_config import parser


work_space = pathlib.Path(__file__).parent.parent
parser.add_argument("--work_space", type=pathlib.Path, default=work_space, help="工作目录")

params = parser.parse_args()

# 配置logging
logger = logging.getLogger('ai2sql')
logger.setLevel(logging.DEBUG)

if not logger.handlers:

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)

    logger.addHandler(console_handler)


