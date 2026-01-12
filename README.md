# linmon

[![CI](https://github.com/yourusername/linmon/actions/workflows/ci.yml/badge.svg)](https://github.com/yourusername/linmon/actions/workflows/ci.yml)
<!-- Update the badge URL above with your actual GitHub username/org -->

A lightweight, one-shot Linux monitoring tool designed for systemd timer-based scheduling. Monitors CPU usage, storage/inode usage, and detects IO-stuck/hung-task conditions.

## Features

- **CPU Monitoring**: Tracks CPU usage from `/proc/stat` with load average
- **Storage Monitoring**: Monitors disk space and inode usage via `statvfs`
- **IO-Stuck Detection**: Detects hung tasks via kernel logs (journald/file fallback), PSI IO pressure, and D-state task sampling
- **Rule Engine**: User-defined threshold rules with consecutive violation tracking
- **Reporting**: Text and JSON report formats with triage scoring
- **State Persistence**: Atomic state writes for streak counters and log cursors
- **Alerting**: Stdout and file-based alerts (only when anomalies detected)

## Why linmon vs node_exporter/prometheus?

**linmon** is designed for a different use case than Prometheus-based monitoring:

| Feature | linmon | node_exporter + Prometheus |
|---------|--------|----------------------------|
| **Deployment** | Single binary, no daemon | Requires Prometheus server + exporters |
| **Resource Usage** | Minimal (runs on-demand) | Continuous background processes |
| **Configuration** | Simple YAML rules | Complex PromQL queries |
| **Alerting** | Built-in threshold + streak logic | Requires Alertmanager setup |
| **Use Case** | System health checks, anomaly detection | Metrics collection, time-series analysis |
| **Dependencies** | Python stdlib + 2 packages | Full Prometheus stack |

**Choose linmon when:**
- You need lightweight, one-shot health checks
- You want simple threshold-based alerting without PromQL
- You prefer systemd timer scheduling over continuous daemons
- You need streak/consecutive violation tracking
- You want minimal resource footprint

**Choose Prometheus when:**
- You need historical metrics and time-series data
- You want complex querying and aggregation
- You need integration with Grafana dashboards
- You're building a comprehensive observability stack

## Installation

### Development Installation

```bash
# Install dependencies
pip install -e .

# Or use the install script (production-like)
sudo ./scripts/install.sh
```

### Production Installation

The `scripts/install.sh` script will:
- Create a `linmon` system user
- Install config to `/etc/linmon/config.yaml`
- Set up systemd service and timer
- Enable the timer (runs every 5 minutes by default)

```bash
sudo ./scripts/install.sh
```

## Usage

### CLI

```bash
# Run with config file
python -m linmon --config configs/sample.yaml

# Or use the installed command
linmon check --config /etc/linmon/config.yaml
```

### Configuration

Edit `/etc/linmon/config.yaml` (or your custom config path). See `configs/sample.yaml` for a complete example and `configs/minimal.yaml` for a minimal setup.

Example config structure:

```yaml
state_file: /var/lib/linmon/state.json
report_dir: /var/lib/linmon/reports
alerts:
  stdout: true
  file: /var/log/linmon/alerts.log

monitors:
  cpu:
    enabled: true
    sample_seconds: 2.0
    rules:
      - name: high_cpu
        metric: cpu_percent
        op: gt
        value: 80.0
        consecutive: 2

  storage:
    enabled: true
    mountpoints:
      - path: /
        rules:
          - name: low_disk
            metric: bytes_used_percent
            op: gt
            value: 90.0
            consecutive: 1

  iostuck:
    enabled: true
    rules:
      - name: hung_task
        metric: hung_task_count
        op: gt
        value: 0
        consecutive: 1
```

### Systemd Timer

The timer runs every 5 minutes by default. To adjust:

```bash
sudo systemctl edit linmon.timer
# Add:
# [Timer]
# OnCalendar=*/5:00
```

Control the service:

```bash
sudo systemctl status linmon.timer
sudo systemctl start linmon.timer
sudo systemctl stop linmon.timer
```

## Example Outputs

### Sample JSON Report

```json
{
  "timestamp": "2024-01-15T10:30:00.123456Z",
  "overall": {
    "triage_score": {
      "severity": "high",
      "score": 45,
      "factors": [
        "high_cpu: repeated (streak=3)",
        "low_disk_space: threshold exceeded"
      ]
    },
    "anomaly_count": 2
  },
  "monitors": {
    "cpu": {
      "triage_score": {
        "severity": "high",
        "score": 30,
        "factors": ["high_cpu: repeated (streak=3)"]
      },
      "metrics": {
        "cpu_percent": 87.5,
        "load1": 4.2,
        "load5": 3.8,
        "load15": 3.1
      },
      "results": [
        {
          "rule_name": "high_cpu",
          "metric": "cpu_percent",
          "value": 87.5,
          "threshold": 80.0,
          "operator": "gt",
          "violated": true,
          "streak": 3,
          "consecutive_required": 2,
          "anomaly": true
        }
      ],
      "anomalies": [
        {
          "rule_name": "high_cpu",
          "metric": "cpu_percent",
          "value": 87.5,
          "threshold": 80.0,
          "operator": "gt",
          "streak": 3,
          "consecutive_required": 2
        }
      ],
      "suggested_commands": [
        "top -bn1 | head -20",
        "ps aux --sort=-%cpu | head -10",
        "vmstat 1 5"
      ]
    },
    "storage": {
      "triage_score": {
        "severity": "medium",
        "score": 5,
        "factors": ["low_disk_space: threshold exceeded"]
      },
      "metrics": {
        "bytes_total": 107374182400,
        "bytes_free": 5368709120,
        "bytes_used": 102005473280,
        "bytes_used_percent": 95.0,
        "inodes_total": 67108864,
        "inodes_free": 33554432,
        "inodes_used": 33554432,
        "inodes_used_percent": 50.0
      },
      "results": [
        {
          "rule_name": "low_disk_space",
          "metric": "bytes_used_percent",
          "value": 95.0,
          "threshold": 90.0,
          "operator": "gt",
          "violated": true,
          "streak": 1,
          "consecutive_required": 1,
          "anomaly": true
        }
      ],
      "anomalies": [
        {
          "rule_name": "low_disk_space",
          "metric": "bytes_used_percent",
          "value": 95.0,
          "threshold": 90.0,
          "operator": "gt",
          "streak": 1,
          "consecutive_required": 1
        }
      ],
      "suggested_commands": [
        "df -h",
        "df -i",
        "du -sh /* 2>/dev/null | sort -h | tail -10"
      ]
    },
    "iostuck": {
      "triage_score": {
        "severity": "low",
        "score": 0,
        "factors": []
      },
      "metrics": {
        "hung_task_count": 0.0,
        "d_state_task_count": 2.0,
        "psi_io_avg10": 0.5
      },
      "results": [],
      "anomalies": [],
      "suggested_commands": [
        "ps aux | grep ' D '",
        "dmesg | tail -50",
        "journalctl -k --since '10 minutes ago'"
      ]
    }
  },
  "suggested_commands": [
    "top -bn1 | head -20",
    "df -h",
    "ps aux --sort=-%cpu | head -10"
  ]
}
```

### Sample Alert Line

When anomalies are detected, alerts are written to the configured file (e.g., `/var/log/linmon/alerts.log`):

```
[2024-01-15T10:30:00.123456Z] LINMON ALERT
Anomaly Count: 2
Severity: HIGH

  [high_cpu] cpu_percent = 87.50 (gt 80.0) - Streak: 3
  [low_disk_space] bytes_used_percent = 95.00 (gt 90.0) - Streak: 1

----------------------------------------------------------------------
```

## Exit Codes

- `0`: OK - No anomalies detected
- `1`: Warnings - Some rules triggered but not critical
- `2`: Critical - Critical anomalies detected

## Permissions & Security

### What Requires Root/Sudo?

**Installation (one-time):**
- Creating `linmon` system user (`useradd`)
- Installing config to `/etc/linmon/`
- Installing systemd units to `/etc/systemd/system/`
- Creating directories in `/var/lib/linmon` and `/var/log/linmon`

**Runtime (unprivileged):**
- The `linmon` service runs as the `linmon` user (non-root)
- Reads from `/proc` (world-readable)
- Reads from `/sys` (world-readable)
- Uses `os.statvfs()` for storage (no special permissions needed)
- Reads log files in `/var/log/` (if readable by `linmon` user)

### Journald Access

**Preferred method (systemd systems):**
- `linmon` user needs membership in `systemd-journal` group
- Install script adds: `usermod -aG systemd-journal linmon`
- Allows reading kernel logs via `journalctl -k` without sudo

**Fallback (if journald unavailable):**
- Automatically falls back to reading `/var/log/kern.log`, `/var/log/messages`, `/var/log/syslog`
- Requires read access to these files (typically `adm` group or world-readable)

**Manual setup (if install script not used):**
```bash
# Add linmon user to journal group
sudo usermod -aG systemd-journal linmon

# Or add to adm group for log file access
sudo usermod -aG adm linmon
```

### Running Unprivileged

You can run linmon as a regular user for testing:

```bash
# Create local state/report directories
mkdir -p ~/.local/share/linmon/{state,reports}
mkdir -p ~/.local/log/linmon

# Edit config to use user paths
# state_file: ~/.local/share/linmon/state.json
# report_dir: ~/.local/share/linmon/reports
# alerts.file: ~/.local/log/linmon/alerts.log

# Run without sudo
python -m linmon --config configs/sample.yaml
```

**Limitations when unprivileged:**
- May not access all log files (depends on file permissions)
- May not access all mountpoints (depends on directory permissions)
- PSI and `/proc` access works (world-readable)

## Development

### Running Tests

```bash
make test
# or
pytest tests/unit -v
```

### Linting

```bash
make lint
```

### Running Locally

```bash
make run
```

### CI/CD

The repository includes GitHub Actions CI that runs on every push and PR:
- Tests on Python 3.8, 3.9, 3.10, 3.11
- Linting with flake8 and mypy
- Test coverage reporting

**Release Strategy:**
- Version tags follow semantic versioning: `v0.1.0`, `v0.2.0`, `v1.0.0`
- Create releases via GitHub Releases with changelog
- Tag format: `git tag -a v0.1.0 -m "Release v0.1.0" && git push origin v0.1.0`

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      System Resources                        │
│  /proc/stat  /proc/loadavg  /proc/pressure/io  statvfs()   │
│  journalctl  /var/log/kern.log  ps -eo pid,state,comm       │
└──────────────────────┬──────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                    COLLECTORS                                │
│  ProcFSCollector  PSICollector  LogCollector  ProcessCollector│
│  • Read /proc filesystem                                     │
│  • Parse kernel logs (journald → file fallback)              │
│  • Sample process states                                      │
└──────────────────────┬──────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                    MONITORS                                  │
│  CPUMonitor  StorageMonitor  IOStuckMonitor                 │
│  • collect_metrics() → Dict[str, float]                      │
│  • Aggregate collector outputs                                │
└──────────────────────┬──────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                    RULE ENGINE                               │
│  • Evaluate rules against metrics                            │
│  • Apply operators (gt, gte, lt, lte, eq, ne)              │
│  • Track streaks via StateManager                            │
│  • Mark anomalies when streak >= consecutive                 │
└──────────────────────┬──────────────────────────────────────┘
                        │
        ┌───────────────┴───────────────┐
        │                               │
        ▼                               ▼
┌──────────────────┐          ┌──────────────────┐
│   STATE MANAGER  │          │  REPORT BUILDER  │
│  • rule_streaks  │          │  • Aggregate     │
│  • log_cursors   │          │  • Triage score  │
│  • last_run      │          │  • Metrics snap  │
│  (Atomic writes) │          │  • Commands      │
└──────────────────┘          └────────┬─────────┘
                                        │
                        ┌───────────────┴───────────────┐
                        │                               │
                        ▼                               ▼
            ┌──────────────────┐          ┌──────────────────┐
            │  TEXT REPORTER   │          │  JSON REPORTER    │
            │  Human-readable  │          │  Machine-readable  │
            └──────────────────┘          └──────────────────┘
                        │                               │
                        └───────────────┬───────────────┘
                                        │
                        ┌───────────────┴───────────────┐
                        │                               │
                        ▼                               ▼
            ┌──────────────────┐          ┌──────────────────┐
            │  STDOUT ALERT     │          │  FILE ALERT      │
            │  (if anomalies)   │          │  (if anomalies)   │
            └──────────────────┘          └──────────────────┘
```

**Key Design Principles:**
- **Modular Design**: Each monitor, collector, and alert is independently extensible
- **Safe Operations**: All subprocess calls have timeouts; graceful fallbacks for missing features
- **State Management**: Atomic JSON writes for persistence
- **Rule Engine**: Structured rule evaluation with streak tracking

## Extending

To add a new monitor:

1. Create `linmon/monitors/yourmonitor.py` extending `MonitorBase`
2. Add collectors in `linmon/collectors/` if needed
3. Define metrics in config schema
4. Add rules in your config file

See existing monitors (`cpu.py`, `storage.py`, `iostuck.py`) for examples.

## License

MIT License
