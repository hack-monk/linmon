# linmon Code Flow Documentation

## High-Level Execution Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    ENTRY POINT                                   │
│  python -m linmon --config <path>  OR  linmon check --config    │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CLI (cli.py)                                  │
│  • Parse command-line arguments                                  │
│  • Extract config path                                           │
│  • Handle --json flag                                            │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              LinmonCore.__init__() (core.py)                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 1. load_config(config_path)                              │  │
│  │    └─> YAML → Pydantic validation → Config object         │  │
│  │                                                             │  │
│  │ 2. StateManager(state_file)                                │  │
│  │    └─> Loads existing state.json (streaks, cursors)        │  │
│  │                                                             │  │
│  │ 3. RuleEngine(state_manager)                               │  │
│  │    └─> Links to state for streak tracking                  │  │
│  │                                                             │  │
│  │ 4. Initialize Monitors (if enabled in config):             │  │
│  │    • CPUMonitor(config, rule_engine)                       │  │
│  │    • StorageMonitor(config, rule_engine)                   │  │
│  │    • IOStuckMonitor(config, rule_engine, state_manager)    │  │
│  │                                                             │  │
│  │ 5. Initialize Reporters:                                    │  │
│  │    • TextReporter()                                        │  │
│  │    • JSONReporter()                                        │  │
│  │                                                             │  │
│  │ 6. Initialize Alerts (if enabled):                        │  │
│  │    • StdoutAlert()                                         │  │
│  │    • FileAlert(filepath)                                  │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              LinmonCore.run() (core.py)                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ STEP 1: Update last_run timestamp                        │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              MONITOR EVALUATION LOOP                             │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ For each enabled monitor:                                  │  │
│  │                                                             │  │
│  │   monitor.evaluate()                                       │  │
│  │   ├─> monitor.collect_metrics()                           │  │
│  │   │   │                                                    │  │
│  │   │   ├─ CPU Monitor:                                     │  │
│  │   │   │   • ProcFSCollector.get_cpu_percent()              │  │
│  │   │   │     └─> Read /proc/stat twice (with sleep)       │  │
│  │   │   │     └─> Calculate: (1 - idle/total) * 100        │  │
│  │   │   │   • ProcFSCollector.read_loadavg()                │  │
│  │   │   │     └─> Read /proc/loadavg                         │  │
│  │   │   │                                                    │  │
│  │   │   ├─ Storage Monitor:                                 │  │
│  │   │   │   • For each mountpoint:                          │  │
│  │   │   │     └─> os.statvfs(mountpoint)                    │  │
│  │   │   │     └─> Calculate bytes/inodes used %              │  │
│  │   │   │                                                    │  │
│  │   │   └─ IO-Stuck Monitor:                                │  │
│  │   │       • LogCollector.collect_kernel_logs()            │  │
│  │   │         ├─> Try journalctl -k (journald)             │  │
│  │   │         └─> Fallback to /var/log/kern.log             │  │
│  │   │       • LogCollector.find_hung_tasks()                │  │
│  │   │         └─> Regex: "blocked for more than X seconds"  │  │
│  │   │       • PSICollector.read_io_pressure() (if available)│  │
│  │   │         └─> Read /proc/pressure/io                    │  │
│  │   │       • ProcessCollector.get_d_state_tasks()          │  │
│  │   │         └─> ps -eo pid,state,comm,wchan | grep " D "  │  │
│  │   │                                                    │  │
│  │   ├─> Collect all rules (global + mountpoint-specific)   │  │
│  │   │                                                    │  │
│  │   └─> rule_engine.evaluate(rules, metrics)             │  │
│  │       │                                                    │  │
│  │       For each rule:                                       │  │
│  │       ├─> Check if metric exists in metrics dict          │  │
│  │       ├─> apply_operator(rule.op, value, threshold)       │  │
│  │       │   └─> Returns True if violated                    │  │
│  │       ├─> Update streak in StateManager:                  │  │
│  │       │   • If violated: increment_rule_streak()          │  │
│  │       │   • If not violated: reset_rule_streak()           │  │
│  │       ├─> Check: streak >= rule.consecutive?              │  │
│  │       └─> Create RuleResult object                         │  │
│  │                                                             │  │
│  │   Returns: List[RuleResult]                                │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              REPORT GENERATION                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ ReportBuilder.build(monitors, results)                    │  │
│  │                                                             │  │
│  │ 1. Collect all anomalies from all monitors                 │  │
│  │                                                             │  │
│  │ 2. Calculate Triage Scores:                                 │  │
│  │    • TriageScorer.score_anomalies(anomalies)               │  │
│  │      └─> Count by severity (critical/high/medium)          │  │
│  │      └─> Calculate score (0-100)                           │  │
│  │      └─> Determine severity level                          │  │
│  │                                                             │  │
│  │ 3. Collect metrics snapshot (for baseline)                │  │
│  │    └─> monitor.collect_metrics() again                     │  │
│  │                                                             │  │
│  │ 4. Collect suggested commands                              │  │
│  │    └─> monitor.get_suggested_commands()                    │  │
│  │                                                             │  │
│  │ 5. Build report dictionary:                                │  │
│  │    {                                                        │  │
│  │      "timestamp": "...",                                    │  │
│  │      "overall": { triage_score, anomaly_count },          │  │
│  │      "monitors": {                                       │   │
│  │        "cpu": { metrics, results, anomalies, ... },      │   │
│  │        "storage": { ... },                               │   │
│  │        "iostuck": { ... }                                │   │
│  │      }                                                   │   │
│  │    }                                                     │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              FORMAT & SAVE REPORTS                              │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ • TextReporter.format(report) → text string              │   │
│  │ • JSONReporter.format(report) → JSON string              │   │
│  │ • atomic_write() to report_dir/report-<timestamp>.txt    │   │
│  │ • atomic_write() to report_dir/report-<timestamp>.json   │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              ALERTING (if anomalies exist)                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ For each alert handler:                                  │   │
│  │   • StdoutAlert.send(anomalies, report)                  │   │
│  │     └─> Prints to stderr with alert banner               │   │
│  │   • FileAlert.send(anomalies, report)                    │   │
│  │     └─> Appends to alert log file                        │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              STATE PERSISTENCE                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ StateManager.save()                                      │   │
│  │   └─> atomic_write_json(state_file, state)               │   │
│  │     └─> Saves:                                           │   │
│  │       • rule_streaks: { rule_name → streak_count }       │   │
│  │       • log_cursors: { source → LogCursor }              │   │
│  │       • last_run: timestamp                              │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌────────────────────────────────────────────────────────────────┐
│              EXIT CODE DETERMINATION                           │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Based on overall triage severity:                        │  │
│  │   • critical → exit_code = 2                             │  │
│  │   • high/medium or any anomalies → exit_code = 1         │  │
│  │   • low (no anomalies) → exit_code = 0                   │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────┬───────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              CLI OUTPUT & EXIT                                  │
│  • Print text_report or json_report to stdout                   │
│  • sys.exit(exit_code)                                          │
└─────────────────────────────────────────────────────────────────┘
```

## Key Components & Data Flow

### 1. Configuration Loading (`config/loader.py`)
- Reads YAML file
- Validates with Pydantic schema
- Rejects unknown monitors/operators
- Returns validated `Config` object

### 2. State Management (`state/manager.py`)
- **Loads** existing state on init (or creates empty)
- **Tracks** rule streaks per rule name
- **Tracks** log cursors for incremental log reading
- **Saves** atomically using temp file + rename

### 3. Rule Evaluation (`rules/engine.py`)
```
For each rule:
  1. Get metric value from metrics dict
  2. Apply operator (gt, gte, lt, lte, eq, ne)
  3. If violated:
       - Increment streak in state
  4. If not violated:
       - Reset streak to 0
  5. Check: streak >= consecutive_required?
       - If yes → anomaly = True
  6. Return RuleResult
