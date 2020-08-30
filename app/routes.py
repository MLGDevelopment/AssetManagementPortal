from flask import render_template, flash, redirect, url_for, request, session
from flask_login import login_user, current_user, logout_user, login_required
from werkzeug.exceptions import HTTPException
from werkzeug.utils import secure_filename
from app import app, bcrypt, logger
from app.models import db, User
from app.forms import RegistrationForm, LoginForm
from datetime import datetime
import datetime
from .scripts import Yardi
import os
import pandas as pd
import xlrd
import json
import sys

packages_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(os.path.join(packages_path, 'Scraping'))
sys.path.append(os.path.join(packages_path, 'dbConn'))
from axioDB import session, RentComp, AxioProperty
from axioScraper import Axio

curr_dir = os.path.dirname(os.path.realpath(__file__))
data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data'))
mlg_data_dir = os.path.join(data_dir, "mlg")
external_data_dir = os.path.join(data_dir, "external")

# GLOBALS + ADDITIONAL PARAMS
pd.set_option('display.max_colwidth', 200)

# from .scripts import db_builder
# db_builder.build()

ALLOWED_EXTENSIONS = ['csv']


@app.before_first_request
def init_app():
    """
    LOAD ALL NECESSARY SESSION VARIABLES HERE
    :return:
    """
    # session['message_content'] = open_message()
    # session['subject_content'] = open_subject()
    # logger.info('LOADED MESSAGE CONTENT')
    # email_manager = EmailManager()
    # email_manager.start_wan_writer()
    # email_manager.start_email_engine()
    # logger.info('EMAIL MANAGER STARTED')


@app.route("/fetch_axio_property/<axio_id>")
def fetch_axio_property(axio_id):
    """
    ROUTE FOR RETURNING AXIO PROPERTY DATA IN JSON
    """

    # check if axio_id is in db and if unit mix is as of today
    today = datetime.date.today()
    unit_mix_res = RentComp.fetch_rent_comp_as_of(axio_id, today)
    prop_details_res = -1  # init prop details res

    if unit_mix_res:
        # unit mix exists per the as of date, pull property details
        prop_details_res = AxioProperty.fetch_property(axio_id)
    else:
        # property not cached, must pull it into db
        axio = Axio(headless=True)
        axio.mlg_axio_login()
        axio.navigate_to_property_report(axio_id)
        prop_details_res = axio.get_property_details(axio_id, return_res=True)
        unit_mix_res = axio.get_property_data(axio_id, return_res=True)

    axio_property = dict({
        "property_name": prop_details_res.property_name,
        "property_address": prop_details_res.property_address,
        "year_built": prop_details_res.year_built,
        "property_website": prop_details_res.property_website,
        "property_owner": prop_details_res.property_owner,
        "property_management": prop_details_res.property_management,
        "property_asset_grade_market": prop_details_res.property_asset_grade_market,
        "property_asset_grade_submarket": prop_details_res.property_asset_grade_submarket,
    })

    axio_property["unit_mix"] = [{"index": i,
                                  "type": r.type,
                                  "quantity": r.quantity,
                                  "area": r.area,
                                  "avg_market_rent": r.avg_market_rent,
                                  "avg_effective_rent": r.avg_effective_rent}
                                 for i, r in enumerate(unit_mix_res)]

    json_res = json.dumps(axio_property)
    return json_res


@app.route("/property-overview")
def property_overview():
    return render_template("property_overview.html")


@app.route("/properties")
def properties_view():
    return render_template("properties.html")


@app.route('/')
@app.route('/dashboard')
def dashboard():
    """
    ROUTE FOR DASHBOARD
    :return:
    """
    def format(x):
        return "${:.1f}K".format(x/1000)

    def format_billion(x):
        return f'${int(x):n}'

    _path = os.path.join(mlg_data_dir, 'asset_perf_summary.xlsx')
    xlsx = pd.ExcelFile(_path)
    df1_mf = pd.read_excel(xlsx, 'multifamily')
    df2_comm = pd.read_excel(xlsx, 'commercial')

    df1_mf["Occ Date"] = df1_mf["Occ Date"].map(lambda x: datetime(*xlrd.xldate_as_tuple(x, 0)).date())
    df1_mf['Orig Sale Proforma Amt'] = df1_mf['Orig Sale Proforma Amt'].apply(format)

    curr_val_mf = format_billion(df1_mf[' Value Estimate'].sum())
    curr_val_comm = format_billion(df2_comm[' Value Estimate'].sum())

    headers = df1_mf.columns.tolist()
    df_mf = df1_mf.values.tolist()

    return render_template("am_dashboard.html",
                           df_mf=df_mf,
                           headers=headers,
                           curr_val_mf=curr_val_mf,
                           curr_val_comm=curr_val_comm)


