# pipewatch

Lightweight CLI monitor for long-running data pipeline jobs with Slack alerting.

---

## Installation

```bash
pip install pipewatch
```

Or install from source:

```bash
git clone https://github.com/yourname/pipewatch.git && cd pipewatch && pip install .
```

---

## Usage

Wrap any pipeline command with `pipewatch` to monitor its runtime and receive a Slack alert on completion or failure:

```bash
pipewatch --job-name "nightly-etl" --slack-webhook $SLACK_WEBHOOK_URL \
  -- python run_pipeline.py --date 2024-01-15
```

**Options:**

| Flag | Description |
|------|-------------|
| `--job-name` | Human-readable name shown in alerts |
| `--slack-webhook` | Incoming Slack webhook URL |
| `--timeout` | Kill job and alert after N seconds |
| `--notify-on` | `all`, `failure`, or `success` (default: `all`) |

**Example alert output in Slack:**
```
✅ [pipewatch] nightly-etl completed in 4m 32s
❌ [pipewatch] nightly-etl FAILED after 1m 08s (exit code 1)
```

You can also set defaults via environment variables:

```bash
export PIPEWATCH_SLACK_WEBHOOK="https://hooks.slack.com/services/..."
export PIPEWATCH_NOTIFY_ON="failure"
```

---

## Requirements

- Python 3.8+
- `requests`

---

## License

MIT © 2024 Your Name