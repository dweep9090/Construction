from datetime import date, timedelta
import pytest
from app.scheduling.engine import EngineTask, EngineDependency, compute_schedule, detect_cycle, downstream_impact, topological_sort

def create_task(tid: int, dur: int, start: date, status: str = "NOT_STARTED", name: str = "") -> EngineTask:
    return EngineTask(
        id=tid, 
        planned_start=start, 
        planned_end=start + timedelta(days=dur), 
        duration=dur, 
        status=status, 
        progress=0,
    )

def test_linear_chain():
    today = date(2026, 9, 20)
    t1 = create_task(1, 5, today)
    t2 = create_task(2, 5, today + timedelta(days=5))
    tasks = [t1, t2]
    deps = [EngineDependency(1, 2)]
    
    compute_schedule(tasks, deps, today)
    
    assert t1.early_start == today
    assert t1.early_finish == today + timedelta(days=5)
    assert t1.late_start == today
    assert t1.total_float == 0
    assert t1.is_critical is True
    
    assert t2.early_start == today + timedelta(days=5)
    assert t2.early_finish == today + timedelta(days=10)
    assert t2.total_float == 0
    assert t2.is_critical is True

def test_branching_float():
    today = date(2026, 9, 20)
    # 1 -> 2 (dur 10)
    # 1 -> 3 (dur 5)
    t1 = create_task(1, 5, today)
    t2 = create_task(2, 10, today + timedelta(days=5))
    t3 = create_task(3, 5, today + timedelta(days=5))
    tasks = [t1, t2, t3]
    deps = [EngineDependency(1, 2), EngineDependency(1, 3)]
    
    compute_schedule(tasks, deps, today)
    
    assert t2.is_critical is True
    assert t2.total_float == 0
    assert t3.is_critical is False
    assert t3.total_float == 5

def test_cycle_detection():
    today = date(2026, 9, 20)
    tasks = [create_task(i, 5, today) for i in [1, 2, 3]]
    deps = [EngineDependency(1, 2), EngineDependency(2, 3), EngineDependency(3, 1)]
    
    cycle = detect_cycle(tasks, deps)
    assert cycle is not None
    assert set(cycle) == {1, 2, 3}
    
    with pytest.raises(ValueError, match="Cycle detected"):
        topological_sort(tasks, deps)

def test_delayed_critical_task():
    today = date(2026, 9, 20)
    t1 = create_task(1, 5, today)
    t2 = create_task(2, 5, today + timedelta(days=5))
    tasks = [t1, t2]
    deps = [EngineDependency(1, 2)]
    
    # Baseline project end
    p_end = compute_schedule(tasks, deps, today)
    assert p_end == today + timedelta(days=10)
    
    # Delay t1 by 4 days
    t1.status = "COMPLETED"
    t1.actual_start = today
    t1.actual_end = today + timedelta(days=9) # dur was 5, now took 9
    
    new_p_end = compute_schedule(tasks, deps, today)
    assert new_p_end == today + timedelta(days=14)
    assert t2.early_start == today + timedelta(days=9)
    assert t2.is_delayed is True

def test_delayed_non_critical_within_float():
    today = date(2026, 9, 20)
    t1 = create_task(1, 5, today)
    t2 = create_task(2, 10, today + timedelta(days=5))
    t3 = create_task(3, 5, today + timedelta(days=5)) # float = 5
    tasks = [t1, t2, t3]
    deps = [EngineDependency(1, 2), EngineDependency(1, 3)]
    
    # Baseline
    p_end = compute_schedule(tasks, deps, today)
    assert p_end == today + timedelta(days=15)
    
    # Delay t3 by 4 days (within its float)
    t3.status = "COMPLETED"
    t3.actual_start = today + timedelta(days=5)
    t3.actual_end = today + timedelta(days=14) # dur 9 instead of 5, shift 4
    
    new_p_end = compute_schedule(tasks, deps, today)
    assert new_p_end == today + timedelta(days=15) # Project end unchanged
    assert t3.is_delayed is True # Task itself is delayed

def test_downstream_impact():
    today = date(2026, 9, 20)
    t1 = create_task(1, 5, today, name="T1")
    t2 = create_task(2, 5, today + timedelta(days=5), name="T2")
    tasks = [t1, t2]
    deps = [EngineDependency(1, 2)]
    
    t1.status = "COMPLETED"
    t1.actual_start = today
    t1.actual_end = today + timedelta(days=9)
    # To test downstream impact we need forecast_start set which happens in compute_schedule
    compute_schedule(tasks, deps, today)
    
    # For downstream_impact, we want to know what moved
    t1.name = "T1"
    t2.name = "T2"
    impacts = downstream_impact(tasks, deps, [1])
    assert len(impacts) == 1
    assert impacts[0]["task_id"] == 2
    assert impacts[0]["shift_days"] == 4
