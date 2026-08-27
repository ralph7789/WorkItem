from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from PySide6.QtCore import Qt
import webbrowser

class GitHubPATDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("GitHub Login")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        label = QLabel("Enter your GitHub Personal Access Token (PAT):")
        layout.addWidget(label)
        
        input_layout = QHBoxLayout()
        self.token_input = QLineEdit()
        self.token_input.setEchoMode(QLineEdit.EchoMode.Password)
        input_layout.addWidget(self.token_input)
        
        self.help_btn = QPushButton("?")
        self.help_btn.setToolTip("How to get a PAT")
        self.help_btn.setFixedWidth(30)
        self.help_btn.clicked.connect(self.show_help)
        input_layout.addWidget(self.help_btn)
        
        layout.addLayout(input_layout)
        
        btn_layout = QHBoxLayout()
        self.ok_btn = QPushButton("OK")
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)
        
    def show_help(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("How to get a PAT")
        msg.setText(
            "1. Go to GitHub Settings > Developer Settings > Personal Access Tokens (Tokens (classic)).\n"
            "2. Click 'Generate new token'.\n"
            "3. Give it the 'repo' scope.\n"
            "4. Copy the token and paste it here."
        )
        link_label = QLabel("<a href='https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens'>Official GitHub Guide</a>")
        link_label.setOpenExternalLinks(True)
        msg.layout().addWidget(link_label, 1, 1)
        msg.exec()
        
    def get_token(self):
        return self.token_input.text()
