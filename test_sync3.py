from src.core.github_sync import GitHubSyncWorker
from src.repositories.workitem_repo import WorkItemRepository
from src.core.domain import DomainWorkItem
repo = WorkItemRepository()
wi = DomainWorkItem(id=0, repo_name="ralph7789/WorkItem", item_type="Development", title="Test Sync Git", body="test body", state="open", sync_status="local")
wi = repo.save_workitem(wi)
print("Created WI:", wi.id)

worker = GitHubSyncWorker("ralph7789/WorkItem")
worker.run()
print("Worker finished")
