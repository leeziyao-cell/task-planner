# -*- coding: utf-8 -*-
"""
命令行接口
提供快速任务管理命令
"""
import argparse
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.notion_client import NotionTaskManager
from src.task_manager import TaskScheduler
from src.notifier import DesktopNotifier, TaskTimer


class TaskCLI:
    """任务管理命令行接口"""

    def __init__(self):
        self.notion = NotionTaskManager()
        self.scheduler = TaskScheduler()
        self.notifier = DesktopNotifier()
        self.timer = TaskTimer(self.notifier)

    def add_task(
        self,
        title: str,
        priority: str = "P2",
        due: Optional[str] = None,
        time: Optional[int] = None,
        tags: Optional[str] = None,
    ):
        """添加新任务"""
        tag_list = tags.split(",") if tags else None

        try:
            task_id = self.notion.add_task(
                title=title,
                priority=priority,
                due_date=due,
                estimated_time=time,
                tags=tag_list,
            )
            print(f"[OK] Task added: {title}")
            print(f"   ID: {task_id}")
            print(f"   Priority: {priority}")
            if due:
                print(f"   Due: {due}")
            if time:
                print(f"   Est. Time: {time} min")
        except Exception as e:
            print(f"[ERROR] Failed to add: {e}")
            print("   Hint: Check TASKS_DB_ID in config.py")

    def list_tasks(self, status: Optional[str] = None, today: bool = False):
        """列出任务"""
        try:
            if today:
                date = datetime.now().strftime("%Y-%m-%d")
                tasks = self.notion.get_tasks(scheduled_date=date)
                print(f"\n[Tasks] Today ({date})")
            else:
                tasks = self.notion.get_tasks(status=status)
                print(f"\n[Task List]")

            print("=" * 50)

            if not tasks:
                print("  No tasks")
                return

            for i, task in enumerate(tasks, 1):
                print(f"  {i}. {task['title']}")
                if task["due_date"]:
                    print(f"     Due: {task['due_date']}")
                if task["estimated_time"]:
                    print(f"     Est: {task['estimated_time']} min")

            print("=" * 50)
            print(f"  Total: {len(tasks)} tasks")

        except Exception as e:
            print(f"[ERROR] Failed: {e}")

    def plan_today(self, start: int = 9, end: int = 18):
        """生成今日计划"""
        try:
            # 获取待办任务
            tasks = self.notion.get_tasks()
            if not tasks:
                print("No tasks to schedule")
                return

            # 生成排程
            schedule = self.scheduler.generate_daily_schedule(
                tasks,
                start_hour=start,
                end_hour=end,
            )

            # 显示排程
            print(self.scheduler.format_schedule_text(schedule))

        except Exception as e:
            print(f"[ERROR] Failed: {e}")

    def start_task(self, task_title: str):
        """开始任务计时"""
        self.timer.start(task_title)

    def stop_task(self):
        """停止任务计时"""
        duration = self.timer.stop()
        return duration

    def status(self):
        """查看当前状态"""
        try:
            tasks = self.notion.get_tasks()
            summary = self.scheduler.get_today_summary(tasks)

            print("\n[Status]")
            print("=" * 40)
            print(f"  Date: {summary['date']}")
            print(f"  Total: {summary['total']}")
            print(f"  Todo: {summary['todo']}")
            print(f"  In Progress: {summary['in_progress']}")
            print(f"  Done: {summary['done']}")

            if summary['total'] > 0:
                rate = int(summary['completion_rate'] * 100)
                bar = "=" * (rate // 5) + "-" * (20 - rate // 5)
                print(f"\n  Completion: [{bar}] {rate}%")

            print("=" * 40)

        except Exception as e:
            print(f"[ERROR] Failed: {e}")

    def _get_status_icon(self, status: str) -> str:
        if "Todo" in status:
            return "[ ]"
        elif "Progress" in status:
            return "[~]"
        elif "Done" in status:
            return "[x]"
        elif "Blocked" in status:
            return "[!]"
        return "[?]"

    def _get_priority_icon(self, priority: str) -> str:
        if priority == "P0":
            return "***"
        elif priority == "P1":
            return "** "
        elif priority == "P2":
            return "*  "
        elif priority == "P3":
            return "   "
        return "   "


def main():
    parser = argparse.ArgumentParser(
        description="Notion Task Planner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m src.cli add "Write paper" -p P1 -d 2026-05-20 -t 60
  python -m src.cli list
  python -m src.cli list --today
  python -m src.cli plan
  python -m src.cli start "Write paper"
  python -m src.cli stop
  python -m src.cli status
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # add 命令
    add_parser = subparsers.add_parser("add", help="添加任务")
    add_parser.add_argument("title", help="任务标题")
    add_parser.add_argument("-p", "--priority", default="P2", choices=["P0", "P1", "P2", "P3"], help="优先级 (默认: P2)")
    add_parser.add_argument("-d", "--due", help="截止日期 (YYYY-MM-DD)")
    add_parser.add_argument("-t", "--time", type=int, help="预估时间 (分钟)")
    add_parser.add_argument("--tags", help="标签 (逗号分隔)")

    # list 命令
    list_parser = subparsers.add_parser("list", help="列出任务")
    list_parser.add_argument("--status", help="按状态过滤")
    list_parser.add_argument("--today", action="store_true", help="只显示今日任务")

    # plan 命令
    plan_parser = subparsers.add_parser("plan", help="生成今日计划")
    plan_parser.add_argument("--start", type=int, default=9, help="开始时间 (小时)")
    plan_parser.add_argument("--end", type=int, default=18, help="结束时间 (小时)")

    # start 命令
    start_parser = subparsers.add_parser("start", help="开始任务计时")
    start_parser.add_argument("title", help="任务标题")

    # stop 命令
    subparsers.add_parser("stop", help="停止任务计时")

    # status 命令
    subparsers.add_parser("status", help="查看状态")

    args = parser.parse_args()

    cli = TaskCLI()

    if args.command == "add":
        cli.add_task(args.title, args.priority, args.due, args.time, args.tags)
    elif args.command == "list":
        cli.list_tasks(args.status, args.today)
    elif args.command == "plan":
        cli.plan_today(args.start, args.end)
    elif args.command == "start":
        cli.start_task(args.title)
    elif args.command == "stop":
        cli.stop_task()
    elif args.command == "status":
        cli.status()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
