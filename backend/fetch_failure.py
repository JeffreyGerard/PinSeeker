import sys
import os
from google.cloud import firestore

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/Users/jeffgerard/Projects/PinSeeker/backend/service-account.json'
os.environ['GOOGLE_CLOUD_PROJECT'] = 'pinseeker-app'

def fetch_latest_failure():
    db = firestore.Client()
    query = db.collection('tee_time_jobs').where('status', '==', 'FAILED')
    results = list(query.stream())
    if not results:
        print("No failed jobs found.")
        return
    
    # Sort locally by updated_at
    results.sort(key=lambda x: x.to_dict().get('updated_at', ''), reverse=True)
    doc = results[0]
    data = doc.to_dict()
    
    print(f"Job ID: {doc.id}")
    for k, v in data.items():
        if k != 'error_screenshot':
            print(f"{k}: {v}")
    
    screenshot = data.get('error_screenshot')
    if screenshot:
        import base64
        out_path = '/Users/jeffgerard/.gemini/antigravity/brain/d80aae5c-c1f3-4d87-89e7-cbb471aa42fc/error_screenshot_latest.png'
        with open(out_path, 'wb') as f:
            f.write(base64.b64decode(screenshot.replace('data:image/png;base64,', '')))
        print(f"Screenshot saved to {out_path}")
    else:
        print("No screenshot attached.")

if __name__ == '__main__':
    fetch_latest_failure()
