# Mission Mode Fleet Hybrid Deployment

## Fleet Architecture

Mission Mode operates across a hybrid fleet of two machines:

### Nodezero (Primary Compute)
- **Hardware**: Mac Mini M4 Pro (48GB RAM)
- **Role**: Primary inference host, long-context reasoning, document synthesis
- **Services**: Ollama hub, CI runner, canonical coordination bus
- **Models**: `nemotron-3-nano:30b` (1M ctx), `qwen3.5:9b` (general chat), `qwen2.5-coder:3b` (fast-code)
- **Network**: Tailscale IP `100.x.x.x` (maks-mac-mini-1)
- **SSH**: `ssh nodezero` (logs in as `nodezero` user)

### Anvil (GPU/Compliance)
- **Hardware**: Windows 11 desktop, AMD Ryzen 7 5800X, RTX 3080 Ti (12GB VRAM)
- **Role**: GPU workloads, evidence storage, audit trail database, Gitea server
- **Services**: Gitea, PostgreSQL, S3/MinIO, Ollama (secondary)
- **GPU Config**: 270W cap + locked 1800 MHz GPU clock
- **Network**: Tailscale IP `100.x.x.x` (anvil)
- **Primary Dev**: This is the primary development machine

## Fleet Coordination Protocol

### Task Routing Rules

```python
TASK_ROUTING = {
    "inference": "nodezero",           # M4 Pro for reasoning
    "file_ops": "anvil",              # Anvil for file operations
    "gpu_workload": "anvil",          # RTX 3080 Ti for GPU
    "document_generation": "nodezero", # M4 Pro for synthesis
    "database_ops": "anvil",          # Anvil for database
    "storage_ops": "anvil",           # Anvil for storage
    "compliance_validation": "nodezero", # M4 Pro for analysis
    "evidence_collection": "anvil",   # Anvil for file access
    "report_generation": "nodezero",  # M4 Pro for document synthesis
    "audit_trail_storage": "anvil"   # Anvil for database operations
}
```

### Health Monitoring

```python
HEALTH_CHECK_INTERVAL = 30  # seconds

FLEET_HEALTH_ENDPOINTS = {
    "nodezero": {
        "ollama": "http://100.x.x.x:11434/api/tags",
        "bus": "http://100.x.x.x:18790/health"
    },
    "anvil": {
        "gitea": "https://<fleet-node>.ts.net",
        "ollama": "http://localhost:11434/api/tags"
    }
}
```

### Fallback Strategy

1. **Primary Unhealthy**: If primary compute (nodezero) is unhealthy, route to fallback (anvil)
2. **GPU Unhealthy**: If GPU compute (anvil) is unhealthy, disable GPU workloads
3. **Both Unhealthy**: Block mission execution with BLOCKED status
4. **Recovery**: Health checks every 30 seconds; auto-recover when node becomes healthy

## Deployment Modes

### Local Mode (Anvil-only)
- **Use Case**: Development, testing, offline operation
- **Configuration**: All tasks execute on Anvil
- **Limitations**: No long-context inference, reduced GPU capacity
- **Activation**: Set `FLEET_MODE=local` in environment

### Hybrid Mode (Default)
- **Use Case**: Production mission execution
- **Configuration**: Tasks routed based on type and fleet health
- **Capabilities**: Full inference, GPU workloads, compliance workflows
- **Activation**: Default mode, no configuration required

### Nodezero-Only Mode
- **Use Case**: GPU-intensive workloads, compliance validation
- **Configuration**: All tasks execute on nodezero
- **Limitations**: No GPU workloads, limited file operations
- **Activation**: Set `FLEET_MODE=nodezero` in environment

## Service Discovery

### Ollama Model Discovery
```bash
# Check nodezero models
curl -s http://100.x.x.x:11434/api/tags | python -m json.tool

# Check Anvil models
curl -s http://localhost:11434/api/tags | python -m json.tool
```

### Gitea Repository Discovery
```bash
# List Gitea repos
gh -H "Authorization: token $GITEA_TOKEN" api https://<fleet-node>.ts.net/api/v1/repos/search
```

### Bus Discovery
```bash
# Check bus health
curl -s http://100.x.x.x:18790/health
```

## Data Synchronization

### Audit Trail Synchronization
- **Primary Storage**: Anvil PostgreSQL
- **Backup**: Nodezero daily snapshot
- **Sync Interval**: Every 5 minutes during active missions
- **Conflict Resolution**: Last-write-wins with audit trail versioning

### Evidence Artifact Synchronization
- **Primary Storage**: Anvil S3/MinIO
- **Backup**: Nodezero weekly snapshot
- **Sync Interval**: On-demand during evidence collection
- **Integrity Check**: SHA-256 hash verification on sync

### Workflow State Synchronization
- **Primary Storage**: Anvil Gitea (kernel/workflows/)
- **Backup**: Nodezero daily snapshot
- **Sync Interval**: On workflow update
- **Conflict Resolution**: Git-based with manual resolution

