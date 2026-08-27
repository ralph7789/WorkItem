with open("src/ui/main_window.py", "r") as f:
    content = f.read()

display_old = """            # Load notes
            html_content = ""
            for note in domain_item.notes:
                html_content += f"<p><i>{note.created_at.strftime('%Y-%m-%d %H:%M')}</i><br>{sanitize_html(note.content)}</p><hr>"
            self.notes_browser.setHtml(html_content)
"""

display_new = """            # Load notes or properties
            html_content = ""
            if domain_item.item_type == "Roadmap":
                self.note_input.setVisible(False)
                self.note_submit_btn.setVisible(False)
                if hasattr(self, 'note_type_combo'): self.note_type_combo.setVisible(False)
                
                try:
                    import json
                    meta = json.loads(domain_item.type_metadata)
                    html_content = f"<h3>Roadmap Details</h3>"
                    html_content += f"<b>Version:</b> {sanitize_html(meta.get('version', ''))}<br>"
                    html_content += f"<b>Stage:</b> {sanitize_html(meta.get('stage', ''))}<br>"
                    html_content += f"<b>Rollout Date:</b> {sanitize_html(meta.get('rollout_date', ''))}<br>"
                    deps = ", ".join(meta.get('dependencies', []))
                    html_content += f"<b>Dependencies:</b> {sanitize_html(deps)}<br>"
                    html_content += f"<b>Feature:</b> {sanitize_html(meta.get('feature', ''))}<br>"
                    html_content += f"<b>Description:</b><br>{sanitize_html(meta.get('description', ''))}<br><br>"
                    html_content += f"<b>Dev Notes:</b><br>{sanitize_html(meta.get('dev_notes', ''))}<br>"
                except Exception as e:
                    html_content = f"<p>Error loading roadmap metadata: {e}</p>"
            else:
                self.note_input.setVisible(True)
                self.note_submit_btn.setVisible(True)
                if hasattr(self, 'note_type_combo'): self.note_type_combo.setVisible(True)
                for note in domain_item.notes:
                    # Parse cross references like #Roadmap-123 or #BUG-42
                    import re
                    content_html = sanitize_html(note.content)
                    content_html = re.sub(r'#([A-Za-z]+)-(\d+)', r'<b style="color: #60a5fa;">#\1-\2</b>', content_html)
                    html_content += f"<p><i>{note.created_at.strftime('%Y-%m-%d %H:%M')}</i><br>{content_html}</p><hr>"
            
            self.notes_browser.setHtml(html_content)
"""
content = content.replace(display_old, display_new)

with open("src/ui/main_window.py", "w") as f:
    f.write(content)
