import re

with open("src/ui/main_window.py", "r") as f:
    content = f.read()

# 1. Update CreateWorkItemDialog types
old_types = 'self.type_combo.addItems(["Development", "Bug", "Enhancement", "Documentation"])'
new_types = 'self.type_combo.addItems(["Development", "Bug", "Enhancement", "Documentation", "Incident"])'
content = content.replace(old_types, new_types)

# 2. Add Recycle Bin toggle and Auto-Sync toggle
init_old = """        # Bottom Panel
        bottom_panel = QWidget()
        bottom_layout = QHBoxLayout(bottom_panel)"""
init_new = """        # Bottom Panel
        bottom_panel = QWidget()
        bottom_layout = QHBoxLayout(bottom_panel)
        
        self.sync_toggle = QPushButton("🔄 Auto-Sync: OFF")
        self.sync_toggle.setCheckable(True)
        self.sync_toggle.toggled.connect(self.on_sync_toggled)
        self.sync_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self.recycle_btn = QPushButton("🗑️ Recycle Bin")
        self.recycle_btn.setCheckable(True)
        self.recycle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.recycle_btn.toggled.connect(self.on_recycle_toggled)
        
        bottom_layout.addWidget(self.sync_toggle)
        bottom_layout.addWidget(self.recycle_btn)
"""
content = content.replace(init_old, init_new)

# 3. Add Incident Note Toggles in detail view
footer_old = """        self.note_type_combo = QComboBox()
        self.note_type_combo.addItems(["Note", "Important", "PR Link", "Closed"])
        self.note_type_combo.setFixedHeight(60)
        footer_layout.addWidget(self.note_type_combo)"""
footer_new = """        self.note_type_combo = QComboBox()
        self.note_type_combo.addItems(["Note", "Important", "PR Link", "Closed", "Mitigated", "Service degradation", "Active", "On Deps"])
        self.note_type_combo.setFixedHeight(60)
        footer_layout.addWidget(self.note_type_combo)"""
content = content.replace(footer_old, footer_new)

# 4. Declare Outage button
header_old = """        status_container = QHBoxLayout()
        status_container.addStretch()
        status_container.addWidget(QLabel("<b>Status:</b>"))"""
header_new = """        status_container = QHBoxLayout()
        status_container.addStretch()
        self.outage_btn = QPushButton("🚨 Declare Outage")
        self.outage_btn.setStyleSheet("background-color: #ef4444; color: white; font-weight: bold;")
        self.outage_btn.setVisible(False)
        self.outage_btn.clicked.connect(self.on_declare_outage)
        status_container.addWidget(self.outage_btn)
        status_container.addWidget(QLabel("<b>Status:</b>"))"""
content = content.replace(header_old, header_new)

# 5. Show Outage button if type is Incident
refresh_old = """        self.title_label.setText(f"<h2>{sanitize_html(domain_item.title)}</h2>")"""
refresh_new = """        self.title_label.setText(f"<h2>{sanitize_html(domain_item.title)}</h2>")
        if domain_item.item_type == "Incident":
            self.outage_btn.setVisible(True)
        else:
            self.outage_btn.setVisible(False)"""
content = content.replace(refresh_old, refresh_new)

# 6. Add stubs for new slots
slots = """    def on_sync_toggled(self, checked):
        if checked:
            self.sync_toggle.setText("🔄 Auto-Sync: ON")
            self.sync_toggle.setStyleSheet("color: #10b981; font-weight: bold;")
            # Start sync timer here in real implementation
        else:
            self.sync_toggle.setText("🔄 Auto-Sync: OFF")
            self.sync_toggle.setStyleSheet("")

    def on_recycle_toggled(self, checked):
        if checked:
            self.title_label.setText("<h2>🗑️ Recycle Bin Mode</h2>")
            self.workitem_model.update_data([]) # Show empty for now
        else:
            repo_name = self.repo_combo.currentText() if self.is_classic_theme else (self.repo_list.currentItem().text() if self.repo_list.currentItem() else None)
            if repo_name:
                self.load_local_data(repo_name)
            else:
                self.title_label.setText("<h2>Select a Repo</h2>")

    def on_declare_outage(self):
        QMessageBox.warning(self, "Outage Declared", "Service Outage has been declared for this incident.")
        # We would update metadata here
        self.on_submit_note(auto_content="[ACTIVE] Outage officially declared.")

    def on_status_changed"""
content = content.replace("    def on_status_changed", slots)

# Fix on_declare_outage calling on_submit_note which requires no args
# Let's fix that.
content = content.replace("self.on_submit_note(auto_content=\"[ACTIVE] Outage officially declared.\")", 
                          "self.note_input.setText('Outage officially declared.'); self.note_type_combo.setCurrentText('Active'); self.on_submit_note()")

# 7. Modify load_repos to segregate Online and Offline
load_repos_old = """        self.repo_combo.clear()
        self.repo_list.clear()
        
        for r in sorted_repos:
            self.repo_combo.addItem(r.name)
            self.repo_list.addItem(r.name)"""
load_repos_new = """        self.repo_combo.clear()
        self.repo_list.clear()
        
        self.repo_combo.addItem("--- ☁️ Online ---")
        # In a real QListView we'd disable this item, but for now it's just a label
        
        online = [r for r in sorted_repos if not r.is_offline]
        offline = [r for r in sorted_repos if r.is_offline]
        
        for r in online:
            self.repo_combo.addItem(r.name)
            self.repo_list.addItem(f"☁️ {r.name}")
            
        self.repo_combo.addItem("--- 📁 Offline ---")
        for r in offline:
            self.repo_combo.addItem(r.name)
            self.repo_list.addItem(f"📁 {r.name}")"""
content = content.replace(load_repos_old, load_repos_new)

# Update on_add_workitem to strip the emoji prefixes
# Since we prefix ☁️ or 📁 in repo_list, we need to clean it up before fetching
clean_old = """        if self.is_classic_theme:
            repo_name = self.repo_combo.currentText()
        else:
            current_repo_item = self.repo_list.currentItem()
            repo_name = current_repo_item.text() if current_repo_item else None"""
clean_new = """        if self.is_classic_theme:
            repo_name = self.repo_combo.currentText()
        else:
            current_repo_item = self.repo_list.currentItem()
            repo_name = current_repo_item.text().replace("☁️ ", "").replace("📁 ", "") if current_repo_item else None
            
        if repo_name and repo_name.startswith("---"):
            repo_name = None"""
content = content.replace(clean_old, clean_new)

with open("src/ui/main_window.py", "w") as f:
    f.write(content)
