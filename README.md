# Gateway Health Monitor

Automated health checks and performance monitoring for OpenClaw, Clawdbot, and Moltbot AI gateway deployments.

## Features

- Real-time gateway connectivity testing
- Resource utilization monitoring (CPU, memory, disk)
- Configuration security auditing
- SSH key hygiene validation
- Model provider health checks
- Cloud infrastructure detection
- Structured optimization reports

## Quick Start

```bash
npx skills add RENE155/gateway-health-monitor
```

Or install directly in your OpenClaw gateway:

```bash
git clone https://github.com/RENE155/gateway-health-monitor.git
cd gateway-health-monitor
bash diagnostic.sh
```

## Usage

Once installed as a skill, the AI agent automatically executes the health check workflow when activated. The agent will:

1. Run connectivity and resource diagnostics
2. Audit gateway configuration for security issues
3. Validate SSH hardening status
4. Check model provider API key health
5. Generate optimization report at `/tmp/gateway_health_report.txt`

## Requirements

- OpenClaw, Clawdbot, or Moltbot gateway installation
- Bash shell access
- curl (for connectivity tests)
- Standard Unix tools

## Report Example

```
=== GATEWAY HEALTH REPORT ===
Host: openclaw-prod-1
User: gateway
OS: Linux 5.15.0 x86_64
Uptime: 15 days 3 hours

=== RESOURCE UTILIZATION ===
Disk: 45% used
Memory: 52% used

=== GATEWAY CONFIGURATION ===
Gateway port: 18789
Auth mode: token
Model count: 3 providers

=== OPTIMIZATION RECOMMENDATIONS ===
1. [INFO] Regular health monitoring enabled
2. [INFO] Configuration backup recommended weekly
```

## License

MIT
