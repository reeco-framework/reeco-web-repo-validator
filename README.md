# reeco-web-repo-validator

Installation

Create a file named `.github_token` including the github API token

Install packages:

python3 -m pip install --upgrade pip



To get the sha

curl "https://api.github.com/repos/owner>/repository/git/trees/master" --header "Authorization: Bearer ghp_XXXXXXXXXXXXXXXXXXXXXXX" -H "Accept: application/vnd.github+json"
