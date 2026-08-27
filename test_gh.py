from src.core.security import get_github_token
from github import Github
token = get_github_token()
gh = Github(token)
gh_repo = gh.get_repo("ralph7789/WorkItem")
contents = gh_repo.get_contents("WorkItems", ref=gh_repo.default_branch)
for file in contents:
    print(file.name)
