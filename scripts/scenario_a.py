import asyncio
import httpx
from collections import Counter

API_URL = "http://localhost:8000"
SEAT_ID = 1

async def attempt_hold(client, user_id):
    try:
        response = await client.post(f"{API_URL}/seats/{SEAT_ID}/hold", json={
            "user_id": f"user_{user_id}",
            "phone": "01700000000"
        }, timeout=5.0)
        return response.status_code
    except Exception as e:
        return 500

async def main():
    print("Scenario A: Concurrency Burst")
    print(f"Simulating 100 users trying to hold Seat {SEAT_ID} at the exact same moment...")
    
    async with httpx.AsyncClient() as client:
        tasks = [attempt_hold(client, i) for i in range(100)]
        results = await asyncio.gather(*tasks)
        
        counts = Counter(results)
        print("\nResults:")
        print(f"200 OK (Success): {counts.get(200, 0)}")
        print(f"409 Conflict (Already taken or processing): {counts.get(409, 0)}")
        print(f"Other errors: {sum(v for k, v in counts.items() if k not in (200, 409))}")
        
        if counts.get(200, 0) == 1:
            print("\n✅ SUCCESS: Exactly one user got the seat.")
        else:
            print("\n❌ FAILURE: Multiple users got the seat or nobody got it!")

if __name__ == "__main__":
    asyncio.run(main())
