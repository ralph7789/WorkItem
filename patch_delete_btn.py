with open("src/ui/main_window.py", "r") as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    new_lines.append(line)
    if "self.status_combo.currentTextChanged.connect(self.on_status_changed)" in line:
        new_lines.append("""
        self.delete_wi_btn = QPushButton("🗑️ Delete")
        self.delete_wi_btn.setStyleSheet("background-color: #ef4444; color: white; border: none;")
        self.delete_wi_btn.clicked.connect(self.on_delete_workitem_btn)
        status_container.addWidget(self.delete_wi_btn)
""")

    if "def show_error(self, err_msg):" in line:
        new_lines.append("""
    def on_delete_workitem_btn(self):
        if not self.current_workitem_id: return
        reply = QMessageBox.question(self, 'Delete WorkItem', 'Delete this WorkItem?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.repo.delete_workitem(self.current_workitem_id)
            self.refresh_workitem_list()
            self.notes_browser.setHtml("")
            self.title_label.setText("")
            self.current_workitem_id = None
""")

with open("src/ui/main_window.py", "w") as f:
    f.writelines(new_lines)
print("Added Delete WorkItem button.")
