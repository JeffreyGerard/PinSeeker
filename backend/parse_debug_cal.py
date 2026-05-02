import re
with open(r'c:\Users\jeffg\Projects\PinSeeker\backend\screenshots\debug_cal.html', 'r', encoding='utf-8') as f:
    html = f.read()

print("Any dp__cell_inner:", "dp__cell_inner" in html)
print("Any day class:", "class=\"day" in html or "class='day" in html or " class=\"day\" " in html)
print("Any fc-daygrid-day-number:", "fc-daygrid-day-number" in html)
print("Any calendar-day:", "calendar-day" in html)
print("Any 29:", ">29<" in html or "> 29 <" in html)

matches = re.findall(r'<([^>]*29[^>]*)>', html)
print("Tags containing 29:", matches)
