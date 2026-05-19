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
    /* Main container */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
        font-size: 18px;
    }

    /* Increase all font sizes */
    p, li, label, .stTextInput label, .stSelectbox label, .stNumberInput label,
    .stMultiSelect label, .stDateInput label, .stTimeInput label, .stTextArea label {
        font-size: 18px !important;
    }

    h1 { font-size: 2.8rem !important; }
    h2 { font-size: 2rem !important; }
    h3 { font-size: 1.5rem !important; }

    .stMetric [data-testid="stMetricValue"] {
        font-size: 2.5rem !important;
    }

    .stButton>button {
        font-size: 18px !important;
        padding: 12px 28px !important;
    }

    .stTextInput input, .stSelectbox, .stNumberInput input, .stTextArea textarea {
        font-size: 18px !important;
    }

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
        color: white;
    }
    [data-testid="stSidebar"] .stRadio label {
        color: white !important;
    }
    [data-testid="stSidebar"] .stMarkdown {
        color: #e0e0e0;
    }

    /* Metrics */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 12px;
        color: white;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    [data-testid="stMetric"] label {
        color: rgba(255,255,255,0.9) !important;
        font-size: 0.9rem !important;
    }
    [data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: white !important;
        font-size: 2rem !important;
        font-weight: bold !important;
    }

    /* Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 10px 24px;
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 2px 10px rgba(102, 126, 234, 0.3);
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.5);
    }

    /* Form submit button */
    .stFormSubmitButton>button {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        width: 100%;
    }

    /* Task cards in expanders */
    .streamlit-expanderHeader {
        background: #f8f9fa;
        border-radius: 8px;
        padding: 10px;
        font-weight: 600;
    }
    .streamlit-expanderContent {
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 0 0 8px 8px;
        padding: 15px;
    }

    /* Tables */
    .stDataFrame {
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }

    /* Progress bar */
    .stProgress > div > div {
        background: linear-gradient(90deg, #11998e 0%, #38ef7d 100%);
        border-radius: 10px;
    }

    /* Section headers */
    h1, h2, h3 {
        color: #1a1a2e;
        font-weight: 700;
    }
    h1 {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 2.5rem !important;
    }

    /* Info boxes */
    .stAlert {
        border-radius: 10px;
        border-left-width: 4px;
    }

    /* Custom card */
    div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"] {
        background: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.08);
        margin-bottom: 15px;
    }

    /* Multiselect */
    .stMultiSelect [data-baseweb="tag"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }

    /* Success/Error messages */
    .stSuccess {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        color: white;
    }
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
    st.markdown("""
    <div style="text-align: center; padding: 20px 0;">
        <h1 style="color: white; font-size: 2rem; margin: 0;">Task Planner</h1>
        <p style="color: rgba(255,255,255,0.7); margin: 5px 0 0 0;">Smart Task Management</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Navigation with icons
    page_icons = {
        "Dashboard": "📊",
        "Today's Plan": "📅",
        "Add Task": "➕",
        "Task List": "📋",
        "Timer": "⏱️",
        "Statistics": "📈",
        "Settings": "⚙️"
    }

    page = st.radio(
        "Navigation",
        list(page_icons.keys()),
        format_func=lambda x: f"{page_icons[x]} {x}",
        index=0,
    )

    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: rgba(255,255,255,0.6); font-size: 0.8rem;">
        <p>Powered by Notion API</p>
        <p>v1.0</p>
    </div>
    """, unsafe_allow_html=True)

    # Load tasks
    try:
        all_tasks = managers["notion"].get_tasks()
        todo_count = sum(1 for t in all_tasks if t["status"] == "Todo")
        in_progress_count = sum(1 for t in all_tasks if t["status"] == "In Progress")
        done_count = sum(1 for t in all_tasks if t["status"] == "Done")
    except Exception as e:
        all_tasks = []
        todo_count = 0
        in_progress_count = 0
        done_count = 0


