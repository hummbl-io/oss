# UpCloud Account Data (verified 2026-08-19)

| Field | Value |
|-------|-------|
| **Verified** | 2026-08-19 via UpCloud API v1.3 |
| **API key** | 1Password item `HUMMBL-UPCLOUD-API-KEY` (id `imnhxfqtwa7wpatigaywmvj6xe`) |
| **Auth method** | Bearer token (`Authorization: Bearer <key>`) |
| **API base** | `https://api.upcloud.com/1.3` |

---

## Account

| Field | Value |
|-------|-------|
| Username | hummbl |
| Credits | 50,000 |

## Trial Resource Limits

| Resource | Limit |
|----------|-------|
| CPU cores (total) | 6 |
| RAM (total) | 12,288 MB (12 GB) |
| Public IPv4 | 2 |
| Public IPv6 | 3 |
| Detached floating IPs | 3 |
| Storage HDD | 10,240 GB (10 TB) |
| Storage MaxIOPS | 10,240 GB (10 TB) |
| Storage SSD | 10,240 GB (10 TB) |
| Storage standard | 10,240 GB (10 TB) |
| Storage total | 1,024 GB |
| Networks | 3 |
| Network peerings | 5 |
| Network gateways | 1 |
| Network gateways (essentials) | 1 |
| Routers | 100 |
| Server groups | 200 |
| Tags | 200 |
| Firewall rules | null (unlimited) |
| Load balancers | 1 |
| Load balancers (essentials) | 1 |
| Managed databases | 1 |
| Managed databases (dev) | 1 |
| Managed Kubernetes | 1 |
| Managed object storages | 1 |
| File storages | 1 |
| CDNs | 1 |
| GPUs | 0 |
| Detached interfaces | 1 |

## Zones (15)

| Zone ID | Description |
|---------|-------------|
| us-chi1 | Chicago #1 |
| us-nyc1 | New York #1 |
| us-sjo1 | San Jose #1 |
| uk-lon1 | London #1 |
| de-fra1 | Frankfurt #1 |
| nl-ams1 | Amsterdam #1 |
| fi-hel1 | Helsinki #1 |
| fi-hel2 | Helsinki #2 |
| dk-cph1 | Copenhagen #1 |
| es-mad1 | Madrid #1 |
| pl-waw1 | Warsaw #1 |
| se-sto1 | Stockholm #1 |
| no-svg1 | Stavanger #1 |
| au-syd1 | Sydney #1 |
| sg-sin1 | Singapore #1 |

## Server Plan Pricing (us-chi1, verified from `/price` API)

### General Purpose (MaxIOPS storage included)

| Plan | CPU | RAM | Disk | Price/mo |
|------|-----|-----|------|----------|
| 1xCPU-1GB | 1 | 1 GB | 25 GB | $0.97 |
| 1xCPU-2GB | 1 | 2 GB | 50 GB | $1.93 |
| 2xCPU-2GB | 2 | 2 GB | 80 GB | $2.90 |
| 2xCPU-4GB | 2 | 4 GB | 80 GB | $3.87 |
| 4xCPU-8GB | 4 | 8 GB | 160 GB | $7.74 |
| 6xCPU-16GB | 6 | 16 GB | 240 GB | $18.01 |
| 8xCPU-32GB | 8 | 32 GB | 320 GB | $35.42 |
| 12xCPU-48GB | 12 | 48 GB | 480 GB | $53.27 |
| 16xCPU-64GB | 16 | 64 GB | 640 GB | $70.83 |
| 24xCPU-96GB | 24 | 96 GB | 960 GB | $106.25 |
| 32xCPU-128GB | 32 | 128 GB | 1280 GB | $141.67 |
| 38xCPU-192GB | 38 | 192 GB | 1920 GB | $188.10 |
| 48xCPU-256GB | 48 | 256 GB | 2560 GB | $250.89 |
| 64xCPU-384GB | 64 | 384 GB | 3840 GB | $352.38 |
| 80xCPU-512GB | 80 | 512 GB | 5120 GB | $467.86 |

