# Internal Git Server Runners Operations Runbook

## Overview

This runbook covers operational procedures for self-hosted git server Actions runners on the HUMMBL fleet. The internal git server is the canonical development surface for all private/internal HUMMBL repos.

## Runner Inventory

### Current Fleet Status (2026-05-29)

| Hostname | Runner Name | Status | Labels | Platform | Python |
|----------|-------------|--------|--------|----------|--------|
| Anvil | anvil-windows-general | ONLINE | self-hosted, windows, python-ci, anvil, windows-general, general | Windows 11 x86_64 | 3.11.15 |
| Nodezero | nodezero-macos-general | OFFLINE | self-hosted, macos, python-ci, nodezero, macos-general, general | macOS 15 ARM64 | 3.14.3 |
| Nodezero | nodezero-macos-arm64 | OFFLINE | self-hosted, macos, arm64, python-ci, nodezero, macos-arm64, general | macOS 15 ARM64 | 3.14.3 |
| Nodezero | nodezero-macos-x64 | OFFLINE | self-hosted, macos, x64, python-ci, nodezero, macos-x64, general | macOS 15 ARM64 (Rosetta) | 3.14.3 |
| Anvil | anvil-windows-arm64 | OFFLINE | self-hosted, windows, arm64, python-ci, anvil, windows-arm64, general | Windows 11 x86_64 | 3.11.15 |
| Anvil | anvil-windows-x64 | OFFLINE | self-hosted, windows, x64, python-ci, anvil, windows-x64, general | Windows 11 x86_64 | 3.11.15 |

**Total**: 6 runners, 1 online

### Label Schema

Runners use a hierarchical label schema for job routing:

- **Platform**: `self-hosted`, `windows`, `macos`, `linux`
- **Architecture**: `x64`, `arm64`
- **Purpose**: `python-ci`, `general`
- **Host**: `anvil`, `nodezero`
- **Specific**: `windows-general`, `macos-general`, `windows-arm64`, `macos-arm64`

## Common Operations

### Check Runner Status

#### Via Internal Git Server Web UI
1. Navigate to the operator-configured internal git server URL.
2. Go to `Actions` → `Runners`
3. View runner status, labels, and last activity

#### Via SSH (Anvil)
```bash
# Check act_runner processes
ps aux | grep act_runner

# Check runner logs
tail -f <RUNNER_LOG_PATH>/*.log
```

#### Via SSH (Nodezero)
```bash
# Check act_runner processes
ps aux | grep act_runner

# Check runner logs
tail -f <RUNNER_LOG_PATH>/*.log
```

### Bring Runner Online

#### Anvil (Windows)
```powershell
# Navigate to runner directory
cd <RUNNER_HOME_DIR>

# Start runner (host mode)
.\act_runner daemon --config config.yaml
```

#### Nodezero (macOS)
```bash
# Navigate to runner directory
cd <RUNNER_HOME_DIR>

# Start runner (host mode)
./act_runner daemon --config config.yaml
```

### Bring Runner Offline

#### Graceful Shutdown
```bash
# Send SIGTERM to act_runner process
pkill -TERM act_runner

# Wait for current jobs to complete (monitor logs)
tail -f <RUNNER_LOG_PATH>/*.log
```

#### Force Shutdown (Emergency Only)
```bash
# Send SIGKILL (immediate termination, job failure)
pkill -KILL act_runner
```

### Configure Runner Labels

Labels are defined in the runner config file (`config.yaml`):

```yaml
# Example config.yaml
runner:
  labels:
    - "self-hosted"
    - "windows"
    - "python-ci"
    - "anvil"
    - "windows-general"
    - "general"
```

To update labels:
1. Edit `config.yaml`
2. Restart the runner daemon
3. Verify labels in internal git server web UI

## Dual-Label Strategy for GitHub/Internal Git Server Portability

### Problem
GitHub Actions uses standard labels (`ubuntu-latest`, `windows-latest`, `macos-latest`) while the internal git server only recognizes custom self-hosted labels. This causes workflows to fail when migrated between platforms.

### Solution
Use a dual-label strategy that includes both platform-standard and custom labels:

```yaml
jobs:
  test:
    runs-on: [ubuntu-latest, self-hosted, windows, python-ci, anvil, windows-general, general]
```

### How It Works
- **GitHub Actions**: Matches `ubuntu-latest` runner (ignores unrecognized custom labels)
- **Internal Git Server Actions**: Matches all custom labels using AND logic (requires runner to have ALL labels)
- **Portability**: Same workflow file works on both platforms without modification

### Implementation Guidelines
1. Always include the platform-standard label first (`ubuntu-latest`, `windows-latest`, `macos-latest`)
2. Follow with all required custom labels for the target platform
3. Ensure runners have ALL custom labels defined in the workflow
4. Test workflows on both platforms after label changes

