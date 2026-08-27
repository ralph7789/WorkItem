import traceback
from PySide6.QtCore import QRunnable, QObject, Signal, Slot
from github import Github
from github.GithubException import GithubException
from src.core.security import get_github_token
from src.repositories.workitem_repo import WorkItemRepository
from src.core.domain import DomainWorkItem
from src.models.database import db

class WorkerSignals(QObject):
    """
    Defines the signals available from a running worker thread.
    Supported signals are:
    - finished: No data
    - error: `str` containing the error message
    - result: `list` of synced WorkItem IDs or success message
    """
    finished = Signal()
    error = Signal(str)
    result = Signal(list)

import json
from datetime import datetime

class GitHubSyncWorker(QRunnable):
    """
    Worker thread to fetch and push GitHub repositories' WorkItems via .wi files in the background.
    """
    def __init__(self, repo_name: str):
        super().__init__()
        self.repo_name = repo_name
        self.signals = WorkerSignals()
        self.repo = WorkItemRepository()

    def serialize_workitem(self, wi: DomainWorkItem) -> str:
        data = {
            "title": wi.title,
            "item_type": wi.item_type,
            "body": wi.body,
            "state": wi.state,
            "type_metadata": wi.type_metadata,
            "notes": [
                {
                    "content": n.content,
                    "created_at": n.created_at.isoformat() if n.created_at else None,
                    "metadata": n.metadata
                } for n in wi.notes if not n.deleted_at
            ]
        }
        return json.dumps(data, indent=2)

    def deserialize_workitem(self, data: dict, sha: str) -> DomainWorkItem:
        wi = DomainWorkItem(
            id=0,
            repo_name=self.repo_name,
            item_type=data.get("item_type", "Development"),
            title=data.get("title", "Untitled"),
            body=data.get("body", ""),
            state=data.get("state", "open"),
            type_metadata=data.get("type_metadata", {}),
            sync_status="SYNCED",
            github_sha=sha
        )
        return wi

    def sanitize_filename(self, title: str) -> str:
        clean = "".join(c if c.isalnum() or c in (" ", "-", "_") else "" for c in title)
        return clean.strip().replace(" ", "_") + ".wi"

    @Slot()
    def run(self):
        token = get_github_token()
        if not token:
            self.signals.error.emit("No GitHub token found in Keyring.")
            self.signals.finished.emit()
            return
            
        try:
            gh = Github(token)
            gh_repo = gh.get_repo(self.repo_name)
            default_branch = gh_repo.default_branch
            
            # --- 1. PUSH Pending Local Changes ---
            with db.connection_context():
                local_items = self.repo.get_workitems_for_repo(self.repo_name)
                for local_wi in local_items:
                    if local_wi.sync_status in ["PENDING_PUSH", "local"]:
                        print("Attempting to push:", local_wi.title)
                        filename = self.sanitize_filename(local_wi.title)
                        path = f"WorkItems/{filename}"
                        content = self.serialize_workitem(local_wi)
                        
                        try:
                            if local_wi.github_sha:
                                # Update existing
                                res = gh_repo.update_file(path, f"Update WorkItem: {local_wi.title}", content, local_wi.github_sha, branch=default_branch)
                                local_wi.github_sha = res['commit'].sha
                            else:
                                # Try to create
                                try:
                                    res = gh_repo.create_file(path, f"Create WorkItem: {local_wi.title}", content, branch=default_branch)
                                    local_wi.github_sha = res['commit'].sha
                                except GithubException as e:
                                    # If it already exists, we must get the SHA first
                                    if e.status == 422:
                                        file_content = gh_repo.get_contents(path, ref=default_branch)
                                        res = gh_repo.update_file(path, f"Update WorkItem: {local_wi.title}", content, file_content.sha, branch=default_branch)
                                        local_wi.github_sha = res['commit'].sha
                                    else:
                                        raise e
                                        
                            local_wi.sync_status = "SYNCED"
                            self.repo.save_workitem(local_wi)
                        except Exception as e:
                            print(f"Error pushing WorkItem {local_wi.title}: {e}")

            # --- 2. PULL Remote Changes ---
            synced_items = []
            try:
                contents = gh_repo.get_contents("WorkItems", ref=default_branch)
                if not isinstance(contents, list):
                    contents = [contents]
            except GithubException as e:
                if e.status == 404:
                    contents = []
                else:
                    raise e
                    
            with db.connection_context():
                local_items = self.repo.get_workitems_for_repo(self.repo_name)
                local_title_map = {wi.title: wi for wi in local_items}
                
                for file in contents:
                    if not file.name.endswith('.wi'):
                        continue
                        
                    # Fetch file content
                    try:
                        file_data = json.loads(file.decoded_content.decode('utf-8'))
                        remote_sha = file.sha
                        
                        # Match by title for now
                        title = file_data.get("title", file.name.replace(".wi", ""))
                        existing_wi = local_title_map.get(title)
                        
                        if existing_wi:
                            # If remote SHA is different and we aren't pending push
                            if existing_wi.github_sha != remote_sha and existing_wi.sync_status not in ["PENDING_PUSH", "local"]:
                                existing_wi.item_type = file_data.get("item_type", existing_wi.item_type)
                                existing_wi.body = file_data.get("body", existing_wi.body)
                                existing_wi.state = file_data.get("state", existing_wi.state)
                                existing_wi.type_metadata = file_data.get("type_metadata", existing_wi.type_metadata)
                                existing_wi.github_sha = remote_sha
                                existing_wi.sync_status = "SYNCED"
                                saved_wi = self.repo.save_workitem(existing_wi)
                                synced_items.append(saved_wi.id)
                        else:
                            # Create new local workitem
                            new_wi = self.deserialize_workitem(file_data, remote_sha)
                            saved_wi = self.repo.save_workitem(new_wi)
                            
                            # Add notes
                            for note_data in file_data.get("notes", []):
                                created_at = None
                                if note_data.get("created_at"):
                                    try:
                                        created_at = datetime.fromisoformat(note_data["created_at"])
                                    except:
                                        pass
                                self.repo.add_note(saved_wi.id, note_data.get("content", ""), metadata=note_data.get("metadata", {}))
                                
                            synced_items.append(saved_wi.id)
                            
                    except Exception as e:
                        print(f"Error parsing .wi file {file.name}: {e}")
                        
            self.signals.result.emit(synced_items)
            
        except GithubException as e:
            self.signals.error.emit(f"GitHub API Error: {e.status}")
        except Exception as e:
            self.signals.error.emit(f"Sync failed: {str(e)}\n{traceback.format_exc()}")
        finally:
            self.signals.finished.emit()

