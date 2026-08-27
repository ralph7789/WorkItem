import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QToolBar, QComboBox, QPushButton, QWidget

class Win(QMainWindow):
    def __init__(self):
        super().__init__()
        tb = QToolBar()
        self.addToolBar(tb)
        
        self.combo = QComboBox()
        self.combo.addItems(["Repo 1", "Repo 2"])
        
        # When you add a widget to a toolbar, you get a QAction
        self.combo_action = tb.addWidget(self.combo)
        self.combo_action.setVisible(False)
        
        btn = QPushButton("Toggle")
        btn.clicked.connect(self.toggle)
        tb.addWidget(btn)
        
    def toggle(self):
        self.combo_action.setVisible(not self.combo_action.isVisible())

app = QApplication([])
w = Win()
w.show()
sys.exit(app.exec())
