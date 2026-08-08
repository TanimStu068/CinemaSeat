# Architectural Decisions & Team Trade-offs

This document outlines the three major architectural decisions our engineering team debated during the development of CinemaSeat, detailing the options considered, the chosen solution, the rationale, and the specific trade-offs accepted.

---

## Decision 1: Concurrency Control Strategy for High Seat Contention

### Context & Problem Statement
During high-demand ticket sales, hundreds of users click "Hold Seat" on the exact same seat within a single millisecond. The system must guarantee zero double-bookings without causing database transaction deadlocks or performance degradation.

### Options Considered
1. **Optimistic Concurrency Control (OCC):** Use version numbers on seats. Read seat state, execute update with `WHERE version = old_version`. If update count is 0, retry.
2. **Distributed Locks (Redis Redlock):** Acquire a Redis key lock per `seat_id` before querying PostgreSQL.
3. **Pessimistic Row Locking (`SELECT ... FOR UPDATE NOWAIT`):** Lock the targeted database row immediately during seat lookup inside a transaction, failing fast if the lock is held.

### Chosen Solution
**Option 3: Pessimistic Row Locking (`SELECT ... FOR UPDATE NOWAIT`)** directly at the PostgreSQL layer.

### Rationale
* Under a burst of 100 simultaneous requests for one seat, Optimistic Locking results in massive retry loops (99 retries for 1 winner), swamping the API workers and DB CPU.
* Redis distributed locks introduce dual-system synchronization risk (a seat could be locked in Redis but fail to write in Postgres) and extra network roundtrips.
* PostgreSQL `SELECT ... FOR UPDATE NOWAIT` attempts to lock the seat row instantly. The winning request acquires the lock in < 1ms, updates seat status to `HELD`, creates the booking, and commits. The remaining 99 requests hit `NOWAIT` immediately, raising a DB `LockNotAvailable` exception that FastAPI instantly returns as an **HTTP 409 Conflict** with zero DB wait time.

### Trade-offs & What We Gave Up
* **Gave Up:** We gave up long-held transactions. DB locks are held only for the fraction of a millisecond during the `POST /seats/{id}/hold` request handler, not across the 60-second user checkout session.

---

## Decision 2: Architecture for 60-Second Seat Hold Expiration

### Context & Problem Statement
When a seat is held, the user has 60 seconds to complete phone OTP verification and payment processing. If they abandon the checkout or run out of time, the seat must automatically revert to `AVAILABLE`.

### Options Considered
1. **Heavy Distributed Task Queue (Celery + RabbitMQ / Redis):** Schedule delayed worker tasks 60 seconds into the future.
2. **Redis Keyspace Expiration Notifications:** Set a Redis key with `EXPIRE 60`, listen to expired events via Pub/Sub to release the seat.
3. **Async Background Worker (`asyncio.create_task` + DB Verification) & Scheduled Recovery Sweeper:** Spawn an async background task within the FastAPI process upon hold creation, combined with periodic DB status reconciliation.

### Chosen Solution
**Option 3: Async Background Worker (`asyncio.create_task`) paired with DB Status Verification.**

### Rationale
* Celery + RabbitMQ introduces heavy infrastructure overhead (2 additional containers, message broker daemons) for simple 60-second memory timers.
* Redis Keyspace notifications are pub/sub messages that are not guaranteed to deliver if the listener container briefly disconnects.
* `asyncio.create_task` within Python's event loop executes `asyncio.sleep(60)` asynchronously without blocking any HTTP threads. After 60 seconds, it queries the booking status: if still `PENDING` or `OTP_SENT`, it atomically frees the seat in PostgreSQL.

### Trade-offs & What We Gave Up
* **Gave Up:** In-memory `asyncio` tasks do not survive an abrupt API container crash/kill during an active 60s hold. We mitigated this by running an database startup sweep and periodic APScheduler checks to clean up orphaned expired holds.

---

## Decision 3: Frontend API URL Configuration & Host Resolution

### Context & Problem Statement
The React frontend (built with Vite) needs to communicate with the FastAPI backend. The app must run seamlessly both locally (`http://localhost:8000`) and deployed on AWS EC2 (`http://13.214.33.207:8000`) without requiring manual code changes or container rebuilds per environment.

### Options Considered
1. **Static Build-time Envs (`VITE_API_URL`):** Embed the API URL into JavaScript static bundle during `npm run build`.
2. **Reverse Proxy (Nginx Container):** Route `/api` requests through Nginx to the backend container on port 80.
3. **Explicit Public Fallback & Protocol Sanitization (`http://13.214.33.207:8000`):** Define the production server address explicitly while allowing environment variable overrides.

### Chosen Solution
**Option 3: Explicit Public Fallback (`http://13.214.33.207:8000`) with Protocol Sanitization.**

### Rationale
* Static build-time environment variables in Vite break when containerized because environment variables are evaluated at image build time, not runtime in the browser.
* Nginx reverse proxies add unnecessary container overhead for this evaluation setup.
* Explicitly providing the AWS server IP `http://13.214.33.207:8000` with fallback sanitization ensures that the browser always constructs full `http://` URLs (preventing relative `:8000/movies` errors) across both local development and AWS GitHub Actions deployments.

### Trade-offs & What We Gave Up
* **Gave Up:** Domain name abstraction. The frontend connects directly to port `8000` on the server IP rather than routed through a unified port 80/443 reverse proxy domain.
