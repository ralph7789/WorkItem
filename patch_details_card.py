import re

with open("src/ui/main_window.py", "r") as f:
    content = f.read()

details_card_code = """
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
"""

# Replace the notes_browser instantiation with our new code
new_content = content.replace("        # Scrollable Notes\n        self.notes_browser = QTextBrowser()", details_card_code)

# We also need to update load_workitem_details to populate this card!
with open("src/ui/main_window.py", "w") as f:
    f.write(new_content)

print("Patched __init__ for details card!")
