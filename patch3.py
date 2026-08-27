with open("src/ui/main_window.py", "r") as f:
    content = f.read()

context_menus = """
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

    def show_workitem_context_menu(self, pos):
        index = self.workitem_view.indexAt(pos)
        if not index.isValid(): return
        menu = QMenu()
        delete_action = menu.addAction("🗑️ Delete WorkItem")
        action = menu.exec(self.workitem_view.viewport().mapToGlobal(pos))
        if action == delete_action:
            wi_id = index.data(Qt.UserRole + 2)
            reply = QMessageBox.question(self, "Delete WorkItem", "Move this WorkItem to Recycle Bin?")
            if reply == QMessageBox.Yes:
                self.repo.delete_workitem(wi_id)
                self.load_local_data(self.current_repo)
"""
# inject at the end of class
content = content + context_menus

with open("src/ui/main_window.py", "w") as f:
    f.write(content)