## Troubleshooting

### Runner Not Appearing in Internal Git Server

**Symptoms**: Runner started but not visible in internal git server UI

**Diagnosis**:
```bash
# Check if act_runner process is running
ps aux | grep act_runner

# Check runner logs for connection errors
tail -f <RUNNER_LOG_PATH>/*.log
```

**Solutions**:
1. Verify `config.yaml` has correct internal git server URL and token
2. Check network connectivity to internal git server
3. Verify runner token is valid (regenerate if needed)
4. Check firewall rules allow outbound connections

### Jobs Not Picking Up

**Symptoms**: Runner online but jobs not executing

**Diagnosis**:
```bash
# Check runner labels match job requirements
# Via internal git server UI: Actions → Runners → [runner] → Labels

# Check runner logs for job assignment
tail -f <RUNNER_LOG_PATH>/*.log | grep "job"
```

**Solutions**:
1. Verify runner has ALL labels required by the job
2. Check runner is not in "offline" state in UI
3. Verify runner has sufficient resources (disk, memory)
4. Check for runner mode restrictions (host vs. container mode)

### Runner Performance Issues

**Symptoms**: Jobs running slowly or timing out

**Diagnosis**:
```bash
# Check system resources
top
htop

# Check disk space
df -h

# Check runner logs for errors
tail -f <RUNNER_LOG_PATH>/*.log
```

**Solutions**:
1. Increase runner resource limits in config
2. Clean up workspace directories
3. Check for background processes consuming resources
4. Consider job consolidation to reduce parallel load

### SSH Connection Timeout to Nodezero

**Symptoms**: Cannot SSH to nodezero

**Diagnosis**:
```bash
# Test SSH connection
ssh -v nodezero

# Check Tailscale status
tailscale status

# Check if nodezero is online
ping <NODEZERO_TAILSCALE_IP>
```

**Solutions**:
1. Verify Tailscale daemon is running on both machines
2. Check for IP changes in Tailscale network
3. Restart Tailscale daemon if needed
4. Check firewall rules on nodezero
5. Use alternative machine for operations if nodezero unavailable

## CI Workflow Label Requirements

### hummbl-governance

Current required labels for all jobs:
```yaml
runs-on: [ubuntu-latest, self-hosted, windows, python-ci, anvil, windows-general, general]
```

**Jobs**:
- `test` (Python 3.11, 3.12, 3.13 matrix)
- `install-smoke` (Python 3.11, 3.12, 3.13 matrix)
- `lint` (Python 3.12)
- `arbiter-governance` (Python 3.12)
- `coverage-matrix-validate` (Python 3.12, advisory)
- `ci` (aggregation job)

### Adding New Repos

When adding a new repo to internal git server CI:

1. **Determine required labels** based on job requirements
2. **Configure runners** with necessary labels
3. **Use dual-label strategy** in workflow files
4. **Test on both platforms** if GitHub mirror exists
5. **Document label requirements** in repo-specific runbook

## Maintenance

### Weekly Tasks
- Review runner status in internal git server UI
- Check runner logs for errors or warnings
- Verify runner labels match workflow requirements
- Monitor disk space on runner hosts

### Monthly Tasks
- Update act_runner binary to latest version
- Review and rotate runner tokens
- Audit runner labels for consistency
- Update this runbook with any process changes

### Quarterly Tasks
- Review runner capacity and utilization
- Plan runner expansion if needed
- Audit security settings and access controls
- Test disaster recovery procedures

## Emergency Procedures

### Runner Host Failure

If a runner host becomes unavailable:

1. **Identify affected repos** (check internal git server UI for queued jobs)
2. **Redirect jobs** to available runners by updating workflow labels
3. **Bring up replacement runner** on alternative host if possible
4. **Document incident** in fleet status log

### Internal Git Server Failure

If internal git server becomes unavailable:

1. **Check internal git server service status** on Anvil
2. **Restart internal git server service** if needed
3. **Verify database integrity**
4. **Check Tailscale Serve configuration** if remote access fails
5. **Fallback to GitHub** for critical CI if needed

### Security Incident

If runner compromise is suspected:

1. **Immediately disable affected runners** in internal git server UI
2. **Rotate all runner tokens**
3. **Audit recent job executions** for suspicious activity
4. **Scan runner hosts** for malware or unauthorized access
5. **Rebuild runners** from clean images if compromise confirmed

## References

- Internal git server Actions Documentation: https://docs.gitea.com/usage/actions/overview
- act_runner GitHub: https://github.com/gitea/act_runner
- Fleet Status: `PROJECTS/hummbl-governance/AGENTS.md` (mesh section)
- CI/CD Architecture Plan: `PROJECTS/hummbl-governance/docs/ci-cd-architecture-plan.md`

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2026-05-29 | Initial runbook creation | Devin |
