import math
from datetime import date, timedelta
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Tuple

@dataclass
class EngineTask:
    id: int
    planned_start: date
    planned_end: date
    duration: int
    status: str
    progress: int
    actual_start: Optional[date] = None
    actual_end: Optional[date] = None
    
    # Computed fields
    forecast_start: Optional[date] = None
    forecast_end: Optional[date] = None
    early_start: Optional[date] = None
    early_finish: Optional[date] = None
    late_start: Optional[date] = None
    late_finish: Optional[date] = None
    total_float: int = 0
    is_critical: bool = False
    delay_days: int = 0
    is_delayed: bool = False

@dataclass
class EngineDependency:
    predecessor_id: int
    successor_id: int
    lag_days: int = 0

def build_graph(tasks: List[EngineTask], deps: List[EngineDependency]) -> Tuple[Dict[int, List[EngineDependency]], Dict[int, List[EngineDependency]]]:
    succ_graph = {t.id: [] for t in tasks}
    pred_graph = {t.id: [] for t in tasks}
    for d in deps:
        if d.predecessor_id in succ_graph and d.successor_id in pred_graph:
            succ_graph[d.predecessor_id].append(d)
            pred_graph[d.successor_id].append(d)
    return succ_graph, pred_graph

def detect_cycle(tasks: List[EngineTask], deps: List[EngineDependency]) -> Optional[List[int]]:
    succ_graph, _ = build_graph(tasks, deps)
    visited = set()
    rec_stack = set()
    path = []

    def dfs(node):
        visited.add(node)
        rec_stack.add(node)
        path.append(node)
        
        for edge in succ_graph.get(node, []):
            nxt = edge.successor_id
            if nxt not in visited:
                if dfs(nxt):
                    return True
            elif nxt in rec_stack:
                path.append(nxt)
                return True
                
        rec_stack.remove(node)
        path.pop()
        return False

    for t in tasks:
        if t.id not in visited:
            if dfs(t.id):
                # extract cycle from path
                cycle_start_idx = path.index(path[-1])
                return path[cycle_start_idx:]
    return None

def topological_sort(tasks: List[EngineTask], deps: List[EngineDependency]) -> List[int]:
    succ_graph, pred_graph = build_graph(tasks, deps)
    in_degree = {t.id: len(pred_graph.get(t.id, [])) for t in tasks}
    
    queue = [t_id for t_id, deg in in_degree.items() if deg == 0]
    sorted_ids = []
    
    while queue:
        curr = queue.pop(0)
        sorted_ids.append(curr)
        for edge in succ_graph.get(curr, []):
            nxt = edge.successor_id
            in_degree[nxt] -= 1
            if in_degree[nxt] == 0:
                queue.append(nxt)
                
    if len(sorted_ids) != len(tasks):
        raise ValueError("Cycle detected during topological sort")
        
    return sorted_ids

def forward_pass(tasks: List[EngineTask], deps: List[EngineDependency], today: date):
    succ_graph, pred_graph = build_graph(tasks, deps)
    sorted_ids = topological_sort(tasks, deps)
    task_dict = {t.id: t for t in tasks}
    
    for t_id in sorted_ids:
        t = task_dict[t_id]
        
        if t.status == "COMPLETED" and t.actual_start and t.actual_end:
            t.forecast_start = t.actual_start
            t.forecast_end = t.actual_end
        elif t.status in ("IN_PROGRESS", "BLOCKED") and t.actual_start:
            t.forecast_start = t.actual_start
            remaining = math.ceil(t.duration * (1 - t.progress / 100))
            t.forecast_end = max(t.actual_start + timedelta(days=t.duration), today + timedelta(days=remaining))
        else:
            # NOT_STARTED or ASSIGNED
            earliest_from_preds = None
            for edge in pred_graph.get(t_id, []):
                pred = task_dict[edge.predecessor_id]
                cand = pred.forecast_end + timedelta(days=edge.lag_days)
                if earliest_from_preds is None or cand > earliest_from_preds:
                    earliest_from_preds = cand
            
            if earliest_from_preds is None:
                earliest_from_preds = t.planned_start
                
            t.forecast_start = max(earliest_from_preds, today)
            t.forecast_end = t.forecast_start + timedelta(days=t.duration)
            
        t.early_start = t.forecast_start
        t.early_finish = t.forecast_end
        
        # Delay Detection
        delay_delta = t.forecast_end - t.planned_end
        t.delay_days = delay_delta.days
        t.is_delayed = t.delay_days > 0 or (t.status != "COMPLETED" and today > t.planned_end)

def backward_pass(tasks: List[EngineTask], deps: List[EngineDependency], project_forecast_end: date):
    succ_graph, pred_graph = build_graph(tasks, deps)
    sorted_ids = topological_sort(tasks, deps)
    task_dict = {t.id: t for t in tasks}
    
    for t_id in reversed(sorted_ids):
        t = task_dict[t_id]
        successors = succ_graph.get(t_id, [])
        
        if not successors:
            t.late_finish = project_forecast_end
        else:
            t.late_finish = min(task_dict[edge.successor_id].late_start - timedelta(days=edge.lag_days) for edge in successors)
            
        t.late_start = t.late_finish - timedelta(days=t.duration)
        
        # Compute Float
        if t.status == "COMPLETED":
            # For display purposes, though not truly floating anymore
            t.total_float = max(0, (t.late_start - t.early_start).days)
        else:
            t.total_float = max(0, (t.late_start - t.early_start).days)
            
        t.is_critical = t.total_float == 0

def downstream_impact(tasks: List[EngineTask], deps: List[EngineDependency], changed_task_ids: List[int]) -> List[dict]:
    succ_graph, _ = build_graph(tasks, deps)
    task_dict = {t.id: t for t in tasks}
    
    queue = list(changed_task_ids)
    visited = set(changed_task_ids)
    impacted = []
    
    while queue:
        curr = queue.pop(0)
        for edge in succ_graph.get(curr, []):
            nxt = edge.successor_id
            if nxt not in visited:
                visited.add(nxt)
                queue.append(nxt)
                
                t = task_dict[nxt]
                if t.forecast_start and t.planned_start and t.forecast_start > t.planned_start:
                    shift = (t.forecast_start - t.planned_start).days
                    impacted.append({
                        "task_id": t.id,
                        "name": t.name, # Assuming we add name to EngineTask for this, or join outside
                        "shift_days": shift,
                        "is_critical": t.is_critical
                    })
    return impacted

def compute_schedule(tasks: List[EngineTask], deps: List[EngineDependency], today: date):
    if not tasks:
        return
    forward_pass(tasks, deps, today)
    
    # Find project end
    project_forecast_end = max(t.forecast_end for t in tasks if t.forecast_end)
    
    backward_pass(tasks, deps, project_forecast_end)
    return project_forecast_end
