---
component-id: reeco-web-repo-validator
name: REECO repository validator
description: A web applciaiton to test annotations on your repository
doi: 10.5281/zenodo.10655175
type: Application
resource: http://reeco.kmi.open.ac.uk
related-components:
- reuses:
  - reeco-python
---
# reeco-web-repo-validator

Installation

Create a file named `.github_token` including the github API token

Install packages:

python3 -m pip install --upgrade pip



To get the sha

curl "https://api.github.com/repos/owner>/repository/git/trees/master" --header "Authorization: Bearer ghp_XXXXXXXXXXXXXXXXXXXXXXX" -H "Accept: application/vnd.github+json"
