from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5

from flask_wtf import FlaskForm, CSRFProtect
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length, URL

import secrets

app = Flask(__name__)
app.secret_key = secrets.token_urlsafe(16)

# Bootstrap-Flask requires this line
bootstrap = Bootstrap5(app)

# Flask-WTF requires this line
csrf = CSRFProtect(app)

class URLForm(FlaskForm):
    url = StringField('Type a GitHub repository URL', validators=[DataRequired(), URL()])
    submit = SubmitField('Submit')

@app.route('/', methods=['GET', 'POST'])
def index():
    form = URLForm()
    message = ""
    if form.validate_on_submit():
        url = form.url.data
        return redirect( url_for('validate', repo=url) )
    else:
        message = "Please enter a valid URL"
    return render_template('index.html', form=form, message=message)

@app.route('/validate',methods = ['GET'])
def validate():
    repo = request.args.get('repo')
    if repo is None:
        resp = make_response("Argument not provided: repo", 400)
        return resp
    else:
        return render_template('validate.html', repo=repo)
    


