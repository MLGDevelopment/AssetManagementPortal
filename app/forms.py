from flask_wtf import FlaskForm, Form
from wtforms import TextAreaField, SelectField
from wtforms import StringField, PasswordField, SubmitField, BooleanField, IntegerField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from app.models import Sponsor
from flask_login import current_user
from app.models import User
import phonenumbers


class RegistrationForm(FlaskForm):
    """
    A class to create a web-form for registering for the site.
    """

    choices = [(i.id, i.sponsor_name) for i in Sponsor.query.all()]

    first_name = StringField('First Name', validators=[DataRequired(), Length(min=2, max=20)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(min=2, max=20)])
    company_name = SelectField('Company Name', choices=choices, validators=[DataRequired()], coerce=int)
    company_email = StringField('Company Email', validators=[DataRequired(), Email()])
    # company_phone = StringField('Company Phone', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Register')

    def validate_company_email(self, company_email):
        email = User.query.filter_by(company_email=company_email.data).first()
        if email:
            raise ValidationError("email already registered")

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError("username taken")


    def validate_phone(self, field):
        if len(field.data) > 16:
            raise ValidationError('Invalid phone number.')
        try:
            input_number = phonenumbers.parse(field.data)
            if not (phonenumbers.is_valid_number(input_number)):
                raise ValidationError('Invalid phone number.')
        except:
            input_number = phonenumbers.parse("+1" + field.data)
            if not (phonenumbers.is_valid_number(input_number)):
                raise ValidationError('Invalid phone number.')


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')


class UpdateAccountForm(FlaskForm):
    """
    A class to create a web-form for registering for the site.
    """
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])

    submit = SubmitField('Update')

    def validate_username(self, username):
        if username.data != current_user.username:
            user = Users.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError("username taken")

    def validate_email(self, email):
        if email.data != current_user.email:
            email = Users.query.filter_by(username=email.data).first()
            if email:
                raise ValidationError("email already registered")

