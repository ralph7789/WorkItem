from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit, 
    QComboBox, QPushButton
)

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
