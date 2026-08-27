import re

with open("src/ui/main_window.py", "r") as f:
    content = f.read()

# 1. Define format_note_content right after the imports
if "def format_note_content" not in content:
    helper = """
def format_note_content(content):
    import re
    from src.core.security import sanitize_html
    safe_content = sanitize_html(content)
    pattern = r'#([A-Za-z0-9_]+)-(\d+)'
    replacement = r"<a href='wi_\g<1>_\g<2>' style='color:#3B82F6; text-decoration:none; font-weight:bold;'>#\g<1>-\g<2></a>"
    return re.sub(pattern, replacement, safe_content)
"""
    # Insert after imports
    content = content.replace("from src.core.security import", helper + "\nfrom src.core.security import")

# 2. Fix the AttributeError
content = content.replace("self.refresh_workitem_list()", "self.load_local_data(self.current_repo)")

with open("src/ui/main_window.py", "w") as f:
    f.write(content)
print("Fixed!")
