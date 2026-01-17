# API Reference

Base URL: `http://localhost:8000/api/v1`

---

## Authentication

### Register
```http
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "full_name": "John Doe",
  "password": "securepass123"
}
```

### Login
```http
POST /auth/login?email=user@example.com&password=securepass123
```

Response:
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

### Get Profile
```http
GET /auth/me
Authorization: Bearer <token>
```

---

## Wallet

### Get Balance
```http
GET /wallet/balance
Authorization: Bearer <token>
```

### Top Up
```http
POST /wallet/topup
Authorization: Bearer <token>
Content-Type: application/json

{
  "amount": 50.00,
  "payment_reference": "STRIPE-123"
}
```

### Transaction History
```http
GET /wallet/transactions?page=1&page_size=20
Authorization: Bearer <token>
```

---

## Jobs

### Submit Job
```http
POST /jobs/
Authorization: Bearer <token>
Content-Type: multipart/form-data

script_file: <train.py>
dataset_file: <data.zip> (optional)
job_data: {
  "script_name": "train.py",
  "docker_image": "nvidia/cuda:12.1-runtime-ubuntu22.04",
  "resource_config": {
    "memory_limit": "8g",
    "cpu_count": 4,
    "timeout_seconds": 3600
  }
}
```

### List Jobs
```http
GET /jobs/?status_filter=running&limit=10
Authorization: Bearer <token>
```

### Get Job Details
```http
GET /jobs/{job_id}
Authorization: Bearer <token>
```

### Cancel Job
```http
POST /jobs/{job_id}/cancel
Authorization: Bearer <token>
```

### Get Logs
```http
GET /jobs/{job_id}/logs
Authorization: Bearer <token>
```

### List Outputs
```http
GET /jobs/{job_id}/outputs
Authorization: Bearer <token>
```

---

## Job Statuses

| Status | Description |
|--------|-------------|
| `pending` | Queued, waiting for worker |
| `preparing` | Worker preparing container |
| `running` | Executing on GPU |
| `completed` | Finished successfully |
| `failed` | Error occurred |
| `cancelled` | User cancelled |
| `killed_no_credits` | Stopped due to insufficient credits |
