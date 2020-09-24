# -*- coding: utf-8 -*-

import os
import sys
import json

from flask import Blueprint, request, jsonify
from flask_login import login_user, current_user, logout_user
from flask_restful import Api, Resource
from flask_api import status

from amp.routes.user import User
from amp.routes.user.models import *

import datetime

packages_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..', '..', '..'))
sys.path.append(os.path.join(packages_path, 'Scraping'))
sys.path.append(os.path.join(packages_path, 'dbConn'))
from axioDB import RentComp, AxioProperty, AxioPropertyOccupancy
from axioScraper import AxioScraper
from yardi import *

api = Blueprint('api', __name__, url_prefix='/api')
api_wrap = Api(api)

axio = AxioScraper(headless=True)
axio.mlg_axio_login()


class TodoItem(Resource):
    def get(self, id):
        return {'task': 'Say "Hello, World!"'}


api_wrap.add_resource(TodoItem, '/todos/<int:id>')


@api.route('/login', methods=['POST'])
def login():
    if current_user.is_authenticated():
        return jsonify(flag='success')

    username = request.form.get('username')
    password = request.form.get('password')
    if username and password:
        user, authenticated = User.authenticate(username, password)
        if user and authenticated:
            if login_user(user, remember='y'):
                return jsonify(flag='success')

    return jsonify(flag='fail', msg='Sorry, try again.')


@api.route('/logout')
def logout():
    if current_user.is_authenticated():
        logout_user()
    return jsonify(flag='success', msg='Logouted.')


@api.route("/fetch_axio_property/<axio_id>")
def fetch_axio_property(axio_id):
    """
    ROUTE FOR RETURNING AXIO PROPERTY DATA IN JSON FORM
    """

    # check if axio_id is in db and if unit mix is as of today
    today = datetime.date.today()
    # today = datetime.date(2020, 9, 1)
    axio.unit_mix = RentComp.fetch_rent_comp_as_of(axio_id, today)
    axio.property_occupancy = AxioPropertyOccupancy.get_occupancy_as_of_date(axio_id, today)
    if axio.unit_mix is not None and axio.property_occupancy is not None:
        # unit mix exists per the as of date, pull property details
        axio.property_details = AxioProperty.fetch_property(axio_id)
        axio.property_occupancy = AxioPropertyOccupancy.get_occupancy_as_of_date(axio_id, today)
    else:
        # property not cached, must pull it into db
        res = axio.navigate_to_property_report(axio_id)
        if res != 0:
            axio.get_property_details(axio_id)
            axio.get_property_data(axio_id)
        else:
            # Dummy response for invalid ID
            axio_property = dict({
                "property_name": "DNE",
                "property_address": "DNE",
                "year_built": "DNE",
                "property_website": "DNE",
                "property_owner": "DNE",
                "property_management": "DNE",
                "property_asset_grade_market": "DNE",
                "property_asset_grade_submarket": "DNE",
                "property_occupancy": 0.0,
            })

            axio_property["unit_mix"] = [{"index": i,
                                          "type": "DNE",
                                          "quantity": i,
                                          "area": i,
                                          "avg_market_rent": i,
                                          "avg_effective_rent": i}
                                         for i in range(1, 30)]

            json_res = json.dumps(axio_property)
            return json_res, status.HTTP_400_BAD_REQUEST

    axio_property = dict({
        "property_name": axio.property_details.property_name
        if axio.property_details.property_name is not None else "",
        "property_address": axio.property_details.property_address
        if axio.property_details.property_address is not None else "",
        "year_built": axio.property_details.year_built
        if axio.property_details.year_built is not None else "",
        "property_website": axio.property_details.property_website
        if axio.property_details.property_website is not None else "",
        "property_owner": axio.property_details.property_owner
        if axio.property_details.property_owner is not None else "",
        "property_management": axio.property_details.property_management
        if axio.property_details.property_management is not None else "",
        "property_asset_grade_market": axio.property_details.property_asset_grade_market
        if axio.property_details.property_asset_grade_market is not None else "",
        "property_asset_grade_submarket": axio.property_details.property_asset_grade_submarket
        if axio.property_details.property_asset_grade_submarket is not None else "",
        "property_occupancy": float(axio.property_occupancy.occupancy)
        if axio.property_occupancy.occupancy is not None else -1
    })

    axio_property["unit_mix"] = [{"index": i,
                                  "type": r.type,
                                  "quantity": r.quantity,
                                  "area": r.area,
                                  "avg_market_rent": r.avg_market_rent,
                                  "avg_effective_rent": r.avg_effective_rent}
                                 for i, r in enumerate(axio.unit_mix)]

    json_res = json.dumps(axio_property)
    return json_res


@api.route('/yardi')
def yardi():
    properties = Property.query.filter(Property.yardi_id != 'nan')
    start = '1/1/2019'
    end = '8/24/2020'
    yardi = Yardi(headless=False)
    yardi.pull_multifamily_stats(properties, start, end)