### Developer (cheapest, standard storage)

| Plan | CPU | RAM | Disk | Price/mo |
|------|-----|-----|------|----------|
| DEV-1xCPU-1GB-10GB | 1 | 1 GB | 10 GB | $0.52 |
| DEV-1xCPU-1GB | 1 | 1 GB | 20 GB | $0.82 |
| DEV-1xCPU-2GB | 1 | 2 GB | 30 GB | $1.41 |
| DEV-1xCPU-4GB | 1 | 4 GB | 40 GB | $2.68 |
| DEV-2xCPU-4GB | 2 | 4 GB | 40 GB | $3.13 |
| DEV-2xCPU-8GB | 2 | 8 GB | 80 GB | $4.32 |
| DEV-2xCPU-16GB | 2 | 16 GB | 80 GB | $5.95 |

### Cloud Native (no included storage, for K8s)

| Plan | CPU | RAM | Price/mo |
|------|-----|-----|----------|
| CLOUDNATIVE-1xCPU-4GB | 1 | 4 GB | $2.08 |
| CLOUDNATIVE-1xCPU-8GB | 1 | 8 GB | $3.42 |
| CLOUDNATIVE-2xCPU-4GB | 2 | 4 GB | $2.68 |
| CLOUDNATIVE-2xCPU-8GB | 2 | 8 GB | $4.17 |
| CLOUDNATIVE-4xCPU-8GB | 4 | 8 GB | $5.51 |
| CLOUDNATIVE-4xCPU-16GB | 4 | 16 GB | $11.61 |

### GPU Plans (post-trial)

| Plan | CPU | RAM | GPU | Price/mo |
|------|-----|-----|-----|----------|
| GPU-8xCPU-64GB-1xL4 | 8 | 64 GB | 1x L4 | $69.00 |
| GPU-12xCPU-128GB-1xL4 | 12 | 128 GB | 1x L4 | $83.00 |
| GPU-12xCPU-128GB-1xL40S | 12 | 128 GB | 1x L40S | $142.50 |
| GPU-12xCPU-240GB-1xH100 | 12 | 240 GB | 1x H100 | $189.00 |
| GPU-16xCPU-192GB-1xL40S | 16 | 192 GB | 1x L40S | $174.22 |
| GPU-24xCPU-480GB-2xH100 | 24 | 480 GB | 2x H100 | $378.00 |
| GPU-24xCPU-240GB-1xB200 | 24 | 240 GB | 1x B200 | $520.00 |
| GPU-48xCPU-960GB-4xH100 | 48 | 960 GB | 4x H100 | $756.00 |
| GPU-48xCPU-480GB-2xB200 | 48 | 480 GB | 2x B200 | $1,040.00 |
| GPU-96xCPU-1920GB-8xH100 | 96 | 1,920 GB | 8x H100 | $1,512.00 |
| GPU-192xCPU-1920GB-8xB200 | 192 | 1,920 GB | 8x B200 | $4,160.00 |

### GPU Spot Plans (cheaper, preemptible)

| Plan | Price/mo |
|------|----------|
| GPU-SPOT-8xCPU-64GB-1xL4 | $69.00 |
| GPU-SPOT-12xCPU-128GB-1xL4 | $82.00 |
| GPU-SPOT-12xCPU-128GB-1xL40S | $107.00 |
| GPU-SPOT-12xCPU-240GB-1xH100 | $188.00 |
| GPU-SPOT-24xCPU-480GB-2xH100 | $377.00 |

## Managed Database Pricing (us-chi1)

