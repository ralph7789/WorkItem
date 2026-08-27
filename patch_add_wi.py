with open("src/ui/main_window.py", "r") as f:
    content = f.read()

old_code = """                    self.repo.save_workitem(domain_item)
                    
                    if data["body"]:
                        saved_item = self.repo.get_workitems_for_repo(repo_name)[0]
                        self.repo.add_note(saved_item.id, f"[Description]\\n{data['body']}")
                        
                    self.load_local_data(repo_name)"""
                    
new_code = """                    self.repo.save_workitem(domain_item)
                    self.load_local_data(repo_name)"""

content = content.replace(old_code, new_code)
with open("src/ui/main_window.py", "w") as f:
    f.write(content)
print("Removed old description note insertion!")