```

### 4. Monitor Pattern (`monitors/base.py`)
All monitors follow this pattern:
```python
class Monitor(MonitorBase):
    def collect_metrics() -> Dict[str, float]:
        # Use collectors to gather raw data
        # Return metric_name → value mapping
    
    def evaluate() -> List[RuleResult]:
        # 1. collect_metrics()
        # 2. Get rules (global + mountpoint-specific)
        # 3. rule_engine.evaluate(rules, metrics)
        # 4. Return results
```

### 5. Streak Tracking Logic
- **First violation**: streak = 1, anomaly = False (if consecutive > 1)
- **Second violation**: streak = 2, anomaly = True (if consecutive = 2)
- **Reset**: When rule not violated, streak = 0
- **Persistent**: Streaks survive across runs via state.json

### 6. Triage Scoring (`triage/scorer.py`)
- Counts anomalies by severity indicators
- Calculates score (0-100) based on:
  - Critical: streak >= 5 → +30 points each
  - High: streak >= 3 → +15 points each
  - Medium: others → +5 points each
- Determines severity: critical/high/medium/low

### 7. Report Structure
```json
{
  "timestamp": "2024-01-01T10:00:00Z",
  "overall": {
    "triage_score": { "severity": "high", "score": 45, "factors": [...] },
    "anomaly_count": 2
  },
  "monitors": {
    "cpu": {
      "triage_score": {...},
      "metrics": { "cpu_percent": 85.5, "load1": 2.3 },
      "results": [ {...}, {...} ],
      "anomalies": [ {...} ],
      "suggested_commands": [ "top -bn1", ... ]
    },
    ...
  }
}
```

## Error Handling & Fallbacks

1. **Journald unavailable** → Falls back to file logs (`/var/log/kern.log`, etc.)
2. **PSI unavailable** → Skips PSI metrics (no error)
3. **Mountpoint inaccessible** → Skips that mountpoint (no error)
4. **Metric missing** → Rule skipped (no error)
5. **Subprocess timeout** → Returns error code, continues
6. **State file corrupt** → Starts with empty state

## Atomic Operations

- **State writes**: Temp file → atomic rename
- **Report writes**: Temp file → atomic rename
- **No partial writes**: Either complete or not written

## Systemd Integration

When run via systemd timer:
1. `linmon.service` runs as `linmon` user
2. Executes: `linmon check --config /etc/linmon/config.yaml`
3. Exit code determines service status:
   - 0 = success (no alerts)
   - 1 = warning (logged)
   - 2 = critical (alerted)
