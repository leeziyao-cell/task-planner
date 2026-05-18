# -*- coding: utf-8 -*-
"""
任务管理器核心逻辑
包含智能排序、时间分配、优先级计算
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import PRIORITY_WEIGHTS, DEFAULT_WORK_HOURS


@dataclass
class TimeSlot:
    """时间段"""
    start: datetime
    end: datetime
    task_id: Optional[str] = None
    task_title: Optional[str] = None

    @property
    def duration_minutes(self) -> int:
        return int((self.end - self.start).total_seconds() / 60)

    def __str__(self) -> str:
        return f"{self.start.strftime('%H:%M')}-{self.end.strftime('%H:%M')}"


class TaskScheduler:
    """智能任务排程器"""

    def __init__(self):
        self.work_hours = DEFAULT_WORK_HOURS
        self.history_file = Path(__file__).parent.parent / "data" / "time_history.json"
        self.history = self._load_history()

    def _load_history(self) -> Dict:
        """加载历史时间记录"""
        if self.history_file.exists():
            with open(self.history_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"tasks": {}}

    def _save_history(self):
        """保存历史时间记录"""
        self.history_file.parent.mkdir(exist_ok=True)
        with open(self.history_file, "w", encoding="utf-8") as f:
            json.dump(self.history, f, ensure_ascii=False, indent=2)

    def calculate_priority_score(self, task: Dict) -> float:
        """计算任务综合优先级分数

        考虑因素：
        1. 优先级权重 (P0-P3)
        2. 截止日期紧迫度
        3. 预估时间长度

        Returns:
            优先级分数，越高越优先
        """
        # 基础优先级分数
        priority = task.get("priority", "P2")
        base_score = PRIORITY_WEIGHTS.get(priority, 50)

        # 截止日期紧迫度
        urgency_bonus = 0
        due_date = task.get("due_date")
        if due_date:
            try:
                due = datetime.strptime(due_date, "%Y-%m-%d")
                days_left = (due - datetime.now()).days
                if days_left < 0:
                    urgency_bonus = 100  # 已过期
                elif days_left == 0:
                    urgency_bonus = 80   # 今天到期
                elif days_left <= 1:
                    urgency_bonus = 60   # 明天到期
                elif days_left <= 3:
                    urgency_bonus = 40   # 3天内
                elif days_left <= 7:
                    urgency_bonus = 20   # 一周内
            except ValueError:
                pass

        # 短任务加成（更容易完成，优先处理）
        estimated = task.get("estimated_time")
        time_bonus = 0
        if estimated:
            if estimated <= 15:
                time_bonus = 10  # 15分钟内
            elif estimated <= 30:
                time_bonus = 5   # 30分钟内

        return base_score + urgency_bonus + time_bonus

    def sort_tasks(self, tasks: List[Dict]) -> List[Dict]:
        """智能排序任务

        按优先级分数降序排列
        """
        return sorted(
            tasks,
            key=lambda t: self.calculate_priority_score(t),
            reverse=True,
        )

    def estimate_task_time(self, task: Dict) -> int:
        """估算任务时间（分钟）

        优先使用用户设定的预估时间，
        如果没有，参考历史数据或使用默认值
        """
        # 用户预估
        if task.get("estimated_time"):
            return task["estimated_time"]

        # 历史数据
        title = task.get("title", "")
        if title in self.history.get("tasks", {}):
            history = self.history["tasks"][title]
            if history.get("avg_time"):
                return int(history["avg_time"])

        # 默认值（基于优先级）
        priority = task.get("priority", "P2")
        defaults = {"P0": 60, "P1": 45, "P2": 30, "P3": 20}
        return defaults.get(priority, 30)

    def generate_daily_schedule(
        self,
        tasks: List[Dict],
        date: Optional[str] = None,
        available_hours: Optional[float] = None,
        start_hour: int = 9,
        end_hour: int = 18,
        break_interval: int = 90,
        break_duration: int = 15,
    ) -> List[TimeSlot]:
        """生成每日排程

        Args:
            tasks: 待排程任务列表
            date: 目标日期 (YYYY-MM-DD)，默认今天
            available_hours: 可用小时数，默认从配置读取
            start_hour: 开始工作时间（24小时制）
            end_hour: 结束工作时间（24小时制）
            break_interval: 工作多久休息一次（分钟）
            break_duration: 休息时长（分钟）

        Returns:
            排程后的时间段列表
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        target_date = datetime.strptime(date, "%Y-%m-%d")

        # 确定可用时间
        if available_hours is None:
            weekday = target_date.weekday()
            if weekday < 5:
                available_hours = self.work_hours["weekday"]
            else:
                available_hours = self.work_hours["weekend"]

        # 智能排序
        sorted_tasks = self.sort_tasks(tasks)

        # 生成时间槽
        schedule = []
        current_time = target_date.replace(hour=start_hour, minute=0, second=0)
        end_time = target_date.replace(hour=end_hour, minute=0, second=0)
        work_since_break = 0

        for task in sorted_tasks:
            # 检查是否超出工作时间
            if current_time >= end_time:
                break

            # 检查是否需要休息
            if work_since_break >= break_interval:
                break_start = current_time
                break_end = current_time + timedelta(minutes=break_duration)
                if break_end <= end_time:
                    schedule.append(TimeSlot(
                        start=break_start,
                        end=break_end,
                        task_id=None,
                        task_title="[Break]"
                    ))
                    current_time = break_end
                    work_since_break = 0

            # 分配任务时间
            task_minutes = self.estimate_task_time(task)
            task_end = current_time + timedelta(minutes=task_minutes)

            # 如果任务超出工作时间，截断
            if task_end > end_time:
                task_end = end_time

            schedule.append(TimeSlot(
                start=current_time,
                end=task_end,
                task_id=task.get("id"),
                task_title=task.get("title", "未知任务"),
            ))

            current_time = task_end
            work_since_break += task_minutes

        return schedule

    def record_actual_time(self, task_title: str, actual_minutes: int):
        """记录实际用时，用于改进未来估算"""
        if "tasks" not in self.history:
            self.history["tasks"] = {}

        if task_title not in self.history["tasks"]:
            self.history["tasks"][task_title] = {
                "records": [],
                "avg_time": None,
            }

        self.history["tasks"][task_title]["records"].append({
            "date": datetime.now().strftime("%Y-%m-%d"),
            "minutes": actual_minutes,
        })

        # 计算平均时间
        records = self.history["tasks"][task_title]["records"]
        avg = sum(r["minutes"] for r in records) / len(records)
        self.history["tasks"][task_title]["avg_time"] = avg

        self._save_history()

    def get_today_summary(self, tasks: List[Dict]) -> Dict:
        """获取今日任务统计

        Returns:
            包含统计信息的字典
        """
        today = datetime.now().strftime("%Y-%m-%d")

        total = len(tasks)
        todo = sum(1 for t in tasks if "Todo" in t.get("status", ""))
        in_progress = sum(1 for t in tasks if "Progress" in t.get("status", ""))
        done = sum(1 for t in tasks if "Done" in t.get("status", ""))
        blocked = sum(1 for t in tasks if "Blocked" in t.get("status", ""))

        total_estimated = sum(
            t.get("estimated_time", 0) or 0 for t in tasks
        )
        total_actual = sum(
            t.get("actual_time", 0) or 0 for t in tasks
        )

        return {
            "date": today,
            "total": total,
            "todo": todo,
            "in_progress": in_progress,
            "done": done,
            "blocked": blocked,
            "completion_rate": done / total if total > 0 else 0,
            "total_estimated_minutes": total_estimated,
            "total_actual_minutes": total_actual,
        }

    def format_schedule_text(self, schedule: List[TimeSlot]) -> str:
        """格式化排程为可读文本"""
        lines = ["[Today Schedule]\n"]
        lines.append("=" * 40)

        for slot in schedule:
            time_str = str(slot)
            if slot.task_id:
                lines.append(f"{time_str}  [Task] {slot.task_title}")
            else:
                lines.append(f"{time_str}  {slot.task_title}")

        lines.append("=" * 40)

        total_work = sum(s.duration_minutes for s in schedule if s.task_id)
        total_break = sum(s.duration_minutes for s in schedule if not s.task_id)
        lines.append(f"\n[Work Time] {total_work} min")
        lines.append(f"[Break Time] {total_break} min")

        return "\n".join(lines)

    def get_statistics(self, tasks: List[Dict]) -> Dict:
        """获取任务统计分析

        Returns:
            包含各种统计数据的字典
        """
        if not tasks:
            return {
                "total": 0,
                "by_status": {},
                "by_priority": {},
                "avg_estimated_time": 0,
                "total_estimated_time": 0,
                "completion_rate": 0,
                "overdue_count": 0,
            }

        # 按状态统计
        by_status = {}
        for t in tasks:
            status = t.get("status", "Unknown")
            by_status[status] = by_status.get(status, 0) + 1

        # 按优先级统计
        by_priority = {}
        for t in tasks:
            priority = t.get("priority", "P2")
            by_priority[priority] = by_priority.get(priority, 0) + 1

        # 时间统计
        estimated_times = [t.get("estimated_time", 0) or 0 for t in tasks]
        total_estimated = sum(estimated_times)
        avg_estimated = total_estimated / len(tasks) if tasks else 0

        # 完成率
        done_count = by_status.get("Done", 0)
        completion_rate = done_count / len(tasks) if tasks else 0

        # 过期任务
        today = datetime.now().strftime("%Y-%m-%d")
        overdue_count = 0
        for t in tasks:
            due_date = t.get("due_date")
            if due_date and due_date < today and t.get("status") != "Done":
                overdue_count += 1

        return {
            "total": len(tasks),
            "by_status": by_status,
            "by_priority": by_priority,
            "avg_estimated_time": avg_estimated,
            "total_estimated_time": total_estimated,
            "completion_rate": completion_rate,
            "overdue_count": overdue_count,
        }

    def get_weekly_trend(self, tasks: List[Dict]) -> List[Dict]:
        """获取本周任务完成趋势

        Returns:
            每天的任务统计列表
        """
        today = datetime.now()
        week_start = today - timedelta(days=today.weekday())

        trend = []
        for i in range(7):
            date = week_start + timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")

            # 统计该日期的任务
            day_tasks = [t for t in tasks if t.get("due_date") == date_str]
            done_tasks = [t for t in day_tasks if t.get("status") == "Done"]

            trend.append({
                "date": date_str,
                "day": date.strftime("%a"),
                "total": len(day_tasks),
                "done": len(done_tasks),
            })

        return trend


# 测试
if __name__ == "__main__":
    scheduler = TaskScheduler()

    # 测试任务
    test_tasks = [
        {"id": "1", "title": "写论文方法部分", "priority": "P1", "estimated_time": 60, "status": "📥 Todo"},
        {"id": "2", "title": "跑消融实验", "priority": "P0", "estimated_time": 45, "status": "📥 Todo", "due_date": "2026-05-17"},
        {"id": "3", "title": "整理参考文献", "priority": "P3", "estimated_time": 20, "status": "📥 Todo"},
        {"id": "4", "title": "代码 review", "priority": "P2", "estimated_time": 30, "status": "📥 Todo"},
    ]

    # 排序
    sorted_tasks = scheduler.sort_tasks(test_tasks)
    print("任务排序结果:")
    for t in sorted_tasks:
        score = scheduler.calculate_priority_score(t)
        print(f"  [{t['priority']}] {t['title']} - 分数: {score}")

    # 生成排程
    print("\n")
    schedule = scheduler.generate_daily_schedule(sorted_tasks)
    print(scheduler.format_schedule_text(schedule))
