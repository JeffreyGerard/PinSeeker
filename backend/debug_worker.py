import os
import django
import json
from datetime import datetime

# Setup Django environment so you can access models/utils if needed
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pinseeker.settings')
django.setup()

# Clean import from the unified backend root
from playwright_logic import book_via_foreup_software

def simulate_cloud_run_event():
    # Simulate the exact JSON payload Cloud Run receives
    json_payload = """
    {
        "course_url": "https://foreupsoftware.com/index.php/booking/19530/1791?_gl=1*9imsew*_ga*OTc1NDk3MjU5LjE3Nzc3Mjc1NDE.*_ga_WQPLP348DP*czE3Nzc3Mjc1NDEkbzEkZzAkdDE3Nzc3Mjc1NDEkajYwJGwwJGgw#teetimes",
        "course_name": "Orchard Creek",
        "course_email": "jeff.gerard05@gmail.com",
        "course_password": "Password101",
        "desired_date": "2026-05-03",
        "earliest_time": "07:00:00",
        "latest_time": "11:00:00",
        "players": 4,
        "public_btn_xpath": "//*[@id='nav-reserve']/a",
        "dry_run": true 
    }
    """
    
    payload = json.loads(json_payload)
    print(f"Starting simulated run for {payload['course_name']}...")
    
    # Mock booking object mirroring the exact Cloud Run payload parsing
    class MockBooking:
        def __init__(self, data):
            self.id = data.get('booking_id', 999)
            self.desired_date = datetime.strptime(data['desired_date'], '%Y-%m-%d').date()
            self.earliest_time = datetime.strptime(data['earliest_time'], '%H:%M:%S').time()
            self.latest_time = datetime.strptime(data['latest_time'], '%H:%M:%S').time()
            self.players = data.get('players', 4)
            self.status = 'RUNNING'
            self.result_log = ""
        def save(self): pass # Mock save

    booking_obj = MockBooking(payload)

    try:
        # Call your unified logic directly
        result = book_via_foreup_software(
            url=payload["course_url"],
            booking=booking_obj,
            email=payload["course_email"],
            password=payload["course_password"],
            dry_run=payload["dry_run"]
        )
        print(f"\nFINAL RESULT: {result}")
    except Exception as e:
        import traceback
        print(f"\nFAILED: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    simulate_cloud_run_event()
