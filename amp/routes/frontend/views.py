# -*- coding: utf-8 -*-

from uuid import uuid4
import os
import sys
import csv
from flask import send_file

from io import StringIO, BytesIO


from flask import Blueprint, render_template, request, flash, \
    url_for, redirect, session, abort, Response
from flask_login import login_required, login_user, current_user, logout_user, \
    confirm_login, login_fresh

from amp.routes.user import *
from amp.extensions import db, login_manager
from .forms import SignupForm, LoginForm, RecoverPasswordForm, ReauthForm, \
    ChangePasswordForm

from collections import Counter

from amp.config import DefaultConfig

packages_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..', '..', '..'))
sys.path.append(os.path.join(packages_path, 'Scraping'))
sys.path.append(os.path.join(packages_path, 'dbConn'))
from axioDB import session, AxioProperty, RentComp, AxioPropertyOccupancy

frontend = Blueprint('frontend', __name__)


def build_csv_response(data=[]):
    if not data:
        return 0
    proxy = StringIO()
    writer = csv.writer(proxy)
    writer.writerow([i for i in list(data[0].keys())])
    for row in data:
        writer.writerow([row.get(i) for i in list(data[0].keys())])

    # Creating the byteIO object from the StringIO Object
    mem = BytesIO()
    mem.write(proxy.getvalue().encode('utf-8'))
    # seeking was necessary. Python 3.5.2, Flask 0.12.2
    mem.seek(0)
    proxy.close()
    return mem


@frontend.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('user.profile'))
    return render_template('index.html')


@frontend.route("/axioscraper", methods=['POST', 'GET'])
def axio_scraper():

    if request.method == 'POST':
        name = ''
        if 'download_property_data' in request.form:
            res = AxioProperty.fetch_all_property_data()
            res = ORM.rows2dict(res)
            sorted(res, key=lambda k: k['property_id'])
            mem = build_csv_response(res)
            name = 'axio_properties.csv'
        elif 'download_rent_data' in request.form:
            res = RentComp.fetch_all_rent_data()
            res = ORM.rows2dict(res)
            mem = build_csv_response(res)
            name = 'axio_rent_data.csv'
        elif 'download_occupancy_data' in request.form:
            res = AxioPropertyOccupancy.fetch_all_occ_data()
            res = ORM.rows2dict(res)
            mem = build_csv_response(res)
            name = 'axio_occupancy_data.csv'

        return send_file(mem,
                         mimetype='text/csv',
                         attachment_filename=name,
                         as_attachment=True, cache_timeout=0)

    c_properties = session.query(AxioProperty).count()
    all_p_data = AxioProperty.fetch_all_property_data()
    all_p_data = [i.__dict__ for i in all_p_data]
    msa_c = Counter([i["msa"] for i in all_p_data]).most_common()
    msa_headers = ["MSA", "Count"]
    return render_template("dashboards/axio_overview.html", p_count=c_properties, msa_overview=msa_c, msa_headers=msa_headers)


@frontend.route("/yardi_scraper")
def yardi_scraper():

    data = {"last_update": "9/19/2020",
            "yardi_headers": [i for i in range(1, 10)],
            "yardi_data": [[i for i in range(1, 10)] for j in range(1, 5)]}

    return render_template("dashboards/yardi_scraper.html", _data=data)


# @frontend.route('/uploads/<filename>')
# def download_file(filename):
#     return send_from_directory(DefaultConfig.PROPERTY_PHOTOS_DIR, filename, as_attachment=True)


@frontend.route("/properties")
def properties_view():
    res = Property.query.filter((Property.report_level == 1) & (Property.status == 'ACTIVE')).all()
    if res:
        img_path = "C:\\Users\\nburmeister\\Documents\\_Development\\QR_Automation\\img"
        img_dirs = {i: i + "/main_banner.jpg" for i in os.listdir(img_path)}
        for prop in res:
            prop.img_path = img_dirs.get(prop.name)

    return render_template("dashboards/properties.html", properties=res)


@frontend.route("/property-overview")
def property_overview():
    return render_template("dashboards/property_overview.html")


@frontend.route("/")
def home():
    return render_template("dashboards/base.html")


@frontend.route('/')
@frontend.route('/dashboard')
def dashboard():
    return render_template("dashboards/am_dashboard.html")


@frontend.route("/build_db")
def build_db():
    from amp.scripts import db_builder
    db_builder.build()
    return redirect(url_for('frontend.dashboard'))


@frontend.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('user.profile'))

    form = LoginForm(login=request.args.get('login', None),
                     next=request.args.get('next', None))

    if form.validate_on_submit():
        user, authenticated = User.authenticate(form.login.data,
                                    form.password.data)

        if user and authenticated:
            remember = request.form.get('remember') == 'y'
            if login_user(user, remember=remember):
                flash("Logged in", 'success')
            return redirect(form.next.data or url_for('user.profile'))
        else:
            flash('Sorry, invalid login', 'danger')

    return render_template('frontend/login.html', form=form)


@frontend.route('/reauth', methods=['GET', 'POST'])
@login_required
def reauth():
    form = ReauthForm(next=request.args.get('next'))

    if request.method == 'POST':
        user, authenticated = User.authenticate(current_user.name,
                                    form.password.data)
        if user and authenticated:
            confirm_login()
            flash('Reauthenticated.', 'success')
            return redirect('/change_password')

        flash('Password is wrong.', 'danger')
    return render_template('frontend/reauth.html', form=form)


@frontend.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out', 'success')
    return redirect(url_for('frontend.index'))


@frontend.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('user.profile'))

    form = SignupForm(next=request.args.get('next'))

    if form.validate_on_submit():
        user = User()
        form.populate_obj(user)

        db.session.add(user)
        db.session.commit()

        if login_user(user):
            flash('Signed up', 'success')
            return redirect(form.next.data or url_for('user.profile'))

    return render_template('frontend/signup.html', form=form)


@frontend.route('/change_password', methods=['GET', 'POST'])
def change_password():
    user = None
    if current_user.is_authenticated:
        if not login_fresh():
            return login_manager.needs_refresh()
        user = current_user
    elif 'activation_key' in request.values and 'email' in request.values:
        activation_key = request.values['activation_key']
        email = request.values['email']
        user = User.query.filter_by(activation_key=activation_key) \
                         .filter_by(email=email).first()

    if user is None:
        abort(403)

    form = ChangePasswordForm(activation_key=user.activation_key)

    if form.validate_on_submit():
        user.password = form.password.data
        user.activation_key = None
        db.session.add(user)
        db.session.commit()

        flash("Your password has been changed, please log in again", "success")
        return redirect(url_for("frontend.login"))

    return render_template("frontend/change_password.html", form=form)


@frontend.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    form = RecoverPasswordForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if user:
            flash('Please see your email for instructions on '
                  'how to access your account', 'success')

            user.activation_key = str(uuid4())
            db.session.add(user)
            db.session.commit()

            return render_template('frontend/reset_password.html', form=form)
        else:
            flash('Sorry, no user found for that email address', 'error')

    return render_template('frontend/reset_password.html', form=form)