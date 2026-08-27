from PySide6.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QLineEdit, QComboBox, QDateEdit, QTextEdit, QDialogButtonBox, QMessageBox
from PySide6.QtCore import QDate
import json

class RoadmapCreationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create Roadmap Item")
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        
        self.title_input = QLineEdit()
        self.version_input = QLineEdit()
        
        self.stage_combo = QComboBox()
        self.stage_combo.addItems(["Draft", "Planning", "In Development", "Beta", "GA/Released"])
        
        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate())
        
        self.deps_input = QLineEdit()
        self.deps_input.setPlaceholderText("e.g. 12, 15 (comma separated IDs)")
        
        self.feature_input = QLineEdit()
        
        self.desc_input = QTextEdit()
        self.desc_input.setMinimumHeight(100)
        
        self.dev_notes_input = QTextEdit()
        self.dev_notes_input.setMinimumHeight(100)
        self.dev_notes_input.setStyleSheet("background-color: #2a2a35;")
        
        form_layout.addRow("Title *", self.title_input)
        form_layout.addRow("Version *", self.version_input)
        form_layout.addRow("Stage", self.stage_combo)
        form_layout.addRow("Rollout Date", self.date_input)
        form_layout.addRow("Dependencies", self.deps_input)
        form_layout.addRow("Feature", self.feature_input)
        form_layout.addRow("Description", self.desc_input)
        form_layout.addRow("Dev Notes", self.dev_notes_input)
        
        layout.addLayout(form_layout)
        
        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.accepted.connect(self.validate_and_accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)
        
    def validate_and_accept(self):
        if not self.title_input.text().strip():
            QMessageBox.warning(self, "Validation Error", "Title is required.")
            return
        if not self.version_input.text().strip():
            QMessageBox.warning(self, "Validation Error", "Version is required.")
            return
        self.accept()
        
    def get_data(self):
        deps = [d.strip() for d in self.deps_input.text().split(',') if d.strip()]
        return {
            "title": self.title_input.text().strip(),
            "type_metadata": json.dumps({
                "version": self.version_input.text().strip(),
                "stage": self.stage_combo.currentText(),
                "rollout_date": self.date_input.date().toString("yyyy-MM-dd"),
                "dependencies": deps,
                "feature": self.feature_input.text().strip(),
                "description": self.desc_input.toPlainText().strip(),
                "dev_notes": self.dev_notes_input.toPlainText().strip()
            })
        }
