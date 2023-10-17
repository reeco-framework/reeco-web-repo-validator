from flask import Flask, render_template, redirect, url_for, request, session, make_response
from flask_bootstrap import Bootstrap

from flask_wtf import FlaskForm, CSRFProtect
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length, URL

from pathlib import Path

import requests
import frontmatter
#from github import Github

import yaml
import secrets

from reeco import Validator

app = Flask(__name__)
app.secret_key = secrets.token_urlsafe(16)

# Bootstrap-Flask requires this line
bootstrap = Bootstrap(app)

GITHUB_TOKEN = Path(".GITHUB_TOKEN").read_text().strip()

# Github
#GH = Github(GITHUB_TOKEN)
# Flask-WTF requires this line
csrf = CSRFProtect(app)

###
VALIDATOR = Validator()
###


class URLForm(FlaskForm):
    url = StringField('GitHub repository URL', validators=[DataRequired(), URL()])
    tree = StringField('Tree (defaults to "main")')
    submit = SubmitField('Submit')

@app.route('/', methods=['GET', 'POST'])
def indexAction():
    form = URLForm()
    message = ""
    if form.validate_on_submit():
        url = form.url.data
        return redirect( url_for('validateAction', repo=url) )
    else:
        message = "Please enter a valid URL"
    return render_template('index.html', form=form, message=message)

@app.route('/validate',methods = ['GET'])
def validateAction():
    repo = request.args.get('url')
    tree = request.args.get('tree')
    if repo is None:
        resp = make_response("Argument not provided: repo", 400)
        return resp
    else:
        if tree is None or tree == "":
            tree = 'main'
        files = getFiles(repo, tree)
        # print("files:",len(files))
        #print("files obj: ", files)
        # Only keep md files
        files = [item for item in files if item['path'].endswith('.md') ]
        # print(len(files))
        if len(files) > 0:
            validation=validate(files)
        else:
            validation={}
        return render_template('validate.html', repo=repo, tree=tree, files=files, validation=validation)

def getFiles(repo, tree):
    repo = repo.replace('https://github.com/','')
    url = "https://api.github.com/repos/" + repo + "/git/trees/" + tree + "?recursive=1"
    #url = "https://api.github.com/search/code?q=extension:md+repo:" + repo
    headers = {'Authorization': 'Bearer ' + GITHUB_TOKEN,
        'Accept': 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28'}
    try:
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            return r.json()['tree']
        else:
            addMessage(3, "Can't connect to the repo: " + r.json()['message'])
    except Exception as ex:
        print(str(ex))
        addMessage(3, "Error while connecting to URL: " + str(url) + " " + str(ex))
    return {}


def validate(files):
    report = {}
    for fi in files:
        content = getFileContent(fi['url'])
        report[fi['path']] = validateFileContent(content)
    return report

def getFileContent(url):
    #print(url)
    headers = {'Authorization': 'Bearer ' + GITHUB_TOKEN, "Accept": "application/vnd.github.raw"}
    r = requests.get(url, headers=headers)
    content = ""
    if r.status_code == 200:
        content = r.text
        #download_url = r.json()['download_url']
        #         try:
        #             down = requests.get(download_url, headers=headers)
        #             if down.status_code == 200:
        #                 return down.text
        #             else:
        #                 addMessage(3, "Cannot access URL: " + download_url)
        #                 print("Cannot access URL " + download_url + " - status was " + down.status_code)
        #         except Exception as e:
        #             # Error
        #             print(e)
    else:
        addMessage(3, "Cannot access URL: " + url)
        print("Cannot access URL " + url + " - status was " + r.status_code)
    return content

def validateFileContent(content):
    report = []
    ## Parse content
    try:
        annotations, content = frontmatter.parse(content)
        yamltxt = yaml.dump(annotations)
    except Exception as e:
        print(str(e))
        report = {'error': [MalformedFileError()]}
        return ["", report]
    ## Start validation
    if 'component-id' in annotations.keys():
        ### Validate as component
        report = VALIDATOR.asComponent(annotations)
    elif 'container-id' in annotations.keys():
        ### Validate as container
        report = VALIDATOR.asContainer(annotations)
    else:
        report = {'info': [NoAnnotationsError()]}
    return [yamltxt, report]

class NoAnnotationsError(Exception):
    def __init__(self):
        # Call the base class constructor with the parameters it needs
        super().__init__("No ecosystem annotations found")
        self.autos = ["Not a component:"]
        self.code = "no annotations found"

class MalformedFileError(Exception):
    def __init__(self):
        # Call the base class constructor with the parameters it needs
        super().__init__("Malformed content, cannot parse Markdown/YAML")
        self.autos = ["Malformed content:"]
        self.code = "error while attempting to parse content"

# Severity:
# - Info: 1
# - Warn: 2
# - Alert: 3
# - Error: 4
def addMessage(severity, message):
    if 'messages' not in session:
        session['messages'] = []
    #print(session)
    session['messages'].append({'severity': severity, 'message': message})
    return True

def clearMessages():
    session.pop('messages', None)
    return True

if __name__ == "__main__":
    from waitress import serve
    serve(app, host="127.0.0.1", port=5000)