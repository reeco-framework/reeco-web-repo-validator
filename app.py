from flask import Flask, render_template, redirect, url_for, request, session
from flask_bootstrap import Bootstrap

from flask_wtf import FlaskForm, CSRFProtect
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length, URL

from pathlib import Path

import requests
import frontmatter
#from github import Github

import secrets

from validator import Validator

app = Flask(__name__)
app.secret_key = secrets.token_urlsafe(16)

# Bootstrap-Flask requires this line
bootstrap = Bootstrap(app)

GITHUB_TOKEN = Path(".GITHUB_TOKEN").read_text()

# Github
#GH = Github(GITHUB_TOKEN)
# Flask-WTF requires this line
csrf = CSRFProtect(app)

###
VALIDATOR = Validator()
###


class URLForm(FlaskForm):
    url = StringField('Type a GitHub repository URL', validators=[DataRequired(), URL()])
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
    repo = request.args.get('repo')
    if repo is None:
        resp = make_response("Argument not provided: repo", 400)
        return resp
    else:
        files = searchFiles(repo)
        if 'total_count' in files and files['total_count'] > 0:
            validation=validate(files['items'])
        else:
            validation={}
        return render_template('validate.html', repo=repo, files=files, validation=validation)
        

def searchFiles(repo):
    repo = repo.replace('https://github.com/','')
    url = "https://api.github.com/search/code?q=extension:md+repo:" + repo
    headers = {'Authorization': 'Bearer ' + GITHUB_TOKEN}
    print(url)
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        return r.json()
    else:
        addMessage(3, "Can't connect to the repo: " + r.json()['message'])
        return "{}"

def validate(files):
    report = {}
    for fi in files:
        content = getFileContent(fi['url'])
        report[fi['path']] = [content, validateFileContent(content)]
    return report

def getFileContent(url):
    headers = {'Authorization': 'Bearer ' + GITHUB_TOKEN}
    r = requests.get(url, headers=headers)
    content = ""
    if r.status_code == 200:
        download_url = r.json()['download_url']
        try:
            down = requests.get(download_url, headers=headers)
            if down.status_code == 200:
                return down.text
            else:
                addMessage(3, "Cannot access URL: " + download_url)
                print("Cannot access URL " + download_url + " - status was " + down.status_code)
        except Exception as e:
            # Error
            print(e)
    else:
        addMessage(3, "Cannot access URL: " + url)
        print("Cannot access URL " + url + " - status was " + r.status_code)
    return content

def validateFileContent(content):
    annotations, content = frontmatter.parse(content)
    report = []
    ## Start validation
    if 'component-id' in annotations.keys():
        ### Validate as component
        report = VALIDATOR.asComponent(annotations)
    elif 'container-id' in annotations.keys():
        ### Validate as container
        report = VALIDATOR.asContainer(annotations)
    else:
        report = [NoAnnotationsError()]
    return report

class NoAnnotationsError(Exception):
    def __init__(self):
        # Call the base class constructor with the parameters it needs
        super().__init__("No ecosystem annotations found")
        self.autos = ''

# Severity:
# - Info: 1
# - Warn: 2
# - Alert: 3
# - Error: 4
def addMessage(severity, message):
    if 'messages' not in session:
        session['messages'] = []
    print(session)
    session['messages'].append({'severity': severity, 'message': message})
    return True

def clearMessages():
    session.pop('messages', None)
    return True

