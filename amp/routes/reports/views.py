
from flask import Blueprint, render_template, request, flash, \
    url_for, redirect, session, abort, Response
from flask_login import login_required, login_user, current_user, logout_user, \
    confirm_login, login_fresh

from amp.routes.user.models import *
from amp.extensions import db, login_manager

reports = Blueprint('reports', __name__, url_prefix='/reports')


@reports.route("/properties_report_list")
def properties_report_list():
    headers = ["Report Level Property List"]
    res = [i.property_name for i in Property.get_report_level_properties()]
    res.sort()
    return render_template('reports/reports.html', data=res, header_names=headers)