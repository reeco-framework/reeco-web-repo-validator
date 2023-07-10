from flask import Flask, render_template, redirect, url_for, request
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
    return r.json()

def validate(files):
    report = {}
    for fi in files:
        report[fi['path']] = validateFile(fi['url'])
    return report

def validateFile(url):
    headers = {'Authorization': 'Bearer ' + GITHUB_TOKEN}
    r = requests.get(url, headers=headers)
    report = []
    if r.status_code == 200:
        download_url = r.json()['download_url']
        try:
            down = requests.get(download_url, headers=headers)
            if down.status_code == 200:
                annotations, content = frontmatter.parse(down.text)
                ## Start validation
                if 'component-id' in annotations.keys():
                    ### Validate as component
                    report = VALIDATOR.asComponent(annotations)
                elif 'container-id' in annotations.keys():
                    ### Validate as container
                    report = VALIDATOR.asContainer(annotations)
            else:
                report = report + ['Error downloading ' + download_url + ' (' + down.status_code + ')']
        except Exception as e:
            # Malformed YAML in Markdown
            report = report + [e]
    return report
