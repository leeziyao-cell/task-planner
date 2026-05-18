# Notion Task Planner - Quick Start Guide

## 1. Install Dependencies

```bash
cd E:\ECL-VLA\task_planner
pip install -r requirements.txt
```

## 2. Setup Notion Database

First, find a Notion page where you want to create the task database, then run:

```bash
python setup.py <your_page_id>
```

Example:
```bash
python setup.py 3619838a-7e5f-80f2-ad65-d411a66f17ef
```

This will create two databases and show you the IDs. Update `config.py` with these IDs.

## 3. Usage

### Command Line (CLI)

```bash
# Add a task
python -m src.cli add "Write paper" -p P1 -d 2026-05-20 -t 60

# List tasks
python -m src.cli list

# List today's tasks
python -m src.cli list --today

# Generate today's plan
python -m src.cli plan

# Check status
python -m src.cli status
```

### Web Interface

```bash
streamlit run app.py
```

Then open http://localhost:8501

## 4. Features

- **Smart Task Sorting**: Based on priority, due date, and estimated time
- **Auto Scheduling**: Generates daily schedule with breaks
- **Desktop Notifications**: Reminders for task start and overtime
- **Progress Tracking**: Visual dashboard with charts
- **Notion Sync**: All data stored in Notion

## 5. Configuration

Edit `config.py` to customize:
- Work hours per day
- Priority weights
- Reminder timing
- Web interface port
