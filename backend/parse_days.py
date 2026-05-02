import re
with open(r'c:\Users\jeffg\Projects\PinSeeker\backend\screenshots\debug_cal.html', 'r', encoding='utf-8') as f:
    html = f.read()

import re
with open(r'c:\Users\jeffg\Projects\PinSeeker\backend\screenshots\debug_cal.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Find anything containing "29"
matches = re.findall(r'(.{20}29.{20})', html)
for m in matches:
    print(m)
