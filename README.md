# linmon

A lightweight, one-shot Linux monitoring tool designed for systemd timer-based scheduling. Monitors CPU usage, storage/inode usage, and detects IO-stuck/hung-task conditions.

## Features

- **CPU Monitoring**: Tracks CPU usage from `/proc/stat` with load average
- **Storage Monitoring**: Monitors disk space and inode usage via `statvfs`
- **IO-Stuck Detection**: Detects hung tasks via kernel logs (journald/file fallback), PSI IO pressure, and D-state task sampling
- **Rule Engine**: User-defined threshold rules with consecutive violation tracking
- **Reporting**: Text and JSON report formats with triage scoring
- **State Persistence**: Atomic state writes for streak counters and log cursors
- **Alerting**: Stdout and file-based alerts (only when anomalies detected)

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

## Exit Codes

- `0`: OK - No anomalies detected
- `1`: Warnings - Some rules triggered but not critical
- `2`: Critical - Critical anomalies detected

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

## Architecture

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
