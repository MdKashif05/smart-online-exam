from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, IntegerField, SelectField, FloatField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from models import User

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already taken. Please choose a different one.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please use a different one.')

class ExamForm(FlaskForm):
    title = StringField('Exam Title', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[DataRequired()])
    duration_minutes = IntegerField('Duration (minutes)', validators=[DataRequired()])
    submit = SubmitField('Save Exam')

class QuestionForm(FlaskForm):
    text = TextAreaField('Question', validators=[DataRequired()])
    question_type = SelectField('Question Type', choices=[
        ('text', 'Text Answer'), 
        ('single_choice', 'Single Choice'), 
        ('multiple_choice', 'Multiple Choice')
    ], validators=[DataRequired()])
    marks = FloatField('Marks', validators=[DataRequired()], default=1.0)
    submit = SubmitField('Add Question')

class OptionForm(FlaskForm):
    text = TextAreaField('Option', validators=[DataRequired()])
    is_correct = BooleanField('Correct Answer')
    submit = SubmitField('Add Option')
