with open("src/ui/main_window.py", "r") as f:
    lines = f.readlines()

new_lines = []
skip = False
for line in lines:
    if "from PySide6.QtWidgets import QGraphicsDropShadowEffect" in line:
        skip = True
    if skip:
        if "setGraphicsEffect(shadow)" in line:
            skip = False
        continue
    new_lines.append(line)

with open("src/ui/main_window.py", "w") as f:
    f.writelines(new_lines)
print("Shadows removed.")
