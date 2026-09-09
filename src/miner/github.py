import os
import requests
from typing import List, Dict, Any

class GitHubClient:
    def __init__(self, token: str | None = None):
        self.token = token or os.getenv("GITHUB_TOKEN")
        if not self.token:
            raise ValueError("No se encontró el token de GitHub. Configura la variable GITHUB_TOKEN.")
        
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }

    def get_org_repositories(self, org: str, max_repos: int = 5) -> List[Dict[str, Any]]: #para ver hasta 5 repositorios
        repos = []
        page = 1
        per_page = 30

        while len(repos) < max_repos:
            url = f"https://api.github.com/orgs/{org}/repos?page={page}&per_page={per_page}&type=public"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code != 200:
                raise RuntimeError(f"Error al consultar la API de GitHub ({response.status_code}): {response.text}")

            data = response.json()
            if not data:
                break

            for repo in data:
                repos.append(repo)
                if len(repos) >= max_repos:
                    break
            
            page += 1

        return repos