# -*- coding: utf-8 -*-

import os
import json
import ast
from amp.config import BaseConfig

from flask import Blueprint, render_template, send_from_directory, request, \
    current_app, flash, redirect, url_for
from flask_login import login_user, current_user, logout_user
from flask_restful import Api, Resource
from flask_api import status
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import HTTPException
from werkzeug.utils import secure_filename
from .forms import SelectAssetManagementReport

from amp.routes.user.models import *

import pandas as pd
import datetime

portal = Blueprint('portal', __name__, url_prefix='/portal')


@portal.route('/quarterly-report-portal/', methods=['POST', 'GET'])
@portal.route('/quarterly-report-portal/<errors>', methods=['POST', 'GET'])
def quarterly_report_portal(errors=None):
    # todo: pull in qr data to date
    reports = SelectAssetManagementReport()
    if errors is not None:
        errors = ast.literal_eval(errors)
        return render_template('portals/quarterly_reports.html', form=reports, errors=errors)

    return render_template('portals/quarterly_reports.html', form=reports, errors=errors)


@portal.route('/uploader', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        try:
            file = request.files['file']
            if file:
                filename = secure_filename(file.filename)
                selected_report = request.form['myField']
                file_path = os.path.join(BaseConfig.UPLOAD_FOLDER, filename)
                res = check_report_file(selected_report, filename, file_path, file)
                if isinstance(res, dict):
                    if 'invalid_properties' in res.keys():
                        return redirect(url_for('portal.quarterly_report_portal', errors=res))
                if isinstance(res, pd.DataFrame):
                    recs = res.to_dict('records')
                    db_records = [QuarterlyReportMetrics(**rec) for rec in recs]
                    [QuarterlyReportMetrics.add_record(i) for i in db_records]
                    db.session.commit()
                flash('file uploaded successfully', 'success')
        except HTTPException:
            flash('Failed Upload. Are you sure you selected the correct file?', 'warning')
            redirect('portal.quarterly_report_portal')
    return redirect('portal.quarterly_report_portal')


def check_report_file(report_id, file_name, file_path, file):
    # todo: check on filename, headers, property names, etc
    if report_id == '1':
        quarter, report = file_name.split('-')
        quarter = quarter.replace("_", "")
        report = report.replace("_", " ").split(".")[0].strip()
        # first check quarter
        today = datetime.date.today()
        ldq = get_last_day_of_the_quarter(today)

        if report == 'distribution and valuations summary':
            file.save(file_path)
            df = pd.read_excel(file_path)
            # first check columns
            properties = Property.get_report_level_properties()
            property_names_list = [i.property_name for i in properties]
            invalid_properties = [i for i in df['property_name'].values.tolist() if i not in property_names_list]
            if invalid_properties:
                return {'invalid_properties': invalid_properties}
            property_name_pid_map = {i.property_name: i.pid for i in properties}
            df["pid"] = df['property_name'].map(property_name_pid_map)
            del df['property_name']
            return df



def get_quarter(date):
    return (date.month - 1) / 3 + 1


def get_prior_quarter(date):
    return (date.month - 1) / 3


def get_first_day_of_the_quarter(date):
    quarter = get_quarter(date)
    return datetime.datetime(date.year, 3 * quarter - 2, 1)


def get_last_day_of_the_quarter(date):
    quarter = get_prior_quarter(date)
    month = 3 * quarter
    remaining = month / 12
    return datetime.datetime(date.year + int(remaining), int(month) % 12 + 1, 1) + datetime.timedelta(days=-1)