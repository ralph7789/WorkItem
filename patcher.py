import re

with open("src/ui/main_window.py", "r") as f:
    content = f.read()

# 1. Add QDialog import
content = content.replace("QToolBar, QComboBox", "QToolBar, QComboBox, QDialog")

# 2. Inject CreateWorkItemDialog before MainWindow
dialog_code = """
class CreateWorkItemDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create New WorkItem")
        self.resize(400, 300)
        
        layout = QVBoxLayout(self)
        
        layout.addWidget(QLabel("Title:"))
        self.title_input = QLineEdit()
        layout.addWidget(self.title_input)
        
        layout.addWidget(QLabel("Description / Body:"))
        self.body_input = QTextEdit()
        layout.addWidget(self.body_input)
        
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Type:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Development", "Bug", "Enhancement", "Documentation"])
        type_layout.addWidget(self.type_combo)
        layout.addLayout(type_layout)
        
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("Create")
        self.save_btn.setObjectName("primary_btn")
        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.save_btn)
        layout.addLayout(btn_layout)

    def get_data(self):
        return {
            "title": self.title_input.text().strip(),
            "body": self.body_input.toPlainText().strip(),
            "type": self.type_combo.currentText()
        }

class MainWindow"""
content = content.replace("class MainWindow", dialog_code)

# 3. Replace status_label with status_combo
status_old = """        self.status_label = QLabel("<b>Status:</b> -")
        self.status_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        header_layout.addWidget(self.title_label)
        header_layout.addWidget(self.status_label)"""
status_new = """        header_layout.addWidget(self.title_label)
        
        status_container = QHBoxLayout()
        status_container.addStretch()
        status_container.addWidget(QLabel("<b>Status:</b>"))
        self.status_combo = QComboBox()
        self.status_combo.addItems(["open", "in-progress", "closed"])
        self.status_combo.currentTextChanged.connect(self.on_status_changed)
        status_container.addWidget(self.status_combo)
        header_layout.addLayout(status_container)"""
content = content.replace(status_old, status_new)

# 4. Modify footer_layout to include note_type_combo
footer_old = """        footer_layout = QHBoxLayout()
        self.note_input = QTextEdit()"""
footer_new = """        footer_layout = QHBoxLayout()
        
        self.note_type_combo = QComboBox()
        self.note_type_combo.addItems(["Note", "Important", "PR Link", "Closed"])
        self.note_type_combo.setFixedHeight(60)
        footer_layout.addWidget(self.note_type_combo)
        
        self.note_input = QTextEdit()"""
content = content.replace(footer_old, footer_new)

# 5. Fix on_add_workitem
add_wi_old = """    def on_add_workitem(self):
        current_repo_item = self.repo_list.currentItem()
        if not current_repo_item:
            QMessageBox.warning(self, "No Repo Selected", "Please select a repository first.")
            return
            
        repo_name = current_repo_item.text()
        title, ok = QInputDialog.getText(self, "Add WorkItem", "Enter WorkItem Title:")
        if ok and title:
            from src.core.domain import DomainWorkItem
            from datetime import datetime, timezone
            
            domain_item = DomainWorkItem(
                id=None,
                repo_name=repo_name,
                item_type="Development",
                title=title,
                body="",
                github_id=None,
                github_number=None,
                state="open",
                sync_status="local",
                local_updated_at=datetime.now(timezone.utc)
            )
            self.repo.save_workitem(domain_item)
            self.load_local_data(repo_name)"""
            
add_wi_new = """    def on_add_workitem(self):
        if self.is_classic_theme:
            repo_name = self.repo_combo.currentText()
        else:
            current_repo_item = self.repo_list.currentItem()
            repo_name = current_repo_item.text() if current_repo_item else None
            
        if not repo_name:
            QMessageBox.warning(self, "No Repo Selected", "Please select a repository first.")
            return
            
        dialog = CreateWorkItemDialog(self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            if data["title"]:
                from src.core.domain import DomainWorkItem
                from datetime import datetime, timezone
                
                domain_item = DomainWorkItem(
                    id=None,
                    repo_name=repo_name,
                    item_type=data["type"],
                    title=data["title"],
                    body=data["body"],
                    github_id=None,
                    github_number=None,
                    state="open",
                    sync_status="local",
                    local_updated_at=datetime.now(timezone.utc)
                )
                self.repo.save_workitem(domain_item)
                
                # Also save the description as the first note if provided
                if data["body"]:
                    saved_item = self.repo.get_workitems_for_repo(repo_name)[0] # It's ordered by updated, so it's first
                    self.repo.add_note(saved_item.id, f"[Description]\n{data['body']}")
                    
                self.load_local_data(repo_name)"""
content = content.replace(add_wi_old, add_wi_new)

# 6. Fix on_workitem_selected to update status combo safely
sel_old = """            self.title_label.setText(f"<h2>{sanitize_html(domain_item.title)}</h2>")
            self.status_label.setText(f"<b>Status:</b> {domain_item.state}")
            
            # Load notes"""
sel_new = """            self.title_label.setText(f"<h2>{sanitize_html(domain_item.title)}</h2>")
            
            self.status_combo.blockSignals(True)
            idx = self.status_combo.findText(domain_item.state)
            if idx >= 0:
                self.status_combo.setCurrentIndex(idx)
            self.status_combo.blockSignals(False)
            
            # Load notes"""
content = content.replace(sel_old, sel_new)

# 7. Prepend note type in on_submit_note
sub_old = """        content = self.note_input.toPlainText().strip()
        if content and domain_item:"""
sub_new = """        content = self.note_input.toPlainText().strip()
        if content and domain_item:
            note_type = self.note_type_combo.currentText()
            if note_type != "Note":
                content = f"[{note_type.upper()}] {content}"
"""
content = content.replace(sub_old, sub_new)


# 8. Add on_status_changed method
status_method = """    def on_status_changed(self, new_status):
        index = self.workitem_view.currentIndex()
        if not index.isValid():
            return
        domain_item = self.workitem_model.get_item(index.row())
        if domain_item:
            logger.info(f"UI Event: Changed status of #{domain_item.id} to {new_status}")
            domain_item.state = new_status
            self.repo.save_workitem(domain_item)
            self.load_local_data(domain_item.repo_name)
            self.on_workitem_selected(index) # refresh view

    def on_submit_note"""
content = content.replace("    def on_submit_note", status_method)


with open("src/ui/main_window.py", "w") as f:
    f.write(content)

print("Patched main_window.py")
