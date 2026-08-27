with open("src/ui/main_window.py", "r") as f:
    content = f.read()

toolbar_code = """        # Spacer to push button to the right
        spacer = QWidget()
        spacer.setSizePolicy(spacer.sizePolicy().Policy.Expanding, spacer.sizePolicy().Policy.Expanding)
        toolbar.addWidget(spacer)"""

new_toolbar_code = """        # Spacer to push button to the right
        spacer = QWidget()
        spacer.setSizePolicy(spacer.sizePolicy().Policy.Expanding, spacer.sizePolicy().Policy.Expanding)
        toolbar.addWidget(spacer)
        
        self.sync_toggle = QCheckBox("🔄 Auto-Sync: OFF")
        self.sync_toggle.toggled.connect(self.on_sync_toggled)
        toolbar.addWidget(self.sync_toggle)"""

if toolbar_code in content:
    content = content.replace(toolbar_code, new_toolbar_code)
    with open("src/ui/main_window.py", "w") as f:
        f.write(content)
    print("Patched toolbar to restore sync_toggle!")
else:
    print("Failed to find toolbar_code")
