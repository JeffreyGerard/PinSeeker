import re
with open(r'c:\Users\jeffg\Projects\PinSeeker\backend\screenshots\tee_sheet_clicked.html', 'r', encoding='utf-8') as f:
    html = f.read()
iframes = re.findall(r'<iframe', html)
print(f"Number of iframes: {len(iframes)}")
# Look for any text related to login
login_text = re.findall(r'(.{20}Log In.{20})', html, re.I)
print(f"Login text matches: {login_text}")
