from flask_wtf import Form
from wtforms import ValidationError, HiddenField, BooleanField, StringField, \
                PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length, EqualTo, Email
from flask_wtf.html5 import EmailField

from amp.routes.user import User
from amp.constants import USERNAME_LEN_MIN, USERNAME_LEN_MAX, USERNAME_TIP, \
                    PASSWORD_LEN_MIN, PASSWORD_LEN_MAX, PASSWORD_TIP, \
                    EMAIL_LEN_MIN, EMAIL_LEN_MAX, EMAIL_TIP, \
                    AGREE_TIP


class SelectAssetManagementReport(Form):
    reports = [(None, ''),
               (1, 'QR - Property & Portfolio Distributions'),
               (2, 'QR - Property & Portfolio Valuations'),
               ]
    myField = SelectField(u'Field name', choices=reports, validators=[DataRequired()], default=None)