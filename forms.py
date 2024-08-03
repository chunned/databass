from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired


class NewReleaseForm(FlaskForm):
    release = StringField('release', validators=[DataRequired()])
    artist = StringField('artist', validators=[DataRequired()])