| Plan | Nodes | CPU | RAM | Storage | Price/mo |
|------|-------|-----|-----|---------|----------|
| 1x1xCPU-1GB-10GB | 1 | 1 | 1 GB | 10 GB | $1.11 |
| 1x1xCPU-2GB-25GB | 1 | 1 | 2 GB | 25 GB | $4.17 |
| 1x2xCPU-4GB-50GB | 1 | 2 | 4 GB | 50 GB | $8.33 |
| 1x2xCPU-4GB-100GB | 1 | 2 | 4 GB | 100 GB | $10.42 |
| 2x2xCPU-4GB-50GB | 2 | 2 | 4 GB | 50 GB | $16.67 |
| 2x2xCPU-4GB-100GB | 2 | 2 | 4 GB | 100 GB | $25.00 |
| 2x4xCPU-8GB-50GB | 2 | 4 | 8 GB | 50 GB | $27.78 |
| 2x4xCPU-8GB-100GB | 2 | 4 | 8 GB | 100 GB | $31.94 |
| 2x6xCPU-16GB-100GB | 2 | 6 | 16 GB | 100 GB | $63.89 |
| 2x8xCPU-32GB-100GB | 2 | 8 | 32 GB | 100 GB | $119.44 |

## Other Pricing

| Resource | Price/mo |
|----------|----------|
| IPv4 address | $0.53 |
| IPv6 address | $0.00 (free) |
| Public egress | $0.00 (zero-cost, Fair Transfer Policy) |
| Public ingress | $0.00 |
| Private egress | $0.00 |
| Private ingress | $0.00 |
| Firewall | $0.00 (free) |
| SDN Private Network | $0.00 (free) |
| SDN Router | $0.00 (free) |
| File storage (1 GB) | $0.02 |
| Server core (ala carte) | $1.32 |
| Server memory (ala carte) | $0.17 |

## Egress / Fair Transfer Policy

UpCloud has **zero-cost egress**. Each server plan includes a fair
transfer quota:

| Plan tier | Included egress |
|-----------|----------------|
| DEV-1xCPU-1GB | 1 TB |
| 1xCPU-1GB (Premium) | 0.5 TB |
| 1xCPU-2GB (Premium) | 1 TB |
| 2xCPU-4GB (Premium) | 3 TB |
| 4xCPU-8GB (Premium) | 5 TB |
| CLOUDNATIVE plans | 1-100 TB |

If the fair transfer limit is exceeded: **no excess fees** — bandwidth is
throttled to 100 Mbps for the remainder of the month. Optional unlimited
egress at $0.01/GB.

Source: https://upcloud.com/docs/products/networking/billing/

## OS Templates (41 total, Linux subset shown)

| Template | Size | Zone |
|----------|------|------|
| Ubuntu Server 26.04 LTS | 10 GB | any |
| Ubuntu Server 24.04 LTS | 10 GB | any |
| Ubuntu Server 24.04 LTS (NVIDIA drivers & CUDA) | 20 GB | any |
| Ubuntu Server 22.04 LTS | 10 GB | any |
| Debian GNU/Linux 13 (Trixie) | 10 GB | any |
| Debian GNU/Linux 12 (Bookworm) | 10 GB | any |
| Debian GNU/Linux 11 (Bullseye) | 3 GB | any |
| Fedora 43 | 10 GB | any |
| Fedora 42 | 10 GB | any |
| CentOS Stream 10 | 10 GB | any |
| CentOS Stream 9 | 5 GB | any |
| Rocky Linux 10 | 10 GB | any |
| Rocky Linux 9 | 10 GB | any |
| AlmaLinux 10 | 10 GB | any |
| AlmaLinux 9 | 10 GB | any |
| AlmaLinux 8 | 5 GB | any |

## Existing Resources

| Resource | Count | Notes |
|----------|-------|-------|
| Servers | 0 | Fresh account |
| Storage devices | 79 | Pre-existing templates |
| Networks | 252 | UpCloud's pre-configured public/private networks per zone |

## API Authentication Notes

- The API key prefix format is `ucat_<25-char-token>` (31 chars total). [REDACTED 2026-08-21: the original text here contained a live captured key value, not just a format description — see 1password-rotation-imnhxfqt operator-queue item.]
- Auth method: **Bearer token** in `Authorization` header.
- HTTP Basic Auth with the key as username does **not** work (returns 401
  AUTHENTICATION_FAILED).
- The 1Password item also has a `username` field set to `hummbl`, but
  this is not used for API auth — only the Bearer token is needed.
