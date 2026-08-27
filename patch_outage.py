with open("src/ui/main_window.py", "r") as f:
    content = f.read()

import re

outage_logic_old = """        if domain_item.item_type == "Incident":
            self.outage_btn.setVisible(True)
        else:
            self.outage_btn.setVisible(False)"""

outage_logic_new = """        if domain_item.item_type == "Incident":
            self.outage_btn.setVisible(True)
            # check notes for mitigation
            is_outage = False
            is_mitigated = False
            for n in domain_item.notes:
                if 'Outage officially declared' in n.content: is_outage = True
                if 'Outage mitigated' in n.content: is_mitigated = True
            
            self.outage_btn.disconnect()
            if is_outage and not is_mitigated:
                self.outage_btn.setText("✅ Mark Mitigated")
                self.outage_btn.setStyleSheet("background-color: #10b981; color: white; border-radius: 4px; padding: 4px 12px;")
                self.outage_btn.clicked.connect(self.on_mitigate_outage)
            else:
                self.outage_btn.setText("🚨 Declare Outage")
                self.outage_btn.setStyleSheet("background-color: #ef4444; color: white; border-radius: 4px; padding: 4px 12px;")
                self.outage_btn.clicked.connect(self.on_declare_outage)
        else:
            self.outage_btn.setVisible(False)"""

content = content.replace(outage_logic_old, outage_logic_new)

declare_old = """    def on_declare_outage(self):
        QMessageBox.warning(self, "Outage Declared", "Service Outage has been declared for this incident.")
        # We would update metadata here
        self.note_input.setText('Outage officially declared.'); self.note_type_combo.setCurrentText('Active'); self.on_submit_note()"""

declare_new = """    def on_declare_outage(self):
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
        self.refresh_workitem_view()"""

content = content.replace(declare_old, declare_new)

with open("src/ui/main_window.py", "w") as f:
    f.write(content)
