from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Optional, InputRequired

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class UserPanel(FlaskForm):
    change_username = BooleanField('Change Username', default=False)
    change_password = BooleanField('Change Password', default=False)

    new_username = StringField('Username', render_kw={'disabled':''}, validators=[Optional()])
    new_password = PasswordField('New Password', render_kw={'disabled':''}, validators=[Optional()])
    confirm_password = PasswordField('Retype Password', render_kw={'disabled': ''}, validators=[Optional()])
    current_password = PasswordField('Current Password', validators=[InputRequired()])

    submit = SubmitField('Save Changes')