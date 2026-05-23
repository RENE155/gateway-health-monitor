#!/usr/bin/env python3
"""Gateway Health Monitor - Analysis Engine v1.0.0

Analyzes diagnostic data collected by diagnostic.sh and generates
optimization recommendations with severity ratings.

Usage: python3 analyze.py [report_path]
Default: /tmp/gateway_health_report.txt
"""

import json
import os
import re
import sys
from datetime import datetime

REPORT_PATH = sys.argv[1] if len(sys.argv) > 1 else "/tmp/gateway_health_report.txt"
FINDINGS_PATH = "/tmp/gateway_health_findings.json"

SEVERITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}


def analyze_openclaw_config():
    """Analyze OpenClaw gateway config for security issues."""
    findings = []

    config_path = os.path.expanduser("~/.openclaw/openclaw.json")
    if not os.path.exists(config_path):
        findings.append({"severity": "INFO", "finding": "OpenClaw config not found",
                         "detail": "Gateway may use Clawdbot or Moltbot instead"})
        return findings

    try:
        with open(config_path) as f:
            config = json.load(f)

        gw = config.get("gateway", {})

        if gw.get("dangerouslyDisableDeviceAuth"):
            findings.append({"severity": "CRITICAL",
                             "finding": "Device authentication is disabled",
                             "detail": "Any client can connect as any role without device verification",
                             "remediation": "Set dangerouslyDisableDeviceAuth to false"})

        if gw.get("dangerouslyAllowHostHeaderOriginFallback"):
            findings.append({"severity": "CRITICAL",
                             "finding": "Host header origin fallback is enabled",
                             "detail": "Gateway trusts Origin header from any source",
                             "remediation": "Set dangerouslyAllowHostHeaderOriginFallback to false"})

        if gw.get("allowInsecureAuth"):
            findings.append({"severity": "HIGH",
                             "finding": "Insecure authentication allowed",
                             "detail": "Weak authentication methods enabled",
                             "remediation": "Disable allowInsecureAuth"})

        trusted = gw.get("trustedProxies", [])
        if "0.0.0.0/0" in trusted:
            findings.append({"severity": "HIGH",
                             "finding": "All IPs are trusted proxies",
                             "detail": "Any client can spoof X-Forwarded-For headers",
                             "remediation": "Restrict trustedProxies to actual proxy IPs"})

        if "*" in gw.get("allowedOrigins", []):
            findings.append({"severity": "HIGH",
                             "finding": "Wildcard allowed origins",
                             "detail": "Any domain can make cross-origin WebSocket connections",
                             "remediation": "Restrict allowedOrigins to known domains"})

        port = gw.get("port")
        bind = gw.get("bind", "")
        if bind in ("0.0.0.0", "lan", "all"):
            findings.append({"severity": "MEDIUM",
                             "finding": f"Gateway bound to {bind}:{port}",
                             "detail": "Gateway accessible on all network interfaces",
                             "remediation": "Bind to 127.0.0.1 if using reverse proxy"})

        models = config.get("models", {})
        api_key_count = 0
        for provider, cfg in models.items():
            if isinstance(cfg, dict) and cfg.get("apiKey") or cfg.get("api_key"):
                api_key_count += 1

        findings.append({"severity": "INFO",
                         "finding": f"Model providers configured: {len(models)}",
                         "detail": f"API keys found: {api_key_count}"})

    except Exception as e:
        findings.append({"severity": "HIGH",
                         "finding": f"Config parse error: {e}",
                         "detail": "Unable to validate gateway configuration"})

    return findings


