from flask_wtf import FlaskForm
from wtforms import FileField, SubmitField
from wtforms.validators import DataRequired

class UploadCSVForm(FlaskForm):
    file = FileField('Upload CSV File', validators=[DataRequired()])
    submit = SubmitField('Upload')
