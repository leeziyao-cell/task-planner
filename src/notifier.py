# -*- coding: utf-8 -*-
"""
桌面通知模块
支持 Windows 桌面通知提醒
"""
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import REMINDER_BEFORE_MINUTES, OVERTIME_WARNING_MINUTES


class DesktopNotifier:
    """桌面通知管理器"""

    def __init__(self):
        self.platform = sys.platform
        self._init_notifier()

    def _init_notifier(self):
        """初始化通知器"""
        try:
            if self.platform == "win32":
                # Windows 10/11 原生通知
                from win10toast import ToastNotifier
                self.toaster = ToastNotifier()
                self.backend = "win10toast"
            else:
                # 跨平台方案
                from plyer import notification
                self.notification = notification
                self.backend = "plyer"
        except ImportError:
            print("⚠️ 通知库未安装，将使用终端输出作为备选")
            print("   安装命令: pip install win10toast (Windows) 或 pip install plyer (跨平台)")
            self.backend = "terminal"

    def send(
        self,
        title: str,
        message: str,
        duration: int = 10,
        icon_path: Optional[str] = None,
    ):
        """发送桌面通知

        Args:
            title: 通知标题
            message: 通知内容
            duration: 显示时长（秒）
            icon_path: 图标路径（可选）
        """
        if self.backend == "win10toast":
            self.toaster.show_toast(
                title=title,
                msg=message,
                duration=duration,
                threaded=True,
            )
        elif self.backend == "plyer":
            self.notification.notify(
                title=title,
                message=message,
                timeout=duration,
                app_icon=icon_path,
            )
        else:
            # 终端备选
            print(f"\n{'='*50}")
            print(f"🔔 {title}")
            print(f"   {message}")
            print(f"{'='*50}\n")

    def remind_task_start(self, task_title: str, scheduled_time: str):
        """任务开始提醒"""
        self.send(
            title="📋 任务提醒",
            message=f"准备开始: {task_title}\n计划时间: {scheduled_time}",
            duration=10,
        )

    def remind_task_overtime(self, task_title: str, minutes: int):
        """任务超时提醒"""
        self.send(
            title="⏰ 超时警告",
            message=f"{task_title}\n已超时 {minutes} 分钟，考虑是否需要休息或调整计划",
            duration=15,
        )

    def remind_break(self, work_minutes: int):
        """休息提醒"""
        self.send(
            title="☕ 休息时间",
            message=f"已连续工作 {work_minutes} 分钟，建议休息 10-15 分钟",
            duration=10,
        )

    def daily_summary(self, summary: dict):
        """每日总结通知"""
        completion = int(summary.get("completion_rate", 0) * 100)
        self.send(
            title="📊 今日总结",
            message=(
                f"完成率: {completion}%\n"
                f"完成: {summary.get('done', 0)}/{summary.get('total', 0)} 个任务\n"
                f"用时: {summary.get('total_actual_minutes', 0)} 分钟"
            ),
            duration=15,
        )


class TaskTimer:
    """任务计时器"""

    def __init__(self, notifier: Optional[DesktopNotifier] = None):
        self.notifier = notifier or DesktopNotifier()
        self.current_task = None
        self.start_time = None
        self._timer_running = False

    def start(self, task_title: str, estimated_minutes: int = 30):
        """开始计时"""
        self.current_task = task_title
        self.start_time = datetime.now()
        self._timer_running = True

        print(f"\n▶️ 开始计时: {task_title}")
        print(f"   预计用时: {estimated_minutes} 分钟")
        print(f"   开始时间: {self.start_time.strftime('%H:%M:%S')}")

    def stop(self) -> int:
        """停止计时，返回实际用时（分钟）"""
        if not self.start_time:
            return 0

        duration = int((datetime.now() - self.start_time).total_seconds() / 60)
        self._timer_running = False

        print(f"\n⏹️ 停止计时: {self.current_task}")
        print(f"   实际用时: {duration} 分钟")

        task_title = self.current_task
        self.current_task = None
        self.start_time = None

        return duration

    def get_elapsed_minutes(self) -> int:
        """获取已用时间（分钟）"""
        if not self.start_time:
            return 0
        return int((datetime.now() - self.start_time).total_seconds() / 60)

    def check_overtime(self, estimated_minutes: int) -> bool:
        """检查是否超时"""
        elapsed = self.get_elapsed_minutes()
        if elapsed > estimated_minutes + OVERTIME_WARNING_MINUTES:
            if self.notifier:
                self.notifier.remind_task_overtime(
                    self.current_task,
                    elapsed - estimated_minutes
                )
            return True
        return False


# 测试
if __name__ == "__main__":
    print("测试桌面通知...")
    notifier = DesktopNotifier()

    # 测试普通通知
    notifier.send("测试通知", "这是一条测试消息")

    # 测试任务提醒
    notifier.remind_task_start("写论文", "14:00-15:30")

    # 测试超时警告
    notifier.remind_task_overtime("跑实验", 30)

    print("\n通知测试完成！")