## Security Considerations

### Network Security
- **Tailscale VPN**: All fleet communication over Tailscale
- **Firewall Rules**: Only Tailscale IPs allowed for inter-machine communication
- **Service Binding**: All services bind to 127.0.0.1 or Tailscale IPs only

### Authentication
- **SSH Keys**: Key-based authentication for all SSH access
- **Gitea Tokens**: Personal access tokens for API access
- **Bus Token**: Shared token for coordination bus access

### Data Encryption
- **At Rest**: AES-256 encryption for sensitive data
- **In Transit**: TLS 1.3 for all network communication
- **Key Management**: Hardware security module (HSM) for production

## Deployment Checklist

### Initial Setup
- [ ] Verify Tailscale connectivity between nodezero and Anvil
- [ ] Configure SSH keys for passwordless login
- [ ] Install Ollama on both machines
- [ ] Configure Gitea on Anvil
- [ ] Set up PostgreSQL on Anvil
- [ ] Configure S3/MinIO on Anvil
- [ ] Test health check endpoints
- [ ] Verify task routing rules
- [ ] Test fallback strategy
- [ ] Configure data synchronization

### Ongoing Operations
- [ ] Monitor fleet health every 30 seconds
- [ ] Sync audit trail every 5 minutes during active missions
- [ ] Backup evidence artifacts weekly
- [ ] Rotate SSH keys quarterly
- [ ] Rotate Gitea tokens quarterly
- [ ] Update fleet configuration as needed
- [ ] Monitor disk space on both machines
- [ ] Monitor GPU temperature on Anvil
- [ ] Monitor memory usage on nodezero

## Troubleshooting

### Nodezero Unreachable
```bash
# Check Tailscale status
tailscale status

# Check SSH connectivity
ssh nodezero echo "connected"

# Check Ollama endpoint
curl -s http://100.x.x.x:11434/api/tags
```

### Anvil GPU Issues
```bash
# Check GPU status
nvidia-smi

# Check GPU temperature
nvidia-smi --query-gpu=temperature.gpu --format=csv

# Check GPU power cap
nvidia-smi --query-gpu=power.limit --format=csv
```

### Gitea Unreachable
```bash
# Check Gitea service
powershell -Command "Get-Service Gitea"

# Check Gitea endpoint
curl -s https://<fleet-node>.ts.net

# Check Gitea logs
cat C:/gitea/data/gitea.log
```

### Database Issues
```bash
# Check PostgreSQL service
powershell -Command "Get-Service postgresql-x64-16"

# Check database connectivity
psql -h localhost -U postgres -d mission_mode -c "SELECT 1"

# Check database size
psql -h localhost -U postgres -d mission_mode -c "SELECT pg_size_pretty(pg_database_size('mission_mode'));"
```

## Performance Optimization

### Nodezero Optimization
- **Model Selection**: Use appropriate model for task complexity
- **Batch Processing**: Batch similar tasks to reduce model loading overhead
- **Context Window**: Use 1M context only when necessary
- **KV Cache**: Enable KV cache quantization for memory efficiency

### Anvil Optimization
- **GPU Clock**: Maintain 1800 MHz locked clock for stability
- **Power Cap**: Use 270W cap for thermal management
- **Storage**: Use SSD for evidence artifact storage
- **Database**: Configure PostgreSQL for audit trail workload

### Network Optimization
- **Compression**: Enable compression for large data transfers
- **Caching**: Cache frequently accessed data locally
- **Connection Pooling**: Use connection pooling for database access
- **Async Operations**: Use async I/O for network operations

## Monitoring

### Metrics to Monitor
- Fleet health status
- Task execution time per machine
- GPU utilization on Anvil
- Memory usage on nodezero
- Disk space on both machines
- Network latency between machines
- Audit trail size and growth rate
- Evidence artifact count and size
- Database query performance

### Alerting Thresholds
- Fleet health: Alert if any machine unhealthy for > 5 minutes
- GPU temperature: Alert if > 85°C
- Memory usage: Alert if > 90%
- Disk space: Alert if < 10% free
- Network latency: Alert if > 100ms
- Database query time: Alert if > 5s

## Future Enhancements

### Planned Features
- **Automatic Failover**: Automatic task rerouting on node failure
- **Load Balancing**: Distribute tasks based on current load
- **Dynamic Scaling**: Add/remove machines based on workload
- **Machine Learning**: Predict optimal task routing based on historical data
- **Enhanced Monitoring**: Real-time dashboard for fleet status
- **Automated Recovery**: Automatic recovery from common failures

### Research Areas
- **Multi-Model Orchestration**: Optimize model selection per task
- **Federated Learning**: Train models across fleet
- **Edge Computing**: Deploy to edge devices
- **Quantum Computing**: Explore quantum computing integration