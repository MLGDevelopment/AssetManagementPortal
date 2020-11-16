# -*- coding: utf-8 -*-

import os
import sys
import json
import datetime
import usaddress
from dateutil.relativedelta import relativedelta
from flask import Blueprint, request, jsonify, redirect, url_for
from flask_login import login_user, current_user, logout_user
from flask_restful import Api, Resource
from flask_api import status
from sqlalchemy.exc import IntegrityError

from amp.routes.user import User
from amp.routes.user.models import *

from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from geopy.exc import GeocoderUnavailable
from geopy import distance

packages_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..', '..', '..'))
sys.path.append(os.path.join(packages_path, 'Scraping'))
sys.path.append(os.path.join(packages_path, 'dbConn'))
from axioDB import RentComp, AxioProperty, AxioPropertyOccupancy
from axioScraper import AxioScraper
from Yardi import *

api = Blueprint('api', __name__, url_prefix='/api')
api_wrap = Api(api)

# TODO: UNCOMMENT FOR PROD
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


@api.route("/fetch_market_view/<radius>/<address>/<city>/<state>/<zip>")
def fetch_market_view(radius, address, city, state, zip):
    """
    ENDPOINT FOR ACQUISITIONS MODEL AXIO MARKET DATA REQUEST
    NEEDS PROPERTY ADDRESS & RADIUS
    IF RADIUS NOT SPECIFIED, DEFAULTS TO 3 MILES
    """
    radius = int(radius)
    address = address.replace("%", " ")
    city = city.replace("%", " ")
    state = state.replace("%", " ")
    subject_address = address + ", " + city + ", " + state + " " + zip

    location = get_lat_lon_from_address(subject_address)
    if location:
        s_lat, s_long = location.latitude, location.longitude
    else:
        return  # TODO ERROR

    # fetch all records
    all_axio_properties = AxioProperty.fetch_all_property_data_by_state(state)

    # now compute linear distance between subject and comps
    props_with_distances = []
    for prop in all_axio_properties:
        if prop.latitude and prop.longitude:
            comp_lat, comp_long = float(prop.latitude), float(prop.longitude)
            d = distance.distance((comp_lat, comp_long), (s_lat, s_long))
            prop.distance_to_subject = d.miles
            props_with_distances.append(prop)
    # todo pull occupancy and rent comp data
    props_in_radius = [i for i in props_with_distances if i.distance_to_subject <= radius]

    unit_mixes = RentComp.fetch_unit_mix_for_ids([i.property_id for i in props_in_radius])
    occupancies = AxioPropertyOccupancy.fetch_occupancies_for_ids([i.property_id for i in props_in_radius])

    # preparse json response:
    # return comp id, name, address, long lat, distance from comp, year built, units, SF, asset quality, owner, pm,
    # todo add occupancy and unit mixes

    res_property_list = []
    for prop in props_in_radius:
        axio_property = dict({
            "property_name": prop.property_name
            if prop.property_name is not None else "",
            "property_address": prop.property_address
            if prop.property_address is not None else "",
            "year_built": prop.year_built
            if prop.year_built is not None else "",
            "property_website": prop.property_website
            if prop.property_website is not None else "",
            "property_owner": prop.property_owner
            if prop.property_owner is not None else "",
            "property_management": prop.property_management
            if prop.property_management is not None else "",
            "property_asset_grade_market": prop.property_asset_grade_market
            if prop.property_asset_grade_market is not None else "",
            "property_asset_grade_submarket": prop.property_asset_grade_submarket
            if prop.property_asset_grade_submarket is not None else "",
            "longitude": str(prop.longitude)
            if prop.longitude is not None else "",
            "latitude": str(prop.latitude)
            if prop.latitude is not None else "",
            "distance-to-subject": prop.distance_to_subject
            if prop.distance_to_subject is not None else "",
            "levels": prop.levels
            if prop.levels is not None else "",
            "axio_id": prop.property_id,
            "units": prop.total_units,
            "square_feet": prop.total_square_feet
        })

        unit_mix = [i for i in unit_mixes if i.property_id == prop.property_id]

        axio_property["unit_mix"] = [{"index": i,
                                      "type": r.type,
                                      "quantity": r.quantity,
                                      "area": r.area,
                                      "avg_market_rent": r.avg_market_rent,
                                      "avg_effective_rent": r.avg_effective_rent}
                                     for i, r in enumerate(unit_mix)]
        res_property_list.append(axio_property)

    json_res = json.dumps(res_property_list)
    return json_res





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
        # property not cached, must add it to db
        res = axio.get_property_report(axio_id)
        if res:
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


