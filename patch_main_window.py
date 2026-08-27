import re

with open("src/ui/main_window.py", "r") as f:
    content = f.read()

# 1. Imports
import_patch = """
from src.ui.github_pat_dialog import GitHubPATDialog
from src.ui.roadmap_dialog import RoadmapCreationDialog
from PySide6.QtCore import QTimer
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtWidgets import QMenu
import json
"""
content = content.replace("import logging", "import logging\n" + import_patch)

# 2. prompt_github_token
prompt_old = """    def prompt_github_token(self):
        token, ok = QInputDialog.getText(
            self, "GitHub Login", 
            "Enter your GitHub Personal Access Token (PAT):",
            QLineEdit.EchoMode.Password
        )
        if ok and token:
            logger.info("New GitHub Token securely saved to Keyring.")
            save_github_token(token.strip())
            self.update_github_btn()
            self.sync_repos()"""

prompt_new = """    def prompt_github_token(self):
        dialog = GitHubPATDialog(self)
        if dialog.exec():
            token = dialog.get_token()
            if token:
                logger.info("New GitHub Token securely saved to Keyring.")
                save_github_token(token.strip())
                self.update_github_btn()
                self.sync_repos()"""
content = content.replace(prompt_old, prompt_new)

# 3. Add context menu policy to lists
setup_lists_old = """        self.repo_list = QListWidget()
        self.repo_list.setFixedWidth(250)
        self.repo_list.itemClicked.connect(self.on_repo_selected)"""

setup_lists_new = """        self.repo_list = QListWidget()
        self.repo_list.setFixedWidth(250)
        self.repo_list.itemClicked.connect(self.on_repo_selected)
        self.repo_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.repo_list.customContextMenuRequested.connect(self.show_repo_context_menu)"""
content = content.replace(setup_lists_old, setup_lists_new)

setup_wi_list_old = """        self.workitem_view = QListView()
        self.workitem_view.clicked.connect(self.on_workitem_selected)"""
setup_wi_list_new = """        self.workitem_view = QListView()
        self.workitem_view.clicked.connect(self.on_workitem_selected)
        self.workitem_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.workitem_view.customContextMenuRequested.connect(self.show_workitem_context_menu)"""
content = content.replace(setup_wi_list_old, setup_wi_list_new)

# 4. setup timer in __init__
init_old = """        self.update_github_btn()
        self.load_repos()"""
init_new = """        self.update_github_btn()
        self.load_repos()
        
        self.sync_timer = QTimer(self)
        self.sync_timer.setInterval(60000)
        self.sync_timer.timeout.connect(self.perform_auto_sync)
        self.is_syncing = False
"""
content = content.replace(init_old, init_new)

# 5. Timer toggle
sync_toggle_old = """    def on_sync_toggled(self, checked):
        if checked:
            self.sync_toggle.setText("🔄 Auto-Sync: ON")
            self.sync_toggle.setStyleSheet("color: #10b981; font-weight: bold;")
            # Start sync timer here in real implementation
        else:
            self.sync_toggle.setText("⏸ Auto-Sync: OFF")
            self.sync_toggle.setStyleSheet("color: #9CA3AF;")
            # Stop timer"""
sync_toggle_new = """    def on_sync_toggled(self, checked):
        if checked:
            self.sync_toggle.setText("🔄 Auto-Sync: ON")
            self.sync_toggle.setStyleSheet("color: #10b981; font-weight: bold;")
            self.sync_timer.start()
        else:
            self.sync_toggle.setText("⏸ Auto-Sync: OFF")
            self.sync_toggle.setStyleSheet("color: #9CA3AF;")
            self.sync_timer.stop()

    def perform_auto_sync(self):
        if self.is_syncing or not get_github_token() or not self.current_repo:
            return
        logger.info(f"Auto-sync triggered for {self.current_repo}")
        self.is_syncing = True
        worker = GitHubSyncWorker(self.current_repo)
        worker.signals.result.connect(self.on_sync_success)
        worker.signals.error.connect(self.on_sync_error)
        self.threadpool.start(worker)

    def on_sync_success(self, _):
        self.is_syncing = False
        logger.info("Auto-sync completed")

    def on_sync_error(self, err):
        self.is_syncing = False
        logger.error(f"Auto-sync failed: {err}")"""
content = content.replace(sync_toggle_old, sync_toggle_new)

with open("src/ui/main_window.py", "w") as f:
    f.write(content)
