import sys
import re

with open("src/ui/main_window.py", "r") as f:
    content = f.read()

if "import re" not in content:
    content = content.replace("import logging", "import logging\nimport re")

helper_func = """
def format_note_content(content):
    import re
    safe_content = sanitize_html(content)
    # Match #[Type]-[ID], e.g. #BUG-45 or #Roadmap-123
    # Group 1: Type, Group 2: ID
    pattern = r'#([A-Za-z0-9_]+)-(\d+)'
    # We will pass both type and ID in the URL to help lookup
    replacement = r"<a href='wi_\g<1>_\g<2>' style='color:#3B82F6; text-decoration:none; font-weight:bold;'>#\g<1>-\g<2></a>"
    return re.sub(pattern, replacement, safe_content)
"""

if "def format_note_content(content):" not in content:
    content = content.replace("def sanitize_html(text):", helper_func + "\n\ndef sanitize_html(text):")

content = content.replace("sanitize_html(note.content)", "format_note_content(note.content)")

anchor_logic = """
        if link.startswith("wi_"):
            parts = link.split("_")
            if len(parts) == 3:
                wi_type = parts[1]
                wi_id_str = parts[2]
                try:
                    target_id_or_number = int(wi_id_str)
                    
                    # We need to find the item in the current repo
                    # First try to match by github_number, then by local ID
                    items = self.repo.get_workitems_for_repo(self.current_repo)
                    target_item = None
                    for item in items:
                        if item.github_number == target_id_or_number:
                            target_item = item
                            break
                    if not target_item:
                        for item in items:
                            if item.id == target_id_or_number:
                                target_item = item
                                break
                    
                    if target_item:
                        # Find the row in the model
                        for row in range(self.workitem_model.rowCount()):
                            if self.workitem_model.get_item(row).id == target_item.id:
                                idx = self.workitem_model.index(row, 0)
                                self.workitem_view.setCurrentIndex(idx)
                                self.on_workitem_selected(idx)
                                break
                except ValueError:
                    pass
            return

        if link.startswith("delete_"):
"""

if "if link.startswith(\"delete_\"):" in content:
    content = content.replace("if link.startswith(\"delete_\"):", anchor_logic)

with open("src/ui/main_window.py", "w") as f:
    f.write(content)
print("Cross-referencing applied.")