def yardi_start_end(prior_month, prior_year, curr_month, curr_year):
    start = "{prior_month}/{prior_year}".format(prior_month=prior_month, prior_year=prior_year)
    end = "{curr_month}/{curr_year}".format(curr_month=curr_month, curr_year=curr_year)
    return start, end

@api.route('/yardi')
def yardi():
    """
    Endpoint for all yardi updates:
    - Multifamily Income Statement, Balance sheet, and unit stats
    - Commercial Income Statement, Balance sheet, and unit stats
    """
    properties = Property.query.filter(Property.yardi_id != 'nan')
    yardi_codes_mf = YardiCodesMF.query.filter(YardiCodesMF.classification == "IS")

    today = datetime.date.today()
    twelve_months_prior = today - relativedelta(months=+11)

    curr_year = today.year
    curr_month = today.month
    prior_month = twelve_months_prior.month
    prior_year = twelve_months_prior.year

    start, end = yardi_start_end(prior_month, prior_year, curr_month, curr_year)

    yardi = Yardi(headless=True)
    yardi.valiant_yardi_login()
    header_map = {i.yardi_acct_code: i.db_alias for i in yardi_codes_mf}
    m_df_cols = [i for i in header_map.values()]
    m_df_cols.append("date")
    for property in properties:
        print("Yardi ID: {yc}".format(yc=property.yardi_id))
        res = yardi.T12_Month_Statement(property.yardi_id, 'Accrual', 'ysi_cf', start, end, yardi_codes_mf)
        m_df = pd.DataFrame(columns=m_df_cols)
        res.columns = [header_map.get(item) for item in res.columns]
        res = res.reset_index(drop=False).rename(columns={"index": "date"})
        res['yardi_id'] = property.yardi_id
        m_df = m_df.merge(res, how='outer')
        m_df = m_df.fillna(0)
        ins_records = m_df.to_dict("records")

        for record in ins_records:
            try:
                YardiIS.add_record(YardiIS(**record))
            except IntegrityError:
                db.session.rollback()
                db.session.flush()
    yardi.driver.quit()
    return redirect(url_for('frontend.dashboard'))


@api.route('/yardi_pull')
def yardi_excel_pull():
    properties = Property.query.filter(Property.yardi_id != 'nan')
    mf_yardi_filter = [(i.property_name, i.yardi_id) for i in properties]
    yardi = Yardi(headless=False)
    yardi.valiant_yardi_login()
    today = datetime.date.today()
    twelve_months_prior = today - relativedelta(months=+11)
    curr_year = today.year
    curr_month = today.month - 1
    prior_month = twelve_months_prior.month
    prior_year = twelve_months_prior.year
    start, end = yardi_start_end(prior_month, prior_year, curr_month, curr_year)
    as_of_date = datetime.datetime.today().date()
    yardi.yardi_excel_pull(mf_yardi_filter, start, end, as_of_date)
    return redirect(url_for('frontend.dashboard'))


def get_lat_lon_from_address(address):
    """

    :return:
    """
    geolocator = Nominatim(user_agent="property-locator", timeout=10000)
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds=2)
    try:
        location = geolocator.geocode(address)
    except GeocoderUnavailable:
        pass

    return location


# property_address = Property("property_address")
# year_built = Property("year_built")
# property_website = Property("property_website")
# property_owner = Property("property_owner")
# property_mgmt = Property("property_management")
# property_asset_grade_market = Property("property_asset_grade_market")
# property_asset_grade_submarket = Property("property_asset_grade_submarket")
# property_occupancy = Property("property_occupancy")
#
# propertyDetails(num_properties, 0) = axioID
# propertyDetails(num_properties, 1) = property_name
# propertyDetails(num_properties, 2) = property_address
# propertyDetails(num_properties, 3) = latitude
# propertyDetails(num_properties, 4) = longitude
# propertyDetails(num_properties, 5) = units
# propertyDetails(num_properties, 6) = square_feet
# propertyDetails(num_properties, 7) = year_built
# propertyDetails(num_properties, 8) = property_owner
# propertyDetails(num_properties, 9) = property_mgmt
# propertyDetails(num_properties, 10) = property_asset_grade_submarket
# propertyDetails(num_properties, 11) = levels
# propertyDetails(num_properties, 12) = occupancy
