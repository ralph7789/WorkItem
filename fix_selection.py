import re

with open("src/ui/main_window.py", "r") as f:
    content = f.read()

# 1. Add self.current_workitem_id = None to __init__
content = content.replace("self.is_classic_theme = False", "self.is_classic_theme = False\n        self.current_workitem_id = None")

# 2. Update on_workitem_selected to save ID
sel_old = """    def on_workitem_selected(self, index):
        domain_item = self.workitem_model.get_item(index.row())
        if domain_item:"""
sel_new = """    def on_workitem_selected(self, index):
        domain_item = self.workitem_model.get_item(index.row())
        if domain_item:
            self.current_workitem_id = domain_item.id"""
content = content.replace(sel_old, sel_new)

# 3. Update on_status_changed
stat_old = """    def on_status_changed(self, new_status):
        index = self.workitem_view.currentIndex()
        if not index.isValid():
            return
        domain_item = self.workitem_model.get_item(index.row())
        if domain_item:"""
stat_new = """    def on_status_changed(self, new_status):
        if not self.current_workitem_id:
            return
        domain_item = self.repo.get_workitem_by_id(self.current_workitem_id)
        if domain_item:"""
content = content.replace(stat_old, stat_new)

# 4. Update on_submit_note
sub_old = """    def on_submit_note(self):
        index = self.workitem_view.currentIndex()
        if not index.isValid():
            return
            
        domain_item = self.workitem_model.get_item(index.row())"""
sub_new = """    def on_submit_note(self):
        if not self.current_workitem_id:
            return
            
        domain_item = self.repo.get_workitem_by_id(self.current_workitem_id)"""
content = content.replace(sub_old, sub_new)

# 5. Fix the refresh view in on_submit_note and on_status_changed
# We no longer have `index` to pass to `self.on_workitem_selected(index)`.
# So we need a `refresh_workitem_view()` method.
content = content.replace("            self.on_workitem_selected(index) # refresh view", "            self.refresh_workitem_view()")
content = content.replace("            self.on_workitem_selected(index)", "            self.refresh_workitem_view()")

# Add refresh_workitem_view
refresh_code = """    def refresh_workitem_view(self):
        if not self.current_workitem_id:
            return
        domain_item = self.repo.get_workitem_by_id(self.current_workitem_id)
        if not domain_item:
            return
        self.title_label.setText(f"<h2>{sanitize_html(domain_item.title)}</h2>")
        self.status_combo.blockSignals(True)
        idx = self.status_combo.findText(domain_item.state)
        if idx >= 0:
            self.status_combo.setCurrentIndex(idx)
        self.status_combo.blockSignals(False)
        html_content = ""
        for note in domain_item.notes:
            html_content += f"<p><i>{note.created_at.strftime('%Y-%m-%d %H:%M')}</i><br>{sanitize_html(note.content)}</p><hr>"
        self.notes_browser.setHtml(html_content)

    def on_status_changed"""
content = content.replace("    def on_status_changed", refresh_code)


with open("src/ui/main_window.py", "w") as f:
    f.write(content)

print("Selection fix applied.")
