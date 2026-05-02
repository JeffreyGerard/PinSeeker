import sys

filepath = r'c:\Users\jeffg\Projects\PinSeeker\backend\bookings\playwright_logic.py'
with open(filepath, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
in_function = False
for i, line in enumerate(lines):
    if 'def book_via_foreup_software' in line:
        in_function = True
        new_lines.append(line)
        continue
    
    if in_function:
        if line.strip() == "" and i < len(lines) - 1 and lines[i+1].startswith('def '):
            in_function = False
            new_lines.append(line)
            continue
        
        # Lines 242-245 were:
        # 242:     with sync_playwright() as p:
        # 243:         browser, context = _new_stealth_context(p, headless=True)
        # 244:         page = context.new_page()
        # 245:         try:
        
        # So from line 246 onwards (index 245), we need to indent by 4 spaces
        # Wait, index 0 is line 1.
        if i >= 245 and i <= 520: # Adjust range to cover the function body
             if line.startswith('        '): # Already indented enough?
                 new_lines.append('    ' + line)
             elif line.startswith('    '):
                 new_lines.append('    ' + line)
             else:
                 new_lines.append(line) # Should not happen for function body
        else:
            new_lines.append(line)
    else:
        new_lines.append(line)

with open(filepath, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
