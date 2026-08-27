import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QListWidget, QListView, QSplitter, QLabel, QTextBrowser, QTextEdit, QPushButton,
    QMessageBox, QInputDialog, QLineEdit, QToolBar, QComboBox, QDialog, QCheckBox
)
from PySide6.QtCore import Qt, QThreadPool

from src.repositories.workitem_repo import WorkItemRepository
from src.viewmodels.workitem_viewmodel import WorkItemListModel
from src.core.github_sync import GitHubSyncWorker, GitHubPushWorker, GitHubRepoListWorker
from src.models.schema import initialize_database, Repo

def format_note_content(content):
    import re
    from src.core.security import sanitize_html
    safe_content = sanitize_html(content)
    pattern = r'#([A-Za-z0-9_]+)-(\d+)'
    replacement = r"<a href='wi_\g<1>_\g<2>' style='color:#3B82F6; text-decoration:none; font-weight:bold;'>#\g<1>-\g<2></a>"
    return re.sub(pattern, replacement, safe_content)

from src.core.security import sanitize_html, get_github_token, save_github_token

import logging
import re

from src.ui.github_pat_dialog import GitHubPATDialog
from src.ui.roadmap_dialog import RoadmapCreationDialog
from PySide6.QtCore import QTimer
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtWidgets import QMenu
import json

import os
from pathlib import Path

