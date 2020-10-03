# -*- coding: utf-8 -*-

import os
from flask import Blueprint, render_template, send_from_directory, request, \
    current_app, flash, redirect
from flask_login import login_user, current_user, logout_user
from flask_restful import Api, Resource
from flask_api import status
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import HTTPException
from werkzeug.utils import secure_filename

from .forms import SelectAssetManagementReport

portal = Blueprint('portal', __name__, url_prefix='/portal')


@portal.route('/quarterly-report-portal', methods=['POST', 'GET'])
def quarterly_report_portal():
    reports = SelectAssetManagementReport()
    return render_template('portals/quarterly_reports.html', form=reports)


@portal.route('/uploader', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        try:
            file = request.files['file']
            if file:
                filename = secure_filename(file.filename)
                file_path = os.path.join(portal.config["UPLOAD_FOLDER"], filename)
                if not os.path.isdir(portal.config["UPLOAD_FOLDER"]):
                    os.makedirs(portal.config["UPLOAD_FOLDER"])
                file.save(file_path)
                # data = read_uploaded_file(file_path)
                flash('File Uploaded Successfully', 'success')
        except HTTPException:
            flash('Failed Upload. Are you sure you selected the correct file?', 'warning')
            redirect('portal.quarterly_report_portal')
    return redirect('portal.quarterly_report_portal')