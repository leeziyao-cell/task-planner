# -*- coding: utf-8 -*-
"""
Task Planner - Streamlit Web Application
Complete task management system with Notion integration
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from src.notion_client import NotionTaskManager
from src.task_manager import TaskScheduler

# Page config
st.set_page_config(
    page_title="Task Planner",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
<style>
    .stMetric {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
    }
    .task-card {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #4CAF50;
        margin-bottom: 10px;
    }
    .priority-P0 { border-left-color: #ff4444; }
    .priority-P1 { border-left-color: #ff8800; }
    .priority-P2 { border-left-color: #ffcc00; }
    .priority-P3 { border-left-color: #888888; }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def init_managers():
    return {
        "notion": NotionTaskManager(),
        "scheduler": TaskScheduler(),
    }


managers = init_managers()


def get_priority_color(priority: str) -> str:
    colors = {"P0": "#ff4444", "P1": "#ff8800", "P2": "#ffcc00", "P3": "#888888"}
    return colors.get(priority, "#888888")


def get_status_color(status: str) -> str:
    colors = {"Todo": "#808080", "In Progress": "#2196F3", "Done": "#4CAF50"}
    return colors.get(status, "#808080")


# ==================== Sidebar ====================
with st.sidebar:
    st.title("Task Planner")
    st.markdown("---")

    page = st.radio(
        "Navigation",
        ["Dashboard", "Today's Plan", "Add Task", "Task List", "Statistics", "Settings"],
        index=0,
    )

    st.markdown("---")
    st.markdown("### Quick Stats")

    try:
        all_tasks = managers["notion"].get_tasks()
        todo_count = sum(1 for t in all_tasks if t["status"] == "Todo")
        in_progress_count = sum(1 for t in all_tasks if t["status"] == "In Progress")
        done_count = sum(1 for t in all_tasks if t["status"] == "Done")

        st.metric("Total Tasks", len(all_tasks))
        st.metric("In Progress", in_progress_count)
    except Exception as e:
        st.error(f"Connection error: {e}")
        all_tasks = []
        todo_count = 0
        in_progress_count = 0
        done_count = 0


# ==================== Dashboard ====================
if page == "Dashboard":
    st.title("Dashboard")

    if not all_tasks:
        st.info("No tasks yet. Add your first task!")
    else:
        # Top metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total", len(all_tasks))
        with col2:
            st.metric("Todo", todo_count)
        with col3:
            st.metric("In Progress", in_progress_count)
        with col4:
            st.metric("Done", done_count)

        # Progress bar
        completion_rate = done_count / len(all_tasks) if all_tasks else 0
        st.markdown("### Completion Progress")
        st.progress(completion_rate)
        st.caption(f"{completion_rate*100:.1f}% complete")

        # Charts
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### Status Distribution")
            status_data = pd.DataFrame({
                "Status": ["Todo", "In Progress", "Done"],
                "Count": [todo_count, in_progress_count, done_count]
            })
            fig = px.pie(
                status_data,
                values="Count",
                names="Status",
                color="Status",
                color_discrete_map={
                    "Todo": "#808080",
                    "In Progress": "#2196F3",
                    "Done": "#4CAF50"
                },
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown("### Priority Distribution")
            priority_counts = {}
            for t in all_tasks:
                p = t.get("priority", "P2")
                priority_counts[p] = priority_counts.get(p, 0) + 1

            priority_data = pd.DataFrame({
                "Priority": list(priority_counts.keys()),
                "Count": list(priority_counts.values())
            })
            fig = px.bar(
                priority_data,
                x="Priority",
                y="Count",
                color="Priority",
                color_discrete_map={
                    "P0": "#ff4444",
                    "P1": "#ff8800",
                    "P2": "#ffcc00",
                    "P3": "#888888"
                },
            )
            st.plotly_chart(fig, use_container_width=True)

        # Recent tasks
        st.markdown("### Recent Tasks")
        for task in all_tasks[:5]:
            with st.expander(f"[{task['priority']}] {task['title']}"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write(f"**Status:** {task['status']}")
                with col2:
                    st.write(f"**Due:** {task.get('due_date', 'N/A')}")
                with col3:
                    st.write(f"**Est Time:** {task.get('estimated_time', 'N/A')} min")


# ==================== Today's Plan ====================
elif page == "Today's Plan":
    st.title("Today's Plan")

    todo_tasks = [t for t in all_tasks if t["status"] == "Todo"]

    if not todo_tasks:
        st.info("No pending tasks to schedule!")
    else:
        # Sort by priority
        sorted_tasks = managers["scheduler"].sort_tasks(todo_tasks)

        st.markdown("### Pending Tasks (Sorted by Priority)")
        for i, task in enumerate(sorted_tasks, 1):
            priority_color = get_priority_color(task["priority"])
            st.markdown(f"""
            <div style="padding: 10px; border-left: 4px solid {priority_color}; margin: 5px 0; background: #f9f9f9;">
                <strong>{i}. {task['title']}</strong> [{task['priority']}]<br>
                <small>Due: {task.get('due_date', 'N/A')} | Est: {task.get('estimated_time', 'N/A')} min</small>
            </div>
            """, unsafe_allow_html=True)

        # Generate schedule
        st.markdown("---")
        st.markdown("### Generate Schedule")

        col1, col2 = st.columns(2)
        with col1:
            start_hour = st.slider("Start Time", 6, 12, 9)
        with col2:
            end_hour = st.slider("End Time", 16, 23, 18)

        if st.button("Generate Today's Schedule"):
            schedule = managers["scheduler"].generate_daily_schedule(
                sorted_tasks,
                start_hour=start_hour,
                end_hour=end_hour,
            )

            st.markdown("### Schedule")

            # Gantt chart
            gantt_data = []
            for slot in schedule:
                gantt_data.append({
                    "Task": slot.task_title or "Break",
                    "Start": slot.start,
                    "Finish": slot.end,
                    "Type": "Task" if slot.task_id else "Break",
                })

            df = pd.DataFrame(gantt_data)
            fig = px.timeline(
                df,
                x_start="Start",
                x_end="Finish",
                y="Task",
                color="Type",
                color_discrete_map={"Task": "#4CAF50", "Break": "#FFE4B5"},
            )
            fig.update_yaxes(autorange="reversed")
            st.plotly_chart(fig, use_container_width=True)

            # Schedule table
            schedule_data = []
            for slot in schedule:
                schedule_data.append({
                    "Time": str(slot),
                    "Task": slot.task_title or "Break",
                    "Duration": f"{slot.duration_minutes} min",
                })
            st.table(pd.DataFrame(schedule_data))


# ==================== Add Task ====================
elif page == "Add Task":
    st.title("Add New Task")

    # Quick add
    st.markdown("### Quick Add")
    quick_title = st.text_input("Task title", placeholder="Enter task title...")
    if st.button("Quick Add") and quick_title:
        try:
            task_id = managers["notion"].add_task(title=quick_title)
            st.success(f"Task added: {quick_title}")
            st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")

    st.markdown("---")

    # Detailed add
    st.markdown("### Detailed Add")
    with st.form("add_task_form"):
        title = st.text_input("Title *", placeholder="Task title")

        col1, col2 = st.columns(2)
        with col1:
            priority = st.selectbox("Priority", ["P0", "P1", "P2", "P3"], index=2)
        with col2:
            due_date = st.date_input("Due Date")

        col1, col2 = st.columns(2)
        with col1:
            estimated_time = st.number_input("Estimated Time (min)", min_value=5, max_value=480, value=30, step=5)
        with col2:
            tags = st.multiselect("Tags", ["Research", "Writing", "Experiment", "Meeting", "Learning"])

        notes = st.text_area("Notes", placeholder="Optional notes...")

        submitted = st.form_submit_button("Add Task")

        if submitted and title:
            try:
                task_id = managers["notion"].add_task(
                    title=title,
                    priority=priority,
                    due_date=due_date.strftime("%Y-%m-%d"),
                    estimated_time=estimated_time,
                    tags=tags,
                    notes=notes,
                )
                st.success(f"Task added: {title}")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")


# ==================== Task List ====================
elif page == "Task List":
    st.title("Task List")

    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        status_filter = st.selectbox("Status", ["All", "Todo", "In Progress", "Done"])
    with col2:
        priority_filter = st.selectbox("Priority", ["All", "P0", "P1", "P2", "P3"])
    with col3:
        search = st.text_input("Search", placeholder="Search tasks...")

    # Filter tasks
    filtered_tasks = all_tasks
    if status_filter != "All":
        filtered_tasks = [t for t in filtered_tasks if t["status"] == status_filter]
    if priority_filter != "All":
        filtered_tasks = [t for t in filtered_tasks if t["priority"] == priority_filter]
    if search:
        filtered_tasks = [t for t in filtered_tasks if search.lower() in t["title"].lower()]

    st.markdown(f"### Tasks ({len(filtered_tasks)})")

    if not filtered_tasks:
        st.info("No tasks found")
    else:
        for task in filtered_tasks:
            priority_color = get_priority_color(task["priority"])
            status_color = get_status_color(task["status"])

            with st.expander(f"[{task['priority']}] {task['title']}"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write(f"**Status:** {task['status']}")
                with col2:
                    st.write(f"**Due:** {task.get('due_date', 'N/A')}")
                with col3:
                    st.write(f"**Est Time:** {task.get('estimated_time', 'N/A')} min")

                if task.get("tags"):
                    st.write(f"**Tags:** {', '.join(task['tags'])}")
                if task.get("notes"):
                    st.write(f"**Notes:** {task['notes']}")

                # Action buttons
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    if st.button("Start", key=f"start_{task['id']}"):
                        try:
                            managers["notion"].update_task(task["id"], status="In Progress")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
                with col2:
                    if st.button("Done", key=f"done_{task['id']}"):
                        try:
                            managers["notion"].update_task(task["id"], status="Done")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
                with col3:
                    if st.button("Delete", key=f"delete_{task['id']}"):
                        try:
                            managers["notion"].delete_task(task["id"])
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")


# ==================== Statistics ====================
elif page == "Statistics":
    st.title("Statistics")

    if not all_tasks:
        st.info("No data to analyze yet")
    else:
        # Status distribution
        st.markdown("### Task Status Distribution")
        status_counts = {}
        for t in all_tasks:
            s = t["status"]
            status_counts[s] = status_counts.get(s, 0) + 1

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Todo", status_counts.get("Todo", 0))
        with col2:
            st.metric("In Progress", status_counts.get("In Progress", 0))
        with col3:
            st.metric("Done", status_counts.get("Done", 0))

        # Priority analysis
        st.markdown("### Priority Analysis")
        priority_data = []
        for t in all_tasks:
            priority_data.append({
                "Priority": t["priority"],
                "Status": t["status"],
                "Est Time": t.get("estimated_time", 0) or 0,
            })

        df = pd.DataFrame(priority_data)

        col1, col2 = st.columns(2)
        with col1:
            fig = px.histogram(
                df,
                x="Priority",
                color="Status",
                barmode="group",
                color_discrete_map={
                    "Todo": "#808080",
                    "In Progress": "#2196F3",
                    "Done": "#4CAF50"
                },
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig = px.box(
                df,
                x="Priority",
                y="Est Time",
                color="Priority",
                color_discrete_map={
                    "P0": "#ff4444",
                    "P1": "#ff8800",
                    "P2": "#ffcc00",
                    "P3": "#888888"
                },
            )
            st.plotly_chart(fig, use_container_width=True)

        # Task list with time
        st.markdown("### Tasks with Time Estimates")
        task_table = []
        for t in all_tasks:
            task_table.append({
                "Title": t["title"],
                "Priority": t["priority"],
                "Status": t["status"],
                "Est Time (min)": t.get("estimated_time", "N/A"),
                "Due Date": t.get("due_date", "N/A"),
            })
        st.dataframe(pd.DataFrame(task_table), use_container_width=True)


# ==================== Settings ====================
elif page == "Settings":
    st.title("Settings")

    st.markdown("### Work Hours")
    col1, col2 = st.columns(2)
    with col1:
        weekday_hours = st.number_input("Weekday Hours", 1, 16, 8)
    with col2:
        weekend_hours = st.number_input("Weekend Hours", 1, 12, 4)

    st.markdown("### Break Settings")
    col1, col2 = st.columns(2)
    with col1:
        break_interval = st.number_input("Break Interval (min)", 30, 180, 90)
    with col2:
        break_duration = st.number_input("Break Duration (min)", 5, 30, 15)

    st.markdown("### Database Info")
    st.code(f"""
Tasks DB ID: {managers['notion'].tasks_db_id}
TimeLog DB ID: {managers['notion'].timelog_db_id}
    """)

    st.markdown("### Export Data")
    if st.button("Export Tasks as CSV"):
        if all_tasks:
            df = pd.DataFrame(all_tasks)
            csv = df.to_csv(index=False)
            st.download_button(
                "Download CSV",
                csv,
                "tasks_export.csv",
                "text/csv",
            )
        else:
            st.info("No tasks to export")
