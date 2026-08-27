import re

with open("src/core/github_sync.py", "r") as f:
    content = f.read()

# Replace GitHubSyncWorker with a file-based sync engine
sync_worker_old = """class GitHubSyncWorker(QRunnable):
    def __init__(self, repo_name: str):
        super().__init__()
        self.repo_name = repo_name
        self.signals = WorkerSignals()
        self.repo_db = WorkItemRepository()

    @Slot()
    def run(self):
        try:
            token = get_github_token()
            if not token:
                self.signals.error.emit("No GitHub token found.")
                return

            g = Github(token)
            gh_repo = g.get_repo(self.repo_name)
            
            # Fetch all issues from GitHub
            issues = gh_repo.get_issues(state='all')
            
            # Update local database
            updated_ids = []
            for issue in issues:
                # Map to DomainWorkItem
                item_type = "Bug" if "bug" in [l.name.lower() for l in issue.labels] else "Development"
                
                domain_item = DomainWorkItem(
                    id=None,
                    repo_name=self.repo_name,
                    item_type=item_type,
                    title=issue.title,
                    body=issue.body or "",
                    github_id=issue.id,
                    github_number=issue.number,
                    state=issue.state,
                    sync_status="synced",
                    local_updated_at=issue.updated_at
                )
                
                # Check if it exists locally to update instead of insert
                existing = self.repo_db.get_workitems_for_repo(self.repo_name)
                for local_item in existing:
                    if local_item.github_id == issue.id:
                        domain_item.id = local_item.id
                        break
                        
                saved = self.repo_db.save_workitem(domain_item)
                updated_ids.append(saved.id)
                
                # We would also fetch comments and map them to Notes here in a full implementation
                
            self.signals.result.emit(updated_ids)
            
        except Exception as e:
            self.signals.error.emit(str(e))"""
            
sync_worker_new = """class GitHubSyncWorker(QRunnable):
    def __init__(self, repo_name: str):
        super().__init__()
        self.repo_name = repo_name
        self.signals = WorkerSignals()
        self.repo_db = WorkItemRepository()

    @Slot()
    def run(self):
        try:
            token = get_github_token()
            if not token:
                self.signals.error.emit("No GitHub token found.")
                return

            g = Github(token)
            gh_repo = g.get_repo(self.repo_name)
            
            import json
            from src.core.domain import DomainWorkItem
            from datetime import datetime, timezone
            
            updated_ids = []
            
            # 1. PULL: Fetch all .wi files from the WorkItems directory
            try:
                contents = gh_repo.get_contents("WorkItems")
                for file_content in contents:
                    if file_content.name.endswith(".wi"):
                        wi_json = json.loads(file_content.decoded_content.decode("utf-8"))
                        
                        domain_item = DomainWorkItem(
                            id=None,
                            repo_name=self.repo_name,
                            item_type=wi_json.get("type", "Development"),
                            title=wi_json.get("title", "Untitled"),
                            body=wi_json.get("body", ""),
                            github_id=None,
                            github_number=None,
                            state=wi_json.get("state", "open"),
                            sync_status="synced",
                            local_updated_at=datetime.fromisoformat(wi_json.get("updated_at", datetime.now(timezone.utc).isoformat())),
                            github_sha=file_content.sha,
                            type_metadata=wi_json.get("metadata", {}),
                            deleted_at=None
                        )
                        
                        if wi_json.get("deleted_at"):
                            domain_item.deleted_at = datetime.fromisoformat(wi_json["deleted_at"])
                            
                        # Check if it exists locally to update
                        existing = self.repo_db.get_workitems_for_repo(self.repo_name, include_deleted=True)
                        for local_item in existing:
                            if local_item.title == domain_item.title: # Use title as identifier for now since we don't have github_id
                                domain_item.id = local_item.id
                                break
                                
                        saved = self.repo_db.save_workitem(domain_item)
                        updated_ids.append(saved.id)
            except Exception as e:
                # Directory might not exist yet
                pass
                
            # 2. PUSH: Find local dirty items and push them
            local_items = self.repo_db.get_workitems_for_repo(self.repo_name, include_deleted=True)
            for item in local_items:
                if item.sync_status != "synced":
                    filename = f"WorkItems/{item.title.replace(' ', '_')}.wi"
                    
                    wi_json = {
                        "title": item.title,
                        "type": item.item_type,
                        "body": item.body,
                        "state": item.state,
                        "metadata": item.type_metadata,
                        "updated_at": item.local_updated_at.isoformat(),
                        "deleted_at": item.deleted_at.isoformat() if item.deleted_at else None
                    }
                    
                    content_str = json.dumps(wi_json, indent=2)
                    
                    try:
                        if item.github_sha:
                            res = gh_repo.update_file(filename, f"Update {item.title}", content_str, item.github_sha)
                            item.github_sha = res["commit"].sha
                        else:
                            res = gh_repo.create_file(filename, f"Create {item.title}", content_str)
                            item.github_sha = res["commit"].sha
                            
                        item.sync_status = "synced"
                        self.repo_db.save_workitem(item)
                    except Exception as push_err:
                        print(f"Error pushing {item.title}: {push_err}")
                        
            self.signals.result.emit(updated_ids)
            
        except Exception as e:
            self.signals.error.emit(str(e))"""
content = content.replace(sync_worker_old, sync_worker_new)

with open("src/core/github_sync.py", "w") as f:
    f.write(content)
