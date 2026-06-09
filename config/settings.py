import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

TEMPLATES_DIR = BASE_DIR / "templates"
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
RECORDS_FILE = DATA_DIR / "records.json"
SENSITIVE_WORDS_FILE = DATA_DIR / "sensitive_words.txt"

TRADING_SCENARIOS = [
    "金融风控",
    "市场营销",
    "供应链管理",
    "智慧城市",
    "医疗健康",
    "教育培训",
    "交通出行",
    "其他"
]

UPDATE_FREQUENCIES = [
    "实时",
    "每日",
    "每周",
    "每月",
    "每季度",
    "每年",
    "按需"
]

REQUIRED_MATERIALS = [
    {"code": "CPMS", "name": "产品说明文档", "required": True},
    {"code": "SQMS", "name": "授权说明文档", "required": True},
    {"code": "YLDQ", "name": "样例字段清单", "required": True},
    {"code": "SCRZ", "name": "数据来源证明", "required": True},
    {"code": "AQSM", "name": "安全合规说明", "required": False},
    {"code": "QTLY", "name": "其他材料", "required": False}
]

PLATFORM_NAMING_RULE = "{product_code}_{scene}_{date}_{material_code}"

for dir_path in [TEMPLATES_DIR, DATA_DIR, OUTPUT_DIR]:
    os.makedirs(dir_path, exist_ok=True)