log_dir = Path.home() / '.workitems'
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / 'app.log'

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("MainWindow")


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
        self.type_combo.addItems(["Development", "Bug", "Enhancement", "Documentation", "Incident", "Roadmap"])
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

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        logger.info("Initializing MainWindow UI...")
        self.setWindowTitle("WorkItems")
        self.resize(1024, 768)
        
        self.is_classic_theme = False
        self.current_workitem_id = None
        self.current_repo = None
        self.is_syncing = False
        self.apply_theme()
            
        self.threadpool = QThreadPool()
        logger.info(f"QThreadPool initialized with max thread count: {self.threadpool.maxThreadCount()}")

        self.repo = WorkItemRepository()

        # Toolbar
        toolbar = QToolBar("Main Toolbar")
        toolbar.setStyleSheet("QToolBar { background-color: transparent; border: none; padding: 4px; }")
        self.addToolBar(toolbar)
        
        self.theme_toggle_btn = QPushButton("🌙")
        self.theme_toggle_btn.setObjectName("theme_toggle_btn")
        self.theme_toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.theme_toggle_btn.clicked.connect(self.toggle_theme)
        toolbar.addWidget(self.theme_toggle_btn)

        self.repo_combo = QComboBox()
        self.repo_combo.currentTextChanged.connect(self.on_combo_repo_selected)
        self.repo_combo_action = toolbar.addWidget(self.repo_combo)
        self.repo_combo_action.setVisible(False)
        
        self.classic_add_repo_btn = QPushButton("+ Repo")
        self.classic_add_repo_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.classic_add_repo_btn.clicked.connect(self.on_add_repo)
        self.classic_add_repo_action = toolbar.addWidget(self.classic_add_repo_btn)
        self.classic_add_repo_action.setVisible(False)
        
        self.classic_del_repo_btn = QPushButton("🗑️")
        self.classic_del_repo_btn.setToolTip("Delete Repository")
        self.classic_del_repo_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.classic_del_repo_btn.clicked.connect(self.on_delete_repo_classic)
        self.classic_del_repo_action = toolbar.addWidget(self.classic_del_repo_btn)
        self.classic_del_repo_action.setVisible(False)
        
        # Spacer to push button to the right
        spacer = QWidget()
        spacer.setSizePolicy(spacer.sizePolicy().Policy.Expanding, spacer.sizePolicy().Policy.Expanding)
        toolbar.addWidget(spacer)
        
        self.sync_toggle = QCheckBox("🔄 Auto-Sync: OFF")
        self.sync_toggle.toggled.connect(self.on_sync_toggled)
        toolbar.addWidget(self.sync_toggle)
        
        self.github_btn = QPushButton("Link GitHub")
        self.github_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.github_btn.clicked.connect(self.prompt_github_token)
        toolbar.addWidget(self.github_btn)

        # Central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)

        # 1. Sidebar for Repositories
        self.sidebar_widget = QWidget()
        sidebar_layout = QVBoxLayout(self.sidebar_widget)
        sidebar_layout.setContentsMargins(0,0,0,0)
        
        self.repo_list = QListWidget()
        self.repo_list.setFixedWidth(250)
        self.repo_list.itemClicked.connect(self.on_repo_selected)
        self.repo_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.repo_list.customContextMenuRequested.connect(self.show_repo_context_menu)
        
        self.add_repo_btn = QPushButton("+ Add Repository")
        self.add_repo_btn.setObjectName("primary_btn")
        self.add_repo_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_repo_btn.clicked.connect(self.on_add_repo)
        
        sidebar_layout.addWidget(QLabel("<b>Repositories</b>"))
        sidebar_layout.addWidget(self.repo_list)
        sidebar_layout.addWidget(self.add_repo_btn)
        main_layout.addWidget(self.sidebar_widget)

        # 2. Master-Detail Splitter
        self.splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(self.splitter)

        # Master: List of WorkItems + Add Button
        master_widget = QWidget()
        master_layout = QVBoxLayout(master_widget)
        master_layout.setContentsMargins(0,0,0,0)
        
        self.workitem_view = QListView()

        self.workitem_model = WorkItemListModel()
        self.workitem_view.setModel(self.workitem_model)
        self.workitem_view.clicked.connect(self.on_workitem_selected)
        self.workitem_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.workitem_view.customContextMenuRequested.connect(self.show_workitem_context_menu)
        
        self.add_wi_btn = QPushButton("+ Add WorkItem")
        self.add_wi_btn.setObjectName("primary_btn")
        self.add_wi_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_wi_btn.clicked.connect(self.on_add_workitem)
        
        wi_header_layout = QHBoxLayout()
        wi_header_layout.addWidget(QLabel("<b>WorkItems</b>"))
        wi_header_layout.addStretch()
        self.recycle_toggle = QCheckBox("🗑️ Recycle Bin")
        self.recycle_toggle.toggled.connect(self.on_recycle_toggled)
        wi_header_layout.addWidget(self.recycle_toggle)
        master_layout.addLayout(wi_header_layout)
        
        master_layout.addWidget(self.workitem_view)
        master_layout.addWidget(self.add_wi_btn)
        self.splitter.addWidget(master_widget)

        # Detail: Fixed header, scrollable notes, sticky footer
        detail_widget = QWidget()
        detail_layout = QVBoxLayout(detail_widget)
        detail_layout.setContentsMargins(16, 16, 16, 16)
        detail_layout.setSpacing(12)

        # Fixed Header
        header_layout = QHBoxLayout()
        self.title_label = QLabel("<h2 style='color: #888;'>Select a WorkItem</h2>")
        header_layout.addWidget(self.title_label)
        
        status_container = QHBoxLayout()
        status_container.addStretch()
        self.outage_btn = QPushButton("🚨 Declare Outage")
        self.outage_btn.setStyleSheet("background-color: #ef4444; color: white; font-weight: bold;")
        self.outage_btn.setVisible(False)
        self.outage_btn.clicked.connect(self.on_declare_outage)
        status_container.addWidget(self.outage_btn)
        status_container.addWidget(QLabel("<b>Status:</b>"))
        self.status_combo = QComboBox()
        self.status_combo.addItems(["open", "in-progress", "closed"])
        self.status_combo.currentTextChanged.connect(self.on_status_changed)

        self.delete_wi_btn = QPushButton("🗑️ Delete")
        self.delete_wi_btn.setStyleSheet("background-color: #ef4444; color: white; border: none;")
        self.delete_wi_btn.clicked.connect(self.on_delete_workitem_btn)
        status_container.addWidget(self.delete_wi_btn)
        status_container.addWidget(self.status_combo)
        
        self.cloud_sync_check = QCheckBox("☁️ Sync to Cloud")
        self.cloud_sync_check.setChecked(True)
        self.cloud_sync_check.setVisible(False)
        self.cloud_sync_check.toggled.connect(self.on_cloud_sync_toggled)
        status_container.addWidget(self.cloud_sync_check)
        
        header_layout.addLayout(status_container)
        detail_layout.addLayout(header_layout)


        # --- DETAILS CARD ---
        from PySide6.QtWidgets import QFrame
        self.details_card = QFrame()
        self.details_card.setObjectName("detailsCard")
        self.details_card.setVisible(False)
        
        details_card_layout = QVBoxLayout(self.details_card)
        details_card_layout.setContentsMargins(16, 16, 16, 16)
        details_card_layout.setSpacing(12)
        
        meta_layout = QHBoxLayout()
        self.type_badge = QLabel()
        self.type_badge.setObjectName("typeBadge")
        self.meta_text = QLabel()
        self.meta_text.setObjectName("metaText")
        
        meta_layout.addWidget(self.type_badge)
        meta_layout.addWidget(self.meta_text)
        meta_layout.addStretch()
        details_card_layout.addLayout(meta_layout)
        
        self.details_separator = QFrame()
        self.details_separator.setObjectName("detailsSeparator")
        self.details_separator.setFrameShape(QFrame.Shape.HLine)
        details_card_layout.addWidget(self.details_separator)
        
        self.description_text = QTextBrowser()
        self.description_text.setObjectName("descriptionText")
        self.description_text.setOpenExternalLinks(True)
        self.description_text.setMinimumHeight(100)
        self.description_text.setMaximumHeight(200) # Prevents taking up whole screen
        details_card_layout.addWidget(self.description_text)
        
        detail_layout.addWidget(self.details_card)
        
        # --- NOTES HEADER ---
        self.notes_header = QLabel("Activity & Notes")
        self.notes_header.setObjectName("notesHeader")
        self.notes_header.setVisible(False)
        detail_layout.addWidget(self.notes_header)
        
        # Scrollable Notes
        self.notes_browser = QTextBrowser()


        self.notes_browser.setOpenLinks(False)
        self.notes_browser.anchorClicked.connect(self.on_note_anchor_clicked)
        detail_layout.addWidget(self.notes_browser)

        # Sticky Footer
        footer_layout = QHBoxLayout()
        
        self.note_type_combo = QComboBox()
        self.note_type_combo.addItems(["Note", "Important", "PR Link", "Closed", "Mitigated", "Service degradation", "Active", "On Deps"])
        self.note_type_combo.setFixedHeight(60)
        footer_layout.addWidget(self.note_type_combo)
        
        self.note_input = QTextEdit()

        self.note_input.setFixedHeight(60)
        self.note_input.setPlaceholderText("Write a chronological note...")
        self.submit_btn = QPushButton("Submit")
        self.submit_btn.setObjectName("primary_btn")
        self.submit_btn.setFixedHeight(60)
        self.submit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.submit_btn.clicked.connect(self.on_submit_note)
        
        footer_layout.addWidget(self.note_input)
        footer_layout.addWidget(self.submit_btn)
        detail_layout.addLayout(footer_layout)

        self.splitter.addWidget(detail_widget)
        self.splitter.setSizes([300, 500])
        
        # Initial updates
        self.update_github_btn()
        self.load_repos()
        
        self.sync_timer = QTimer(self)
        self.sync_timer.setInterval(60000)
        self.sync_timer.timeout.connect(self.perform_auto_sync)

        
        # Initial check (optional, user can skip)
        logger.info("Checking Keyring for GitHub Token on startup...")
        if not get_github_token():
            reply = QMessageBox.question(
                self, "GitHub Integration", 
                "No GitHub token found. Would you like to link GitHub now?\n\n(You can skip and link it later from the top-right button.)",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.prompt_github_token()
        else:
            self.sync_repos()
            
        # Switch to Classic Mode as default
        self.toggle_theme()

    def toggle_theme(self):
        self.is_classic_theme = not self.is_classic_theme
        if self.is_classic_theme:
            self.theme_toggle_btn.setText("☀️")
            self.sidebar_widget.hide()
            self.repo_combo_action.setVisible(True)
            self.classic_add_repo_action.setVisible(True)
            self.classic_del_repo_action.setVisible(True)
            self.workitem_view.setObjectName("workitem_list")
        else:
            self.theme_toggle_btn.setText("🌙")
            self.sidebar_widget.show()
            self.repo_combo_action.setVisible(False)
            self.classic_add_repo_action.setVisible(False)
            self.classic_del_repo_action.setVisible(False)
            self.workitem_view.setObjectName("")
            
        self.apply_theme()
        
    def apply_theme(self):
        theme_file = "style_classic.qss" if self.is_classic_theme else "style_analogue.qss"
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
            base_path = os.path.join(base_path, '..', '..')
            
        qss_path = os.path.join(base_path, theme_file)
        try:
            with open(qss_path, "r") as f:
                QApplication.instance().setStyleSheet(f.read())
        except Exception as e:
            logger.warning(f"Could not load stylesheet {theme_file}: {e}")

    def update_github_btn(self):
        if get_github_token():
            self.github_btn.setText("GitHub Linked")
            self.github_btn.setObjectName("")
            self.github_btn.setEnabled(False)
        else:
            self.github_btn.setText("Link GitHub")
            self.github_btn.setObjectName("primary_btn")
            self.github_btn.setEnabled(True)
        # Force style re-evaluation
        self.github_btn.style().unpolish(self.github_btn)
        self.github_btn.style().polish(self.github_btn)

    def sync_repos(self):
        if not get_github_token():
            return
        logger.info("Spawning background GitHubRepoListWorker to fetch repos...")
        worker = GitHubRepoListWorker()
        worker.signals.result.connect(lambda repos: self.load_repos())
        worker.signals.error.connect(lambda err: logger.error(f"Repo list sync error: {err}"))
        self.threadpool.start(worker)

    def prompt_github_token(self):
        dialog = GitHubPATDialog(self)
        if dialog.exec():
            token = dialog.get_token()
            if token:
                logger.info("New GitHub Token securely saved to Keyring.")
                save_github_token(token.strip())
                self.update_github_btn()
                self.sync_repos()

    def load_repos(self):
        self.repo_list.clear()
        self.repo_combo.blockSignals(True)
        self.repo_combo.clear()
        
        model = QStandardItemModel()
        self.repo_combo.setModel(model)
        
        repos = self.repo.get_all_repos()
        
        online = [r for r in repos if not r.is_offline]
        offline = [r for r in repos if r.is_offline]
        
        if online:
            header = QStandardItem("--- ☁️ Online ---")
            header.setEnabled(False)
            model.appendRow(header)
            for r in online:
                item = QStandardItem(r.name)
                model.appendRow(item)
                self.repo_list.addItem(f"☁️ {r.name}")
                
        if offline:
            header = QStandardItem("--- 📁 Offline ---")
            header.setEnabled(False)
            model.appendRow(header)
            for r in offline:
                item = QStandardItem(r.name)
                model.appendRow(item)
                self.repo_list.addItem(f"📁 {r.name}")
                
        self.repo_combo.blockSignals(False)

    def on_combo_repo_selected(self, text):
        if text and not text.startswith("---"):
            self.current_repo = text
            self.load_local_data(text)

    def on_add_repo(self):
        repo_name, ok = QInputDialog.getText(self, "Add Repository", "Enter repo name (e.g., my-project):")
        if ok and repo_name:
            # Locally created repos are always offline
            Repo.get_or_create(name=repo_name, defaults={
                'owner': repo_name.split('/')[0] if '/' in repo_name else 'local',
                'is_offline': True
            })
            self.load_repos()

    def on_add_workitem(self):
        if self.is_classic_theme:
            repo_name = self.repo_combo.currentText()
        else:
            current_repo_item = self.repo_list.currentItem()
            repo_name = current_repo_item.text().replace("☁️ ", "").replace("📁 ", "") if current_repo_item else None
            
        if repo_name and repo_name.startswith("---"):
            repo_name = None
            
        if not repo_name:
            QMessageBox.warning(self, "No Repo Selected", "Please select a repository first.")
            return
            
        types = ["Development", "Bug", "Enhancement", "Documentation", "Incident", "Roadmap"]
        item_type, ok = QInputDialog.getItem(self, "Select Type", "WorkItem Type:", types, 0, False)
        if not ok or not item_type:
            return
            
        if item_type == "Roadmap":
            dialog = RoadmapCreationDialog(self)
            if dialog.exec() == QDialog.Accepted:
                data = dialog.get_data()
                from src.core.domain import DomainWorkItem
                from datetime import datetime, timezone
                
                domain_item = DomainWorkItem(
                    id=None,
                    repo_name=repo_name,
                    item_type=item_type,
                    title=data["title"],
                    body="[Roadmap Item]",
                    github_id=None,
                    github_number=None,
                    state="open",
                    sync_status="local",
                    type_metadata=json.loads(data["type_metadata"]),
                    local_updated_at=datetime.now(timezone.utc)
                )
                self.repo.save_workitem(domain_item)
                self.load_local_data(repo_name)
        else:
            dialog = CreateWorkItemDialog(self)
            idx = dialog.type_combo.findText(item_type)
            if idx >= 0:
                dialog.type_combo.setCurrentIndex(idx)
            
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
                    self.load_local_data(repo_name)

    def load_local_data(self, repo_name: str):
        # Read from SQLite
        items = self.repo.get_workitems_for_repo(repo_name=repo_name)
        self.workitem_model.update_data(items)
        logger.info(f"Loaded {len(items)} WorkItems locally for repo: {repo_name}")

    def on_repo_selected(self, item):
        repo_name = item.text().replace("☁️ ", "").replace("📁 ", "")
        if repo_name.startswith("---"):
            return
        self.current_repo = repo_name
        logger.info(f"UI Event: Repo clicked -> {repo_name}")
        self.load_local_data(repo_name)
        
        # Only sync if we have a token and it's an online repo
        if get_github_token() and not repo_name.startswith("📁"):
            logger.info(f"Spawning background GitHubSyncWorker for {repo_name}...")
            worker = GitHubSyncWorker(repo_name)
            worker.signals.result.connect(lambda ids: self.load_local_data(repo_name))
            worker.signals.error.connect(self.show_error)
            self.threadpool.start(worker)

    def show_error(self, err_msg):
        logger.error(f"Sync/System Error Dialog shown to user: {err_msg}")
        QMessageBox.critical(self, "Sync Error", err_msg)

    def on_delete_workitem_btn(self):
        if not self.current_workitem_id: return
        reply = QMessageBox.question(self, 'Delete WorkItem', 'Delete this WorkItem?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.repo.delete_workitem(self.current_workitem_id)
            self.load_local_data(self.current_repo)
            self.notes_browser.setHtml("")
            self.title_label.setText("")
            self.current_workitem_id = None

    def on_workitem_selected(self, index):
        domain_item = self.workitem_model.get_item(index.row())
        if domain_item:
            self.current_workitem_id = domain_item.id
            logger.info(f"UI Event: WorkItem selected -> #{domain_item.github_number or 'Local'} {domain_item.title}")
            self.title_label.setText(f"<h2>{sanitize_html(domain_item.title)}</h2>")
            
            # Show cloud sync toggle only for online repos
            try:
                db_repo = Repo.get(Repo.name == self.current_repo)
                is_online = not db_repo.is_offline
            except:
                is_online = False
            self.cloud_sync_check.setVisible(is_online)
            if is_online:
                sync_enabled = domain_item.sync_status != "no_sync"
                self.cloud_sync_check.blockSignals(True)
                self.cloud_sync_check.setChecked(sync_enabled)
                self.cloud_sync_check.blockSignals(False)
        if domain_item.item_type == "Incident":
            self.outage_btn.setVisible(True)
            # check notes for mitigation
            is_outage = False
            is_mitigated = False
            for n in domain_item.notes:
                if 'Outage officially declared' in n.content: is_outage = True
                if 'Outage mitigated' in n.content: is_mitigated = True
            
            try: self.outage_btn.clicked.disconnect()
            except RuntimeError: pass
            if is_outage and not is_mitigated:
                self.outage_btn.setText("✅ Mark Mitigated")
                self.outage_btn.setStyleSheet("background-color: #10b981; color: white; border-radius: 4px; padding: 4px 12px;")
                self.outage_btn.clicked.connect(self.on_mitigate_outage)
            else:
                self.outage_btn.setText("🚨 Declare Outage")
                self.outage_btn.setStyleSheet("background-color: #ef4444; color: white; border-radius: 4px; padding: 4px 12px;")
                self.outage_btn.clicked.connect(self.on_declare_outage)
        else:
            self.outage_btn.setVisible(False)
            
            self.status_combo.blockSignals(True)
            idx = self.status_combo.findText(domain_item.state)
            if idx >= 0:
                self.status_combo.setCurrentIndex(idx)
            self.status_combo.blockSignals(False)
            
            # Load notes
            html_content = ""
            for note in domain_item.notes:
                html_content += f"<p><i>{note.created_at.strftime('%Y-%m-%d %H:%M')}</i> &nbsp;&nbsp; <a href='delete_{note.id}' style='color:#ef4444; font-weight:bold; text-decoration:none;'>[ 🗑️ Delete Note ]</a><br>{format_note_content(note.content)}</p><hr>"
            
            self.notes_browser.setHtml(html_content)

    def refresh_workitem_view(self):
        if not self.current_workitem_id:
            self.details_card.setVisible(False)
            self.notes_header.setVisible(False)
            return
        domain_item = self.repo.get_workitem_by_id(self.current_workitem_id)
        if not domain_item:
            self.details_card.setVisible(False)
            self.notes_header.setVisible(False)
            return
            
        self.title_label.setText(f"<h2>{sanitize_html(domain_item.title)}</h2>")
        
        # Populate Details Card
        self.details_card.setVisible(True)
        self.notes_header.setVisible(True)
        self.type_badge.setText(domain_item.item_type)
        self.meta_text.setText(f"WorkItem #{domain_item.id} • Last Updated: {domain_item.local_updated_at.strftime('%Y-%m-%d %H:%M')}")
        
        desc = domain_item.body.strip() if domain_item.body else "<i>No description provided.</i>"
        self.description_text.setHtml(f"<div style='margin-bottom: 8px;'>{sanitize_html(desc)}</div>")

        if domain_item.item_type == "Incident":
            self.outage_btn.setVisible(True)
            # check notes for mitigation
            is_outage = False
            is_mitigated = False
            for n in domain_item.notes:
                if 'Outage officially declared' in n.content: is_outage = True
                if 'Outage mitigated' in n.content: is_mitigated = True
            
            try: self.outage_btn.clicked.disconnect()
            except RuntimeError: pass
            if is_outage and not is_mitigated:
                self.outage_btn.setText("✅ Mark Mitigated")
                self.outage_btn.setStyleSheet("background-color: #10b981; color: white; border-radius: 4px; padding: 4px 12px;")
                self.outage_btn.clicked.connect(self.on_mitigate_outage)
            else:
                self.outage_btn.setText("🚨 Declare Outage")
                self.outage_btn.setStyleSheet("background-color: #ef4444; color: white; border-radius: 4px; padding: 4px 12px;")
                self.outage_btn.clicked.connect(self.on_declare_outage)
        else:
            self.outage_btn.setVisible(False)
        self.status_combo.blockSignals(True)
        idx = self.status_combo.findText(domain_item.state)
        if idx >= 0:
            self.status_combo.setCurrentIndex(idx)
        self.status_combo.blockSignals(False)
        html_content = ""
        for note in domain_item.notes:
            # Skip old description notes from before the Details Card pivot to prevent duplication
            if note.content.startswith("[Description]\n") and domain_item.body in note.content:
                continue
            html_content += f"<p><i>{note.created_at.strftime('%Y-%m-%d %H:%M')}</i> &nbsp;&nbsp; <a href='delete_{note.id}' style='color:#ef4444; font-weight:bold; text-decoration:none;'>[ 🗑️ Delete Note ]</a><br>{format_note_content(note.content)}</p><hr>"
        self.notes_browser.setHtml(html_content)

    def on_note_anchor_clicked(self, url):
        link = url.toString()
        
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

            note_id = int(link.split("_")[1])
            reply = QMessageBox.question(self, "Delete Note", "Are you sure you want to delete this note?")
            if reply == QMessageBox.Yes:
                self.repo.delete_note(note_id)
                self.refresh_workitem_view()
                if self.current_repo:
                    self.load_local_data(self.current_repo)

    def on_sync_toggled(self, checked):
        if checked:
            self.sync_toggle.setText("🔄 Auto-Sync: ON")
            self.sync_toggle.setStyleSheet("color: #10b981; font-weight: bold;")
            self.sync_timer.start()
            self.perform_auto_sync() # Fire immediately on toggle
        else:
            self.sync_toggle.setText("🔄 Auto-Sync: OFF")
            self.sync_toggle.setStyleSheet("")
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
        logger.error(f"Auto-sync failed: {err}")

    def on_recycle_toggled(self, checked):
        repo_name = self.repo_combo.currentText() if self.is_classic_theme else (self.repo_list.currentItem().text().replace("☁️ ", "").replace("📁 ", "") if self.repo_list.currentItem() else None)
        if checked:
            self.title_label.setText("<h2>🗑️ Recycle Bin Mode</h2>")
            if repo_name and not repo_name.startswith("---"):
                items = self.repo.get_workitems_for_repo(repo_name, include_deleted=True)
                deleted_items = [i for i in items if i.deleted_at is not None]
                self.workitem_model.update_data(deleted_items)
            else:
                self.workitem_model.update_data([])
        else:
            if repo_name and not repo_name.startswith("---"):
                self.load_local_data(repo_name)
            else:
                self.title_label.setText("<h2>Select a Repo</h2>")

    def on_declare_outage(self):
        QMessageBox.warning(self, "Outage Declared", "Service Outage has been declared for this incident.")
        self.note_input.setText('Outage officially declared.')
        if self.note_type_combo.isVisible(): self.note_type_combo.setCurrentText('Active')
        self.on_submit_note()
        self.refresh_workitem_view()
        
    def on_mitigate_outage(self):
        QMessageBox.information(self, "Mitigated", "Outage has been marked as mitigated.")
        self.note_input.setText('[System] Outage mitigated.')
        if self.note_type_combo.isVisible(): self.note_type_combo.setCurrentText('Mitigated')
        self.on_submit_note()
        self.refresh_workitem_view()

    def on_status_changed(self, new_status):
        if not self.current_workitem_id:
            return
        domain_item = self.repo.get_workitem_by_id(self.current_workitem_id)
        if domain_item:
            logger.info(f"UI Event: Changed status of #{domain_item.id} to {new_status}")
            domain_item.state = new_status; domain_item.sync_status = "local"
            self.repo.save_workitem(domain_item)
            self.load_local_data(domain_item.repo_name)
            self.refresh_workitem_view()

    def on_cloud_sync_toggled(self, checked):
        if not self.current_workitem_id:
            return
        domain_item = self.repo.get_workitem_by_id(self.current_workitem_id)
        if domain_item:
            domain_item.sync_status = "PENDING_PUSH" if checked else "no_sync"
            self.repo.save_workitem(domain_item)
            logger.info(f"Cloud sync {'enabled' if checked else 'disabled'} for WorkItem #{domain_item.id}")

    def on_submit_note(self):
        if not self.current_workitem_id:
            return
            
        domain_item = self.repo.get_workitem_by_id(self.current_workitem_id)
        content = self.note_input.toPlainText().strip()
        if content and domain_item:
            note_type = self.note_type_combo.currentText()
            if note_type != "Note":
                content = f"[{note_type.upper()}] {content}"

            logger.info(f"UI Event: Submitting new note for WorkItem #{domain_item.id}")
            
            # 1. Save locally for instant UI response
            self.repo.add_note(domain_item.id, content); domain_item.sync_status = "local"; self.repo.save_workitem(domain_item)
            self.note_input.clear()
            
            # Refresh local view
            self.load_local_data(domain_item.repo_name)
            
            # Re-select the item to update notes view
            self.refresh_workitem_view()
            
            # 2. Push to GitHub in the background if it's synced to a GH issue
            if domain_item.github_number and get_github_token():
                logger.info(f"Spawning background GitHubPushWorker for issue #{domain_item.github_number}...")
                push_worker = GitHubPushWorker(
                    repo_name=domain_item.repo_name,
                    issue_number=domain_item.github_number,
                    comment_body=content
                )
                push_worker.signals.error.connect(lambda err: logger.error(f"Push Error: {err}"))
                push_worker.signals.result.connect(lambda res: logger.info(f"Successfully pushed comment to issue #{res[0]}"))
                self.threadpool.start(push_worker)

    def show_repo_context_menu(self, pos):
        item = self.repo_list.itemAt(pos)
        if not item: return
        menu = QMenu()
        delete_action = menu.addAction("🗑️ Delete Repository")
        action = menu.exec(self.repo_list.mapToGlobal(pos))
        if action == delete_action:
            repo_name = item.text().replace("☁️ ", "").replace("📁 ", "")
            reply = QMessageBox.question(self, "Delete Repo", f"Move {repo_name} to Recycle Bin?")
            if reply == QMessageBox.Yes:
                self.repo.delete_repo(repo_name)
                self.load_repos()

    def on_delete_repo_classic(self):
        repo_name = self.repo_combo.currentText()
        if not repo_name or repo_name.startswith("---"):
            return
        reply = QMessageBox.question(self, "Delete Repo", f"Move {repo_name} to Recycle Bin?")
        if reply == QMessageBox.Yes:
            self.repo.delete_repo(repo_name)
            self.load_repos()

    def show_workitem_context_menu(self, pos):
        index = self.workitem_view.indexAt(pos)
        if not index.isValid(): return
        menu = QMenu()
        
        is_recycle_mode = hasattr(self, 'recycle_toggle') and self.recycle_toggle.isChecked()
        
        if is_recycle_mode:
            restore_action = menu.addAction("♻️ Restore WorkItem")
            action = menu.exec(self.workitem_view.viewport().mapToGlobal(pos))
            if action == restore_action:
                wi_id = index.data(Qt.UserRole + 2)
                self.repo.restore_workitem(wi_id)
                self.on_recycle_toggled(True)
        else:
            delete_action = menu.addAction("🗑️ Delete WorkItem")
            action = menu.exec(self.workitem_view.viewport().mapToGlobal(pos))
            if action == delete_action:
                wi_id = index.data(Qt.UserRole + 2)
                reply = QMessageBox.question(self, "Delete WorkItem", "Move this WorkItem to Recycle Bin?")
                if reply == QMessageBox.Yes:
                    self.repo.delete_workitem(wi_id)
                    self.load_local_data(self.current_repo)

if __name__ == "__main__":
    logger.info("=== WORKITEMS APP STARTING ===")
    initialize_database()
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    
    _test_runner = None
    if "--ni" in sys.argv:
        try:
            from src.e2e_test import E2ETestRunner
            _test_runner = E2ETestRunner(window)
        except Exception as e:
            logger.error(f"Failed to start E2E test runner: {e}")
            
    exit_code = app.exec()
    logger.info(f"=== WORKITEMS APP CLOSING (Exit Code: {exit_code}) ===")
    sys.exit(exit_code)
