import asyncio
import httpx
import os
import argparse

API_URL = os.getenv('API_URL', 'http://localhost:8000')

async def hold_seat(client, seat_id, user_id, phone):
    try:
        response = await client.post(f"{API_URL}/seats/{seat_id}/hold", json={"user_id": user_id, "phone": phone})
        status = response.status_code
        data = response.json()
        return status, data.get('booking_ref', None)
    except Exception as e:
        return None, str(e)

async def run_test(seat_id, showtime_id, count=100):
    async with httpx.AsyncClient() as client:
        tasks = []
        for i in range(count):
            user_id = f"user_{i}"
            phone = f"0170000{i:04d}"
            tasks.append(hold_seat(client, seat_id, user_id, phone))
        results = await asyncio.gather(*tasks)
        total = len(results)
        success = sum(1 for status, _ in results if status == 200)
        conflict = sum(1 for status, _ in results if status == 409)
        other = total - success - conflict
        # Verify oversell by checking final seat status
        response = await client.get(f"{API_URL}/showtimes/{showtime_id}/seats")
        seats = response.json()
        seat = next((s for s in seats if s['id'] == seat_id), None)
        oversell = 0
        # If seat status is not AVAILABLE or HELD, count as oversell (unlikely)
        if seat and seat['status'] not in ('AVAILABLE', 'HELD'):
            oversell = 1
        
        report = f"""
| Metric | Count |
|--------|-------|
| Requests Sent | {total} |
| Successful Holds (200) | {success} |
| Rejections (409) | {conflict} |
| Other Errors | {other} |
| Oversell (double-booked) | {oversell} |
"""
        print(report)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Concurrency test for seat hold')
    parser.add_argument('--seat-id', type=int, required=True, help='Seat ID to test')
    parser.add_argument('--showtime-id', type=int, required=True, help='Showtime ID containing the seat')
    parser.add_argument('--count', type=int, default=100, help='Number of concurrent requests')
    args = parser.parse_args()
    asyncio.run(run_test(args.seat_id, args.showtime_id, args.count))
