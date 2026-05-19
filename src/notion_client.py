# -*- coding: utf-8 -*-
"""
Notion API 集成模块
使用 httpx 直接调用 Notion API (兼容 notion-client 3.x)
"""
import httpx
from datetime import datetime
from typing import Optional, List, Dict
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import NOTION_TOKEN, TASKS_DB_ID, TIMELOG_DB_ID


class NotionTaskManager:
    """Notion 任务管理器"""

    def __init__(self, token: str = NOTION_TOKEN):
        self.token = token
        self.tasks_db_id = TASKS_DB_ID
        self.timelog_db_id = TIMELOG_DB_ID
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Notion-Version': '2022-06-28',
            'Content-Type': 'application/json',
        }
        self.base_url = 'https://api.notion.com/v1'

    def _request(self, method: str, path: str, retries: int = 3, **kwargs) -> dict:
        """统一请求方法，带重试机制"""
        url = f'{self.base_url}/{path}'

        for attempt in range(retries):
            try:
                response = httpx.request(method, url, headers=self.headers, timeout=30, **kwargs)
                if response.status_code >= 400:
                    raise Exception(f"Notion API error ({response.status_code}): {response.text}")
                return response.json()
            except (httpx.ConnectError, httpx.ReadTimeout) as e:
                if attempt == retries - 1:
                    raise Exception(f"Network error after {retries} retries: {e}")
                import time
                time.sleep(1)  # 等待1秒后重试

    # ========== Task CRUD ==========

    def add_task(
        self,
        title: str,
        priority: str = "P2",
        due_date: Optional[str] = None,
        estimated_time: Optional[int] = None,
        tags: Optional[List[str]] = None,
        notes: Optional[str] = None,
    ) -> str:
        """添加新任务

        Returns:
            创建的任务页面 ID
        """
        properties = {
            "Name": {"title": [{"text": {"content": title}}]},
            "Status": {"select": {"name": "Todo"}},
            "Priority": {"select": {"name": priority}},
        }

        if due_date:
            properties["Due Date"] = {"date": {"start": due_date}}

        if estimated_time:
            properties["Est Time"] = {"number": estimated_time}

        if tags:
            properties["Tags"] = {
                "multi_select": [{"name": tag} for tag in tags]
            }

        if notes:
            properties["Notes"] = {
                "rich_text": [{"text": {"content": notes}}]
            }

        data = self._request('POST', 'pages', json={
            "parent": {"database_id": self.tasks_db_id},
            "properties": properties,
        })
        return data["id"]

    def get_tasks(
        self,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """获取任务列表

        Args:
            status: 按状态过滤 (Todo / In Progress / Done)
            priority: 按优先级过滤 (P0 / P1 / P2 / P3)
            limit: 返回数量限制

        Returns:
            任务列表
        """
        filter_conditions = []

        if status:
            filter_conditions.append({
                "property": "Status",
                "select": {"equals": status}
            })

        if priority:
            filter_conditions.append({
                "property": "Priority",
                "select": {"equals": priority}
            })

        query_body = {"page_size": limit}
        if filter_conditions:
            if len(filter_conditions) == 1:
                query_body["filter"] = filter_conditions[0]
            else:
                query_body["filter"] = {"and": filter_conditions}

        data = self._request(
            'POST',
            f'databases/{self.tasks_db_id}/query',
            json=query_body
        )

        tasks = []
        for page in data.get("results", []):
            task = self._parse_task(page)
            tasks.append(task)

        return tasks

    def get_task(self, task_id: str) -> Dict:
        """获取单个任务"""
        page = self._request('GET', f'pages/{task_id}')
        return self._parse_task(page)

    def update_task(self, task_id: str, **kwargs) -> None:
        """更新任务属性

        支持的属性: title, status, priority, due_date, est_time, actual_time, tags, notes
        """
        properties = {}

        if "title" in kwargs:
            properties["Name"] = {
                "title": [{"text": {"content": kwargs["title"]}}]
            }

        if "status" in kwargs:
            properties["Status"] = {"select": {"name": kwargs["status"]}}

        if "priority" in kwargs:
            properties["Priority"] = {"select": {"name": kwargs["priority"]}}

        if "due_date" in kwargs:
            if kwargs["due_date"]:
                properties["Due Date"] = {"date": {"start": kwargs["due_date"]}}
            else:
                properties["Due Date"] = {"date": None}

        if "est_time" in kwargs:
            properties["Est Time"] = {"number": kwargs["est_time"]}

        if "actual_time" in kwargs:
            properties["Actual Time"] = {"number": kwargs["actual_time"]}

        if "tags" in kwargs:
            properties["Tags"] = {
                "multi_select": [{"name": tag} for tag in kwargs["tags"]]
            }

        if "notes" in kwargs:
            properties["Notes"] = {
                "rich_text": [{"text": {"content": kwargs["notes"]}}]
            }

        if properties:
            self._request('PATCH', f'pages/{task_id}', json={"properties": properties})

    def delete_task(self, task_id: str) -> None:
        """删除任务（归档）"""
        self._request('PATCH', f'pages/{task_id}', json={"archived": True})

    # ========== Time Tracking ==========

    def start_task(self, task_id: str) -> Dict:
        """开始任务，记录开始时间

        Returns:
            {"timelog_id": str, "start_time": datetime}
        """
        now = datetime.now()

        # 创建 timelog 记录
        data = self._request('POST', 'pages', json={
            "parent": {"database_id": self.timelog_db_id},
            "properties": {
                "Name": {"title": [{"text": {"content": task_id}}]},
                "Start Time": {"date": {"start": now.isoformat()}},
            }
        })

        # 更新任务状态为 In Progress
        self.update_task(task_id, status="In Progress")

        return {
            "timelog_id": data["id"],
            "start_time": now,
        }

    def finish_task(self, task_id: str, timelog_id: str, note: str = "") -> int:
        """完成任务，记录结束时间

        Returns:
            实际用时（分钟）
        """
        now = datetime.now()

        # 获取 timelog 的开始时间
        timelog = self._request('GET', f'pages/{timelog_id}')
        start_str = timelog["properties"]["Start Time"]["date"]["start"]
        start_time = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
        duration = int((now - start_time).total_seconds() / 60)

        # 更新 timelog
        update_props = {
            "End Time": {"date": {"start": now.isoformat()}},
            "Duration (min)": {"number": duration},
        }
        if note:
            update_props["Note"] = {"rich_text": [{"text": {"content": note}}]}

        self._request('PATCH', f'pages/{timelog_id}', json={"properties": update_props})

        # 更新任务状态为 Done
        self.update_task(task_id, status="Done")

        return duration

    def get_time_logs(self, task_id: Optional[str] = None, limit: int = 50) -> List[Dict]:
        """获取时间记录"""
        query_body = {"page_size": limit}

        if task_id:
            query_body["filter"] = {
                "property": "Name",
                "title": {"contains": task_id}
            }

        data = self._request(
            'POST',
            f'databases/{self.timelog_db_id}/query',
            json=query_body
        )

        logs = []
        for page in data.get("results", []):
            props = page.get("properties", {})
            log = {
                "id": page["id"],
                "task_id": self._get_title(props.get("Name")),
                "start_time": self._get_date(props.get("Start Time")),
                "end_time": self._get_date(props.get("End Time")),
                "duration": self._get_number(props.get("Duration (min)")),
                "note": self._get_rich_text(props.get("Note")),
            }
            logs.append(log)

        return logs

    # ========== Helper Methods ==========

    def _parse_task(self, page: dict) -> Dict:
        """解析 Notion 页面为任务字典"""
        props = page.get("properties", {})
        return {
            "id": page["id"],
            "title": self._get_title(props.get("Name")),
            "status": self._get_select(props.get("Status")) or "Todo",
            "priority": self._get_select(props.get("Priority")) or "P2",
            "due_date": self._get_date(props.get("Due Date")),
            "estimated_time": self._get_number(props.get("Est Time")),
            "actual_time": self._get_number(props.get("Actual Time")),
            "tags": self._get_multi_select(props.get("Tags")),
            "notes": self._get_rich_text(props.get("Notes")),
            "created_time": page.get("created_time"),
            "last_edited_time": page.get("last_edited_time"),
        }

    def _get_title(self, prop: Optional[Dict]) -> str:
        if not prop or not prop.get("title"):
            return ""
        return "".join(t.get("plain_text", "") for t in prop["title"])

    def _get_select(self, prop: Optional[Dict]) -> str:
        if not prop or not prop.get("select"):
            return ""
        return prop["select"].get("name", "")

    def _get_date(self, prop: Optional[Dict]) -> str:
        if not prop or not prop.get("date"):
            return ""
        return prop["date"].get("start", "")

    def _get_number(self, prop: Optional[Dict]) -> Optional[float]:
        if not prop:
            return None
        return prop.get("number")

    def _get_multi_select(self, prop: Optional[Dict]) -> List[str]:
        if not prop or not prop.get("multi_select"):
            return []
        return [item["name"] for item in prop["multi_select"]]

    def _get_rich_text(self, prop: Optional[Dict]) -> str:
        if not prop or not prop.get("rich_text"):
            return ""
        return "".join(t.get("plain_text", "") for t in prop["rich_text"])


# 测试
if __name__ == "__main__":
    manager = NotionTaskManager()
    print("NotionTaskManager initialized")
    print(f"Tasks DB: {manager.tasks_db_id}")
    print(f"TimeLog DB: {manager.timelog_db_id}")

    # 测试获取任务
    tasks = manager.get_tasks()
    print(f"\nFound {len(tasks)} tasks:")
    for t in tasks:
        print(f"  - [{t['priority']}] {t['title']} ({t['status']})")
