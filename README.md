# reeco-web-repo-validator

Installation

Create a file named `.github_token` including the github API token

Install packages:

python3 -m pip install --upgrade pip



To get the sha

curl "https://api.github.com/repos/enridaga/colatti/git/trees/master" --header "Authorization: Bearer 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" -H "Accept: application/vnd.github+json"