class GitHubPushWorker(QRunnable):
    # Deprecated: GitHubSyncWorker handles pushing via PENDING_PUSH sync status.
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.signals = WorkerSignals()
    @Slot()
    def run(self):
        self.signals.finished.emit()

class GitHubRepoListWorker(QRunnable):
    """
    Worker thread to fetch all repositories accessible by the user.
    """
    def __init__(self):
        super().__init__()
        self.signals = WorkerSignals()
        self.repo = WorkItemRepository()

    @Slot()
    def run(self):
        token = get_github_token()
        if not token:
            self.signals.error.emit("No GitHub token found in Keyring.")
            self.signals.finished.emit()
            return
            
        try:
            gh = Github(token)
            repos = gh.get_user().get_repos(sort='updated')
            
            repo_names = []
            with db.connection_context():
                from src.models.schema import Repo
                for i, r in enumerate(repos):
                    if i >= 15: # Cap it at 15 recently updated repos to avoid long load times
                        break
                    Repo.get_or_create(name=r.full_name, defaults={'owner': r.owner.login, 'github_id': str(r.id)})
                    repo_names.append(r.full_name)
                    
            self.signals.result.emit(repo_names)
            
        except GithubException as e:
            self.signals.error.emit(f"GitHub API Error: {e.status}")
        except Exception as e:
            self.signals.error.emit(f"Repo fetch failed: {str(e)}\n{traceback.format_exc()}")
        finally:
            self.signals.finished.emit()