# ==================== Dashboard ====================
if page == "Dashboard":
    st.markdown("# Dashboard")
    st.markdown(f"### Welcome back! Here's your task overview for {datetime.now().strftime('%B %d, %Y')}")

    if not all_tasks:
        st.markdown("""
        <div style="text-align: center; padding: 60px 20px; background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); border-radius: 15px; margin: 20px 0;">
            <h2 style="color: #667eea;">No tasks yet!</h2>
            <p style="color: #666; font-size: 1.1rem;">Click "Add Task" to create your first task</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Top metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Tasks", len(all_tasks))
        with col2:
            st.metric("To Do", todo_count)
        with col3:
            st.metric("In Progress", in_progress_count)
        with col4:
            st.metric("Completed", done_count)

        st.markdown("<br>", unsafe_allow_html=True)

        # Progress bar
        completion_rate = done_count / len(all_tasks) if all_tasks else 0
        st.markdown("### Completion Progress")
        progress_col1, progress_col2 = st.columns([3, 1])
        with progress_col1:
            st.progress(completion_rate)
        with progress_col2:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); padding: 15px; border-radius: 10px; text-align: center;">
                <span style="color: white; font-size: 1.5rem; font-weight: bold;">{completion_rate*100:.0f}%</span>
            </div>
            """, unsafe_allow_html=True)

        # Charts
        st.markdown("<br>", unsafe_allow_html=True)
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
                    "Todo": "#94a3b8",
                    "In Progress": "#3b82f6",
                    "Done": "#10b981"
                },
                hole=0.6,
            )
            fig.update_layout(
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                margin=dict(t=20, b=20, l=20, r=20),
                height=300,
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
                    "P0": "#ef4444",
                    "P1": "#f97316",
                    "P2": "#eab308",
                    "P3": "#6b7280"
                },
            )
            fig.update_layout(
                showlegend=False,
                margin=dict(t=20, b=20, l=20, r=20),
                height=300,
                xaxis_title="",
                yaxis_title="",
            )
            st.plotly_chart(fig, use_container_width=True)

        # Recent tasks
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### Recent Tasks")
        for task in all_tasks[:5]:
            priority_color = get_priority_color(task["priority"])
            status_color = get_status_color(task["status"])
            with st.expander(f"{task['priority']} | {task['title']}"):
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.markdown(f"**Status:** {task['status']}")
                with col2:
                    st.markdown(f"**Due:** {task.get('due_date', 'N/A')}")
                with col3:
                    st.markdown(f"**Est Time:** {task.get('estimated_time', 'N/A')} min")
                with col4:
                    st.markdown(f"**Tags:** {', '.join(task.get('tags', [])) or 'None'}")


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

            with st.expander(f"{task['priority']} | {task['title']}"):
                # Task info
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown(f"**Priority:** {task['priority']}")
                with col2:
                    st.markdown(f"**Due:** {task.get('due_date', 'N/A')}")
                with col3:
                    st.markdown(f"**Est Time:** {task.get('estimated_time', 'N/A')} min")

                if task.get("tags"):
                    st.markdown(f"**Tags:** {', '.join(task['tags'])}")
                if task.get("notes"):
                    st.markdown(f"**Notes:** {task['notes']}")

                st.markdown("---")

                # Action buttons
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    if st.button("Edit", key=f"edit_plan_{task['id']}"):
                        st.session_state.editing_task = task
                        st.rerun()

                with col2:
                    if st.button("Delete", key=f"delete_plan_{task['id']}"):
                        try:
                            managers["notion"].delete_task(task["id"])
                            st.success(f"Deleted: {task['title']}")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")

                with col3:
                    if st.button("Start", key=f"start_plan_{task['id']}"):
                        try:
                            managers["notion"].update_task(task["id"], status="In Progress")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")

                with col4:
                    if st.button("Done", key=f"done_plan_{task['id']}"):
                        try:
                            managers["notion"].update_task(task["id"], status="Done")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")

        # Edit task modal
        if "editing_task" in st.session_state and st.session_state.editing_task:
            st.markdown("---")
            st.markdown("### Edit Task")
            edit_task = st.session_state.editing_task

            with st.form("edit_task_form"):
                new_title = st.text_input("Title", value=edit_task["title"])
                col1, col2 = st.columns(2)
                with col1:
                    priority_idx = ["P0", "P1", "P2", "P3"].index(edit_task.get("priority", "P2"))
                    new_priority = st.selectbox("Priority", ["P0", "P1", "P2", "P3"], index=priority_idx)
                with col2:
                    new_due = st.date_input("Due Date")

                col1, col2 = st.columns(2)
                with col1:
                    new_est_time = st.number_input("Est Time (min)", value=edit_task.get("estimated_time") or 30, min_value=5, max_value=480, step=5)
                with col2:
                    new_tags = st.multiselect("Tags", ["Research", "Writing", "Experiment", "Meeting", "Learning"],
                                              default=edit_task.get("tags", []))

                new_notes = st.text_area("Notes", value=edit_task.get("notes", ""))

                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("Save Changes"):
                        try:
                            managers["notion"].update_task(
                                edit_task["id"],
                                title=new_title,
                                priority=new_priority,
                                due_date=new_due.strftime("%Y-%m-%d"),
                                est_time=new_est_time,
                                tags=new_tags,
                                notes=new_notes,
                            )
                            del st.session_state.editing_task
                            st.success("Task updated!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
                with col2:
                    if st.form_submit_button("Cancel"):
                        del st.session_state.editing_task
                        st.rerun()

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


# ==================== Timer ====================
elif page == "Timer":
    st.markdown("# Timer")
    st.markdown("### Focus Timer - Track your work sessions")

    # Initialize session state for timer
    if "timer_running" not in st.session_state:
        st.session_state.timer_running = False
        st.session_state.timer_start = None
        st.session_state.timer_task = None
        st.session_state.timer_elapsed = 0
        st.session_state.timer_sessions = []  # 保存的历史会话

    # Timer display
    if st.session_state.timer_running and st.session_state.timer_start:
        elapsed = int((datetime.now() - st.session_state.timer_start).total_seconds())
        st.session_state.timer_elapsed = elapsed
    else:
        elapsed = st.session_state.timer_elapsed

    hours = elapsed // 3600
    minutes = (elapsed % 3600) // 60
    seconds = elapsed % 60

    # Big timer display
    st.markdown(f"""
    <div style="text-align: center; padding: 40px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 20px; margin: 20px 0;">
        <h1 style="color: white; font-size: 4rem; margin: 0; letter-spacing: 5px;">
            {hours:02d}:{minutes:02d}:{seconds:02d}
        </h1>
        <p style="color: rgba(255,255,255,0.8); font-size: 1.2rem; margin-top: 10px;">
            {"Running" if st.session_state.timer_running else "Paused"}
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Task selection
    st.markdown("### Select Task")
    todo_tasks = [t for t in all_tasks if t["status"] in ["Todo", "In Progress"]]

    if todo_tasks:
        task_options = [f"[{t['priority']}] {t['title']}" for t in todo_tasks]
        selected_task_idx = st.selectbox(
            "Choose a task to track",
            range(len(task_options)),
            format_func=lambda x: task_options[x],
        )
        selected_task = todo_tasks[selected_task_idx]
    else:
        st.info("No tasks available. Add a task first!")
        selected_task = None

    # Timer controls
    st.markdown("### Controls")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("Start", disabled=st.session_state.timer_running or not selected_task):
            st.session_state.timer_running = True
            st.session_state.timer_start = datetime.now()
            st.session_state.timer_task = selected_task["id"]
            st.rerun()

    with col2:
        if st.button("Pause", disabled=not st.session_state.timer_running):
            st.session_state.timer_running = False
            st.rerun()

    with col3:
        if st.button("Reset"):
            st.session_state.timer_running = False
            st.session_state.timer_start = None
            st.session_state.timer_elapsed = 0
            st.session_state.timer_task = None
            st.rerun()

    # Save session
    st.markdown("---")
    st.markdown("### Save Session")
    st.markdown(f"Time to save: **{st.session_state.timer_elapsed // 60} minutes**")

    if st.button("Save Session", type="primary") and st.session_state.timer_elapsed > 0 and selected_task:
        try:
            minutes = st.session_state.timer_elapsed // 60

            # Save to local history
            managers["scheduler"].record_actual_time(
                selected_task["title"],
                minutes
            )

            # Update Notion task
            try:
                current_actual = selected_task.get("actual_time") or 0
                new_actual = current_actual + minutes
                managers["notion"].update_task(
                    selected_task["id"],
                    actual_time=new_actual
                )
            except Exception as notion_error:
                st.warning(f"Local saved, but Notion update failed: {notion_error}")

            # Add to session history
            st.session_state.timer_sessions.append({
                "task": selected_task["title"],
                "priority": selected_task["priority"],
                "minutes": minutes,
                "time": datetime.now().strftime("%H:%M"),
            })

            st.success(f"Session saved! {minutes} minutes recorded for {selected_task['title']}")

            # Reset timer
            st.session_state.timer_running = False
            st.session_state.timer_start = None
            st.session_state.timer_elapsed = 0
            st.session_state.timer_task = None
            st.rerun()
        except Exception as e:
            st.error(f"Error saving session: {e}")

    # Timer stats
    st.markdown("---")
    st.markdown("### Today's Sessions")

    # Show current running session
    if st.session_state.timer_running:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); padding: 15px; border-radius: 10px; margin-bottom: 15px;">
            <strong>Running:</strong> {selected_task['title'] if selected_task else 'Unknown'} - {st.session_state.timer_elapsed // 60} min
        </div>
        """, unsafe_allow_html=True)

    # Show saved sessions
    if st.session_state.timer_sessions:
        total_time = sum(s["minutes"] for s in st.session_state.timer_sessions)

        # Group sessions by task name
        task_groups = {}
        for session in st.session_state.timer_sessions:
            task_name = session["task"]
            if task_name not in task_groups:
                task_groups[task_name] = {
                    "priority": session["priority"],
                    "total_minutes": 0,
                    "sessions": 0,
                    "last_time": session["time"],
                }
            task_groups[task_name]["total_minutes"] += session["minutes"]
            task_groups[task_name]["sessions"] += 1
            task_groups[task_name]["last_time"] = session["time"]

        # Display grouped tasks
        for task_name, info in task_groups.items():
            sessions_text = f" ({info['sessions']} sessions)" if info['sessions'] > 1 else ""
            st.markdown(f"""
            <div style="background: #f8f9fa; padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 4px solid {get_priority_color(info['priority'])};">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <strong style="font-size: 1.1rem;">{task_name}</strong>
                        <span style="color: #666; font-size: 0.9rem;"> [{info['priority']}]</span>
                        <span style="color: #999; font-size: 0.8rem;">{sessions_text}</span>
                    </div>
                    <div style="text-align: right;">
                        <span style="font-weight: bold; color: #667eea; font-size: 1.3rem;">{info['total_minutes']} min</span>
                        <span style="color: #999; font-size: 0.8rem; margin-left: 10px;">last: {info['last_time']}</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Total summary
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 10px; margin-top: 15px; text-align: center;">
            <span style="color: white; font-size: 1.1rem;">Total Today: </span>
            <span style="color: white; font-size: 1.8rem; font-weight: bold;">{total_time} minutes</span>
            <span style="color: rgba(255,255,255,0.8); font-size: 0.9rem;"> ({len(task_groups)} tasks, {len(st.session_state.timer_sessions)} sessions)</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("No sessions recorded yet today")

    # Auto-refresh if timer is running
    if st.session_state.timer_running:
        import time
        time.sleep(1)
        st.rerun()


# ==================== Statistics ====================
elif page == "Statistics":
    st.markdown("# Statistics")

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
