import pandas as pd
import os
from app.models import db, Sponsor
from sqlalchemy.exc import IntegrityError
from app import logger
from flask import flash

curr_dir = os.path.dirname(os.path.realpath(__file__))
data_dir = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..', 'data', "external"))
mlg_data_dir = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..', 'data', "mlg"))


class DataBaseBuilder:

    def __init__(self):
        # CBSA = os.path.join(data_dir, "CBSA.xlsx")
        # COUNTIES = os.path.join(data_dir, "Counties.xlsx")
        # DIVISION = os.path.join(data_dir, "Division.xlsx")
        # REGIONS = os.path.join(data_dir, "Regions.xlsx")
        # STATES = os.path.join(data_dir, "States.xlsx")
        # ZCTA_CBSA = os.path.join(data_dir, "ZCTA_CBSA.xlsx")
        # ZCTA_COUNTY = os.path.join(data_dir, "ZCTA_County.xlsx")
        # ZIP_CODES = os.path.join(data_dir, "ZIP Codes.xlsx")
        SPONSORS = os.path.join(mlg_data_dir, "sponsors.xlsx")

        # self.CBSA_DF = pd.read_excel(CBSA)
        # self.COUNTIES_DF = pd.read_excel(COUNTIES)
        # self.DIVISION_DF = pd.read_excel(DIVISION)
        # self.REGIONS_DF = pd.read_excel(REGIONS)
        # self.STATES_DF = pd.read_excel(STATES)
        # self.ZCTA_CBSA_DF = pd.read_excel(ZCTA_CBSA)
        # self.ZCTA_COUNTY_DF = pd.read_excel(ZCTA_COUNTY)
        # self.ZIP_CODES_DF = pd.read_excel(ZIP_CODES)
        self.SPONSORS_DF = pd.read_excel(SPONSORS)

    def build_sponsor_table(self):
        records = self.SPONSORS_DF.to_dict("records")
        try:
            [Sponsor.add_record(Sponsor(**records[i])) for i in range(len(records))]
            db.session.commit()
            flash("record inserted", "success")
            return 0
        except IntegrityError:
            db.session.rollback()
            db.session.flush()
            return 1

    def build(self):
        if (self.build_sponsor_table()):
            return 1

        return 0


def build_sponsors():
    db_build = DataBaseBuilder()
    db_build.build()


def build():
    build_sponsors()


if __name__ == "__main__":
    build()