import xml.etree.ElementTree as ET
from datetime import datetime

import pytest

from scheduler import ScanSchedule, SchedulerManager, main as scheduler_main


def schedule(**kwargs):
    defaults = dict(id="t", name="t", enabled=True, drive="C:", frequency="daily",
                    time="02:00", created_at=datetime(2026, 10, 21))
    return ScanSchedule(**{**defaults, **kwargs})


def test_daily_runs_today_if_still_ahead():
    assert schedule().get_next_run(datetime(2026, 10, 21, 1, 0)) == datetime(2026, 10, 21, 2, 0)
    assert schedule().get_next_run(datetime(2026, 10, 21, 3, 0)) == datetime(2026, 10, 22, 2, 0)


def test_weekly_and_monthly():
    wed = datetime(2026, 10, 21, 3, 0)
    assert schedule(frequency="weekly", day_of_week="friday").get_next_run(wed) == datetime(2026, 10, 23, 2, 0)
    assert schedule(frequency="weekly", day_of_week="wednesday").get_next_run(wed) == datetime(2026, 10, 28, 2, 0)
    assert schedule(frequency="monthly", day_of_month=5).get_next_run(wed) == datetime(2026, 11, 5, 2, 0)
    assert schedule(frequency="monthly", day_of_month=31).get_next_run(datetime(2026, 12, 30)) == datetime(2027, 1, 28, 2, 0)


def test_tasks_and_logs_round_trip(tmp_path, monkeypatch):
    config = str(tmp_path / "tasks.json")
    manager = SchedulerManager(config)
    task_id = manager.add_task("Nightly", drive=str(tmp_path), actions=["scan"])
    assert manager.tasks[task_id].next_run is not None

    log = manager.run_task(task_id)
    assert log.status == "completed", log.error_message

    reloaded = SchedulerManager(config)
    assert isinstance(reloaded.tasks[task_id].next_run, datetime)
    assert len(reloaded.get_recent_logs()) == 1


def test_add_task_validates_input(tmp_path):
    manager = SchedulerManager(str(tmp_path / "tasks.json"))
    with pytest.raises(ValueError):
        manager.add_task("x", frequency="hourly")
    with pytest.raises(ValueError):
        manager.add_task("x", actions=["rm_rf"])


def test_windows_task_xml_is_valid(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    SchedulerManager.create_windows_task("task_1", "Nightly & <weekly>")
    xml_file = tmp_path / "eatup_task_task_1.xml"
    text = xml_file.read_text(encoding="utf-8")
    assert 'encoding="UTF-8"' in text
    assert "http://schemas.microsoft.com/windows/2004/02/mit/task" in text
    ET.fromstring(text)  # must be importable by Task Scheduler
    assert "--auto-run" in text


def test_auto_run_runs_a_task_without_the_menu(tmp_path, monkeypatch):
    config = str(tmp_path / "tasks.json")
    manager = SchedulerManager(config)
    task_id = manager.add_task("Nightly", drive=str(tmp_path), actions=["scan"])
    # main() creates its own manager; hand it the one backed by this tmp config
    monkeypatch.setattr("scheduler.SchedulerManager", lambda *a, **k: manager)
    assert scheduler_main(["--auto-run", task_id]) == 0
    assert scheduler_main(["--auto-run", "missing"]) == 1
