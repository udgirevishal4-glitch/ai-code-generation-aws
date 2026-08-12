import os
import requests

def get_issues(repo: str):
    token = os.getenv('GITHUB_TOKEN')
    headers = {'Accept': 'application/vnd.github+json'}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    url = f'https://api.github.com/repos/{repo}/issues'
    response = requests.get(url, params={'state': 'open', 'per_page': 20}, headers=headers, timeout=15)
    response.raise_for_status()
    return [i for i in response.json() if 'pull_request' not in i]