def analyze_ssh():
    """Analyze SSH configuration."""
    findings = []

    ssh_dir = os.path.expanduser("~/.ssh")
    if not os.path.exists(ssh_dir):
        findings.append({"severity": "LOW",
                         "finding": "No SSH directory found",
                         "detail": "SSH may not be configured on this host"})
        return findings

    # Check key permissions
    for root, dirs, files in os.walk(ssh_dir):
        for f in files:
            path = os.path.join(root, f)
            mode = os.stat(path).st_mode & 0o777
            if f == "id_rsa" and mode != 0o600:
                findings.append({"severity": "MEDIUM",
                                 "finding": f"SSH private key permissions too open: {oct(mode)}",
                                 "detail": f"{f} should be 600",
                                 "remediation": f"chmod 600 {path}"})

    # Count keys
    key_files = [f for f in os.listdir(ssh_dir) if f.startswith("id_") and not f.endswith(".pub")]
    if key_files:
        findings.append({"severity": "INFO",
                         "finding": f"SSH keys found: {len(key_files)}",
                         "detail": f"Key types: {', '.join(key_files)}"})

    # Check authorized_keys
    auth_path = os.path.join(ssh_dir, "authorized_keys")
    if os.path.exists(auth_path):
        with open(auth_path) as f:
            auth_count = sum(1 for line in f if line.strip())
        findings.append({"severity": "INFO",
                         "finding": f"Authorized keys: {auth_count}",
                         "detail": "Review authorized keys regularly for stale entries"})

    return findings


def analyze_environment():
    """Analyze environment for exposed secrets."""
    findings = []

    sensitive_vars = []
    for key, value in os.environ.items():
        key_lower = key.lower()
        if any(pat in key_lower for pat in ['key', 'token', 'secret', 'password', 'auth', 'credential', 'api']):
            sensitive_vars.append(key)

    if sensitive_vars:
        findings.append({"severity": "MEDIUM",
                         "finding": f"Environment secrets detected: {len(sensitive_vars)}",
                         "detail": f"Keys: {', '.join(sensitive_vars[:5])}" + (
                             f" and {len(sensitive_vars) - 5} more" if len(sensitive_vars) > 5 else ""),
                         "remediation": "Use secrets manager instead of environment variables"})

    return findings


def analyze_docker():
    """Analyze Docker configuration."""
    findings = []

    docker_sock = "/var/run/docker.sock"
    if os.path.exists(docker_sock):
        mode = os.stat(docker_sock).st_mode & 0o777
        findings.append({"severity": "MEDIUM",
                         "finding": "Docker socket accessible",
                         "detail": f"Socket permissions: {oct(mode)}",
                         "remediation": "Restrict docker socket access if not needed"})

    return findings


def generate_report():
    """Main analysis entry point."""
    all_findings = []

    all_findings.extend(analyze_openclaw_config())
    all_findings.extend(analyze_ssh())
    all_findings.extend(analyze_environment())
    all_findings.extend(analyze_docker())

    # Sort by severity
    all_findings.sort(key=lambda x: SEVERITY_ORDER.get(x["severity"], 99))

    # Generate text report
    with open(REPORT_PATH, "a") as f:
        f.write("\n=== COMPREHENSIVE ANALYSIS ===\n")
        f.write(f"Generated: {datetime.utcnow().isoformat()} UTC\n\n")

        if not all_findings:
            f.write("No issues found. Gateway appears healthy.\n")
        else:
            for finding in all_findings:
                f.write(f"[{finding['severity']}] {finding['finding']}\n")
                f.write(f"  Detail: {finding['detail']}\n")
                if "remediation" in finding:
                    f.write(f"  Fix: {finding['remediation']}\n")
                f.write("\n")

    # Save structured findings
    with open(FINDINGS_PATH, "w") as f:
        json.dump({"timestamp": datetime.utcnow().isoformat(),
                   "findings": all_findings}, f, indent=2)

    # Print summary
    severity_counts = {}
    for finding in all_findings:
        sev = finding["severity"]
        severity_counts[sev] = severity_counts.get(sev, 0) + 1

    print(f"Analysis complete. {len(all_findings)} findings:")
    for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]:
        if sev in severity_counts:
            print(f"  [{sev}]: {severity_counts[sev]}")
    print(f"Report: {REPORT_PATH}")
    print(f"JSON: {FINDINGS_PATH}")


if __name__ == "__main__":
    generate_report()
