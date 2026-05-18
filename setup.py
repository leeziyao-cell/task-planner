# -*- coding: utf-8 -*-
"""
初始化脚本 - 创建 Notion 数据库并配置系统
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from src.notion_client import NotionTaskManager


def setup(parent_page_id: str):
    """初始化任务管理系统

    Args:
        parent_page_id: Notion 父页面 ID（用于创建数据库）
    """
    print("[INIT] Start initializing task management system...")

    manager = NotionTaskManager()

    # 创建任务数据库
    print("\n[DB] Creating tasks database...")
    tasks_db_id = manager.create_tasks_database(parent_page_id)
    print(f"   [OK] Tasks DB ID: {tasks_db_id}")

    # 创建时间记录数据库
    print("\n[DB] Creating time log database...")
    timelog_db_id = manager.create_timelog_database(parent_page_id)
    print(f"   [OK] TimeLog DB ID: {timelog_db_id}")

    # 提示用户更新配置
    print("\n" + "="*50)
    print("[CONFIG] Please update config.py with these IDs:")
    print(f'   TASKS_DB_ID = "{tasks_db_id}"')
    print(f'   TIMELOG_DB_ID = "{timelog_db_id}"')
    print("="*50)

    # 或者设置环境变量
    print("\nOr set environment variables:")
    print(f'   set TASKS_DB_ID={tasks_db_id}')
    print(f'   set TIMELOG_DB_ID={timelog_db_id}')

    return tasks_db_id, timelog_db_id


if __name__ == "__main__":
    if len(sys.argv) > 1:
        page_id = sys.argv[1]
        setup(page_id)
    else:
        print("使用方法: python setup.py <parent_page_id>")
        print("\n示例: python setup.py 3619838a-7e5f-80f2-ad65-d411a66f17ef")
        print("\n提示: parent_page_id 是你想要创建数据库的 Notion 页面 ID")
