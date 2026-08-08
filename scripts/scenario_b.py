import asyncio
import httpx
import os

API_URL = "http://localhost:8000"
# For this script to run quickly, we should run the server with HOLD_TTL_SECONDS=5
SEAT_ID = 2

async def main():
    print("Scenario B: Expiry and Rebook")
    
    # 1. Alice holds the seat
    print("Alice is holding the seat...")
    async with httpx.AsyncClient() as client:
        res1 = await client.post(f"{API_URL}/seats/{SEAT_ID}/hold", json={
            "user_id": "alice",
            "phone": "01711111111"
        })
        
        if res1.status_code == 200:
            ref = res1.json().get("booking_ref")
            print(f"Alice held the seat. Booking Ref: {ref}")
        else:
            print("Failed to hold seat.")
            return

        # 2. Wait for hold to expire
        ttl = int(os.getenv("HOLD_TTL_SECONDS", "300"))
        wait_time = ttl + 2 # wait a bit longer for the worker to run
        print(f"Waiting {wait_time} seconds for hold to expire...")
        
        # We poll the status
        for _ in range(wait_time // 2):
            await asyncio.sleep(2)
            print("Checking status...")
            b_res = await client.get(f"{API_URL}/booking/{ref}/status")
            status = b_res.json().get("status")
            print(f"Alice booking status: {status}")
            if status == "FAILED":
                break
                
        # 3. Bob holds the seat
        print("\nBob is trying to hold the same seat now...")
        res2 = await client.post(f"{API_URL}/seats/{SEAT_ID}/hold", json={
            "user_id": "bob",
            "phone": "01722222222"
        })
        
        if res2.status_code == 200:
            print(f"✅ SUCCESS: Bob successfully held the seat. Booking Ref: {res2.json().get('booking_ref')}")
        else:
            print(f"❌ FAILURE: Bob couldn't hold the seat. Status: {res2.status_code}")
            
if __name__ == "__main__":
    asyncio.run(main())
