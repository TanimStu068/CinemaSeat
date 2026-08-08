# Architecture Decisions

## 1. Concurrency Control
We used **Pessimistic Locking (`SELECT ... FOR UPDATE NOWAIT`)** to handle concurrent seat requests. 
- **Why?** Optimistic locking would result in 99 database retries for 100 users trying to book the same seat. Pessimistic locking with `NOWAIT` immediately rejects the 99 losers with a `409 Conflict`, avoiding the thundering herd problem entirely.

## 2. Idempotency & Webhooks
The mock gateway is unreliable and may send duplicate webhooks.
- We used **Redis `SETNX`** with an 86400 TTL to ensure each webhook event is processed exactly once based on the `event_id`.

## 3. Webhook Race Conditions
Sometimes the webhook arrives *before* the initial `/charge` POST request finishes writing the `booking_ref` and `payment_id` to the database.
- We implemented a **retry loop** in the webhook handler. If the booking is not found, the handler waits 0.5s and retries up to 6 times before giving up.

## 4. Fault Isolation
The `api` container explicitly does **NOT** depend on the `gateway` container. 
- **Why?** If the gateway goes down (which is expected during testing), the API must still be able to serve the browsing endpoints and return a `200 OK` for `/health`. 

## 5. Deployment Strategy
Our CI/CD pipeline runs `docker compose up -d --build --no-deps api frontend`.
- This ensures rolling updates. The database, redis, and gateway containers are untouched, preserving state and preventing downtime of the core infrastructure.
