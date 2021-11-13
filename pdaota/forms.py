from pdaota import app, mongo
from pdaota.lib import *
from flask_wtf import FlaskForm
from wtforms import (BooleanField, StringField, PasswordField, SelectField, SelectMultipleField, widgets, validators)

class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()

class RegistrationForm(FlaskForm):
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email Address', [validators.Length(min=6, max=35)])
    password = PasswordField('New Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Repeat Password')
    accept_tos = BooleanField('I accept the TOS', [validators.DataRequired()])

class NewProjectForm(FlaskForm):
    possible_collabs = MultiCheckboxField(label = 'Choose Collaborators', 
                                choices = [])

    project_name = StringField('Project Name', [validators.Length(min=4, max=25)])
    total_rounds = SelectField(label = 'Number of Rounds', 
                            choices = TOTAL_ROUND_CHOICES)

    