@app.route("/account")
@login_required
def account():
    """
    ROUTE FOR VIEW ACCOUNT

    :return:
    """

    is_logged_in = current_user.is_authenticated()

    if is_logged_in:
        print

    return render_template('layout.html', title='Account')


@app.route("/about")
def about():
    """
    ROUTE FOR THE ABOUT PAGE

    :return:
    """
    # TODO: move out of here
    return render_template("about.html")


@app.route('/property_list')
def property_list():
    return render_template('propert_list.html')


@app.route("/register", methods=['GET','POST'])
def register():
    if current_user.is_authenticated:
        return redirect('/')
    form = RegistrationForm(request.form)
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode("utf-8")
        user = User(first_name=form.first_name.data, last_name=form.last_name.data, company_name=form.company_name.data,
                    company_email=form.company_email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        session.clear()
        login_user(user, remember=form.remember.data)
        flash("Account created!", 'success')
        # next_page = request.args.get('next')
        # redirect(next_page) if next_page else
        return redirect(url_for('dashboard'))
    return render_template("register.html", title="Register", form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    """
    ROUTE FOR LOGGING IN

    :return:
    """

    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(company_email=form.company_email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            # session['number'] = consequent_integers.next()
            login_user(user, remember=form.remember.data)

            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('Login Unsuccessful.', 'danger')

    return render_template("login.html", title="Login", form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect('/')


@app.route("/password")
def password():
    return render_template('password.html')


@app.route('/yardi', methods=['GET', 'POST'])
def yardi():

    form = YardiForm()
    df = pd.DataFrame()
    if form.validate_on_submit():
        property_code = form.property_code.data
        book_code = form.book_code.data
        account_tree = form.account_tree.data
        period_start = form.period_start.data
        period_end = form.period_end.data
        if valiant_yardi_login():
            df = T12_Month_Statement(property_code, book_code, account_tree, period_start, period_end)
            return render_template("yardi.html", form=form, prop_data=df)
    return render_template('yardi.html', form=form, prop_data=df)


@app.route("/analytics")
def analytics():
    return render_template('mlganalytics.html')


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/uploader', methods=['GET', 'POST'])
@login_required
def upload_file():
    if request.method == 'POST':
        try:
            file = request.files['file']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                if not os.path.isdir(app.config["UPLOAD_FOLDER"]):
                    os.makedirs(app.config["UPLOAD_FOLDER"])
                file.save(file_path)
                flash('File Uploaded Successfully', 'success')
                data = read_uploaded_file(file_path)
        except HTTPException:
            flash('Failed Upload. Are you sure you selected the correct file?', 'warning')
            redirect('company_portal')
    return redirect('company_portal')


@app.route("/build_db")
def build_db():
    from app.scripts import db_builder
    if(db_builder.build()):
        flash("record exists", "error")
    else:
        flash("record exists", "success")

    return render_template("am_dashboard.html")


# @app.route('/company_portal', methods=['POST', 'GET'])
# @login_required
# def company_portal():
#
#     post_form = PostForm()
#     form = RedditAccountConfiguration()
#
#     if post_form.validate_on_submit():
#         # UPDATE GLOBALS
#         session['message_content'] = post_form.body.data
#         session['subject_content'] = post_form.subject.data
#
#     if form.validate_on_submit():
#         reddit.refresh_token(form.client_id.data, form.client_secret.data,
#                              form.reddit_password.data, 'test_script', form.reddit_account_username.data)
#
#         reddit.build_connection()
#
#     associations = Company.query.join(primary_key_subscribers).filter(
#         primary_key_subscribers.c.company == current_user.company_name).first()
#
#     if associations:
#         primary_keywords = associations.primary_keywords
#         secondary_keywords = associations.secondary_keywords
#         return render_template('company_portal.html',
#                                primary_keywords=primary_keywords,
#                                secondary_keywords=secondary_keywords,
#                                form=form,
#                                reddit=reddit,
#                                post_form=post_form,
#                                message_content=session['message_content'],
#                                subject_content=session['subject_content'])
#
#     return render_template("company_portal.html",
#                            form=form,
#                            reddit=reddit,
#                            post_form=post_form,
#                            message_content=session['message_content'],
#                            subject_content=session['subject_content'])


@app.route('/acquisitions_model')
def acquisitions_model():
    """
    ROUTE FOR MODELING A DEAL
    :return:
    """
    df = pd.read_excel('app/model_fields.xlsx')
    fields = df.values.tolist()
    for field in fields:
        var = field[0]
        name = var.replace(" ", "_")
        setattr(AcquisitionForm, name, FloatField(var, validators=[DataRequired()]))

    acq_form = AcquisitionForm()
    return render_template('acquisitions_model.html', form=acq_form)
