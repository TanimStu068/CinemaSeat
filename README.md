# Team Antigravity: CinemaSeat

This repository contains the backend and frontend for the CinemaSeat ticketing application.

## Prerequisites
- Docker & Docker Compose
- Node.js (for local frontend dev)
- Python 3.11 (for running scripts)

## Running Locally
From the root of the repository, run:
```bash
docker compose up
```
This single command spins up:
1. `db`: PostgreSQL 16
2. `redis`: Redis 7
3. `gateway`: Mock Payment/OTP Gateway
4. `api`: FastAPI Backend (port 8000)
5. `frontend`: React Frontend (port 3000)

The API will automatically run database migrations and seed initial data.

## Proof Scripts
To prove the system handles race conditions and hold expiries, we have provided two python scripts.
Before running them, make sure to install their dependencies:
```bash
pip install httpx
```

**Scenario A: Concurrency (The Thundering Herd)**
Simulates 100 users attempting to book the exact same seat simultaneously.
```bash
python scripts/scenario_a.py
```
*Expected: Exactly one 200 OK, 99 409 Conflicts.*

**Scenario B: Expiry and Rebook**
Shows a user holding a seat, the hold expiring (based on `HOLD_TTL_SECONDS`), and another user successfully booking it.
```bash
python scripts/scenario_b.py
```
