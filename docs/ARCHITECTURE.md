# Home-GPU-Cloud Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        LOCAL AREA NETWORK                           │
├─────────────────┬─────────────────────┬─────────────────────────────┤
│   NODO A        │   NODO B            │   NODO C                    │
│   Controller    │   NAS/Storage       │   GPU Worker                │
│                 │                     │                             │
│ ┌─────────────┐ │ ┌─────────────────┐ │ ┌─────────────────────────┐ │
│ │  FastAPI    │ │ │   NFS Server    │ │ │   Celery Worker         │ │
│ │  Backend    │ │ │ /srv/nfs/shared │ │ │   (single concurrency)  │ │
│ └──────┬──────┘ │ └────────┬────────┘ │ └───────────┬─────────────┘ │
│        │        │          │          │             │               │
│ ┌──────┴──────┐ │          │          │ ┌───────────┴─────────────┐ │
│ │ PostgreSQL  │ │          │          │ │   Docker + NVIDIA       │ │
│ │ Redis       │ │          │          │ │   Container Toolkit     │ │
│ └─────────────┘ │          │          │ └───────────┬─────────────┘ │
│                 │          │          │             │               │
│                 │          └──NFS────►│   /mnt/home-gpu-cloud      │
│                 │           mount     │             │               │
│                 │                     │     ┌───────┴───────┐       │
│                 │                     │     │   GPU         │       │
│                 │                     │     │   (NVIDIA)    │       │
│                 │                     │     └───────────────┘       │
└─────────────────┴─────────────────────┴─────────────────────────────┘
```

## Data Flow

1. **User uploads script + dataset** → FastAPI receives multipart upload
2. **Files stored on NFS** → `/srv/nfs/shared/jobs/{job_id}/input/`
3. **Job created in PostgreSQL** → status = `pending`
4. **Task queued to Redis** → Celery task with job metadata
5. **Worker picks up task** → consumes from `gpu_jobs` queue
6. **Worker reads files via NFS mount** → `/mnt/home-gpu-cloud/jobs/{job_id}/`
7. **Docker container launched** → nvidia runtime, resource limits
8. **Billing heartbeat every 60s** → backend debits credits
9. **Kill switch if credits ≤ 0** → container stopped immediately
10. **Results written to NFS** → `/mnt/home-gpu-cloud/jobs/{job_id}/output/`
11. **User downloads results** → via API

## Security Model

| Layer | Protection |
|-------|------------|
| Container | No network, resource limits, capability drop |
| Docker | Read-only input mount, no privilege escalation |
| NFS | Quota per user directory |
| API | JWT authentication, worker secret |
| Billing | Optimistic locking, atomic transactions |
