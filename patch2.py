with open("src/ui/main_window.py", "r") as f:
    content = f.read()

load_repos_old = """    def load_repos(self):
        self.repo_list.clear()
        
        # Block signals to prevent redundant loads when adding items to combo
        self.repo_combo.blockSignals(True)
        self.repo_combo.clear()
        
        repos = self.repo.get_all_repos()
        for r in repos:
            self.repo_list.addItem(r.name)
            self.repo_combo.addItem(r.name)
            
        self.repo_combo.blockSignals(False)"""

load_repos_new = """    def load_repos(self):
        self.repo_list.clear()
        self.repo_combo.blockSignals(True)
        self.repo_combo.clear()
        
        model = QStandardItemModel()
        self.repo_combo.setModel(model)
        
        repos = self.repo.get_all_repos()
        
        online = [r for r in repos if not r.is_offline]
        offline = [r for r in repos if r.is_offline]
        
        if online:
            header = QStandardItem("--- ☁️ Online ---")
            header.setEnabled(False)
            model.appendRow(header)
            for r in online:
                item = QStandardItem(r.name)
                model.appendRow(item)
                self.repo_list.addItem(f"☁️ {r.name}")
                
        if offline:
            header = QStandardItem("--- 📁 Offline ---")
            header.setEnabled(False)
            model.appendRow(header)
            for r in offline:
                item = QStandardItem(r.name)
                model.appendRow(item)
                self.repo_list.addItem(f"📁 {r.name}")
                
        self.repo_combo.blockSignals(False)"""
content = content.replace(load_repos_old, load_repos_new)

on_add_workitem_old = """    def on_add_workitem(self):
        if self.is_classic_theme:
            repo_name = self.repo_combo.currentText()
        else:
            if not self.repo_list.currentItem():
                self.show_error("Please select a repository first.")
                return
            repo_name = self.repo_list.currentItem().text().replace("☁️ ", "").replace("📁 ", "")
            
        if not repo_name or repo_name.startswith("---"):
            return
            
        title, ok = QInputDialog.getText(self, "New WorkItem", "Enter title:")
        if ok and title:
            # Simplistic for now, using a default type
            type_obj, _ = WorkItemType.get_or_create(name="Task")
            db_repo = Repo.get(Repo.name == repo_name)
            WorkItem.create(
                repo=db_repo,
                item_type=type_obj,
                title=title
            )
            self.load_local_data(repo_name)"""

on_add_workitem_new = """    def on_add_workitem(self):
        if self.is_classic_theme:
            repo_name = self.repo_combo.currentText()
        else:
            if not self.repo_list.currentItem():
                self.show_error("Please select a repository first.")
                return
            repo_name = self.repo_list.currentItem().text().replace("☁️ ", "").replace("📁 ", "")
            
        if not repo_name or repo_name.startswith("---"):
            return
            
        types = ["Task", "Incident", "BUG", "Roadmap"]
        item_type, ok = QInputDialog.getItem(self, "Select Type", "Type:", types, 0, False)
        if not ok or not item_type:
            return
            
        if item_type == "Roadmap":
            dialog = RoadmapCreationDialog(self)
            if dialog.exec():
                data = dialog.get_data()
                type_obj, _ = WorkItemType.get_or_create(name=item_type)
                db_repo = Repo.get(Repo.name == repo_name)
                WorkItem.create(
                    repo=db_repo,
                    item_type=type_obj,
                    title=data['title'],
                    type_metadata=data['type_metadata']
                )
                self.load_local_data(repo_name)
        else:
            title, ok = QInputDialog.getText(self, "New WorkItem", "Enter title:")
            if ok and title:
                type_obj, _ = WorkItemType.get_or_create(name=item_type)
                db_repo = Repo.get(Repo.name == repo_name)
                WorkItem.create(
                    repo=db_repo,
                    item_type=type_obj,
                    title=title
                )
                self.load_local_data(repo_name)"""
content = content.replace(on_add_workitem_old, on_add_workitem_new)

with open("src/ui/main_window.py", "w") as f:
    f.write(content)
