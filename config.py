# -*- coding: utf-8 -*-
"""
任务管理系统配置
"""
import os
from pathlib import Path

# 项目路径
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

# Notion 配置 (从环境变量读取)
NOTION_TOKEN = os.getenv("NOTION_TOKEN", "")
TASKS_DB_ID = os.getenv("TASKS_DB_ID", "")
TIMELOG_DB_ID = os.getenv("TIMELOG_DB_ID", "")

# 本地数据库
LOCAL_DB_PATH = DATA_DIR / "tasks.db"

# 时间管理配置
DEFAULT_WORK_HOURS = {
    "weekday": 8,  # 工作日可用小时
    "weekend": 4,  # 周末可用小时
}

# 任务优先级权重
PRIORITY_WEIGHTS = {
    "P0": 100,  # 紧急重要
    "P1": 75,   # 重要不紧急
    "P2": 50,   # 紧急不重要
    "P3": 25,   # 不紧急不重要
}

# 提醒配置
REMINDER_BEFORE_MINUTES = 15  # 任务开始前多少分钟提醒
OVERTIME_WARNING_MINUTES = 30  # 超时警告阈值

# Web 界面配置
WEB_PORT = 8501
