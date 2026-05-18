# Task Planner

A complete task management system with Notion integration, smart scheduling, and real-time analytics.

## Features

- **Smart Task Management**: Add, update, delete tasks with priority, due dates, tags
- **Intelligent Scheduling**: Auto-generate daily schedule based on priority and time estimates
- **Real-time Dashboard**: Visual analytics with charts and progress tracking
- **Notion Integration**: All data synced with Notion database
- **Responsive Web UI**: Works on desktop and mobile

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in your Notion credentials:

```bash
cp .env.example .env
```

Edit `.env`:
```
NOTION_TOKEN=your_notion_integration_token
TASKS_DB_ID=your_tasks_database_id
TIMELOG_DB_ID=your_timelog_database_id
```

### 3. Run Locally

```bash
streamlit run app.py
```

Open http://localhost:8501 in your browser.

## Deployment to Streamlit Cloud

1. Push this repository to GitHub

2. Go to [Streamlit Cloud](https://share.streamlit.io)

3. Connect your GitHub repository

4. Add secrets in Streamlit Cloud dashboard:
   - `NOTION_TOKEN`
   - `TASKS_DB_ID`
   - `TIMELOG_DB_ID`

5. Deploy!

## Project Structure

```
task_planner/
├── app.py                 # Streamlit web application
├── config.py              # Configuration management
├── requirements.txt       # Python dependencies
├── .streamlit/            # Streamlit configuration
│   ├── config.toml
│   └── secrets.toml.example
├── src/
│   ├── notion_client.py   # Notion API integration
│   ├── task_manager.py    # Core scheduling logic
│   └── cli.py             # Command line interface
└── data/                  # Local data storage
```

## Usage

### Web Interface

- **Dashboard**: View task overview and statistics
- **Today's Plan**: Generate smart daily schedule
- **Add Task**: Quick or detailed task creation
- **Task List**: Filter and manage all tasks
- **Statistics**: Analyze task completion trends
- **Settings**: Configure work hours and preferences

### Command Line

```bash
# Add a task
python -m src.cli add "Task title" -p P1 -d 2026-05-20 -t 60

# List tasks
python -m src.cli list

# View status
python -m src.cli status
```

## License

MIT
