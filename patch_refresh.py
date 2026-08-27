import re

with open("src/ui/main_window.py", "r") as f:
    content = f.read()

replacement = """    def refresh_workitem_view(self):
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

        if domain_item.item_type == "Incident":"""

content = content.replace("""    def refresh_workitem_view(self):
        if not self.current_workitem_id:
            return
        domain_item = self.repo.get_workitem_by_id(self.current_workitem_id)
        if not domain_item:
            return
        self.title_label.setText(f"<h2>{sanitize_html(domain_item.title)}</h2>")
        if domain_item.item_type == "Incident":""", replacement)

# Now, we should filter out the old "[Description]" notes if they exist, so they don't double-render
note_filter_old = """        html_content = ""
        for note in domain_item.notes:
            html_content += f"<p><i>{note.created_at.strftime('%Y-%m-%d %H:%M')}</i> &nbsp;&nbsp; <a href='delete_{note.id}' style='color:#ef4444; font-weight:bold; text-decoration:none;'>[ 🗑️ Delete Note ]</a><br>{format_note_content(note.content)}</p><hr>"
        self.notes_browser.setHtml(html_content)"""

note_filter_new = """        html_content = ""
        for note in domain_item.notes:
            # Skip old description notes from before the Details Card pivot to prevent duplication
            if note.content.startswith("[Description]\\n") and domain_item.body in note.content:
                continue
            html_content += f"<p><i>{note.created_at.strftime('%Y-%m-%d %H:%M')}</i> &nbsp;&nbsp; <a href='delete_{note.id}' style='color:#ef4444; font-weight:bold; text-decoration:none;'>[ 🗑️ Delete Note ]</a><br>{format_note_content(note.content)}</p><hr>"
        self.notes_browser.setHtml(html_content)"""

content = content.replace(note_filter_old, note_filter_new)

with open("src/ui/main_window.py", "w") as f:
    f.write(content)

print("Patched refresh_workitem_view!")
