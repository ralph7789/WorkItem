import sys

def apply_shadow(var_name):
    return f"""
        from PySide6.QtWidgets import QGraphicsDropShadowEffect
        from PySide6.QtGui import QColor
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 80))
        self.{var_name}.setGraphicsEffect(shadow)
"""

with open("src/ui/main_window.py", "r") as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    new_lines.append(line)
    if "self.notes_browser = QTextBrowser()" in line:
        new_lines.append(apply_shadow("notes_browser"))
    elif "self.note_input = QTextEdit()" in line:
        new_lines.append(apply_shadow("note_input"))
    elif "self.workitem_view = QListView()" in line:
        new_lines.append(apply_shadow("workitem_view"))

with open("src/ui/main_window.py", "w") as f:
    f.writelines(new_lines)

print("Shadows patched successfully.")
