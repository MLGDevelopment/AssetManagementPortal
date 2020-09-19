import os
import datetime
import pandas as pd
from sqlalchemy.exc import IntegrityError


# todo: move paths to config
curr_dir = os.path.dirname(os.path.realpath(__file__))
data_dir = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..', '..', 'data', 'external'))
mlg_data_dir = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..', 'data', 'mlg'))
db_data_dir = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..', 'data', 'db'))


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
        # self.CBSA_DF = pd.read_excel(CBSA)
        # self.COUNTIES_DF = pd.read_excel(COUNTIES)
        # self.DIVISION_DF = pd.read_excel(DIVISION)
        # self.REGIONS_DF = pd.read_excel(REGIONS)
        # self.STATES_DF = pd.read_excel(STATES)
        # self.ZCTA_CBSA_DF = pd.read_excel(ZCTA_CBSA)
        # self.ZCTA_COUNTY_DF = pd.read_excel(ZCTA_COUNTY)
        # self.ZIP_CODES_DF = pd.read_excel(ZIP_CODES)
        pass

    def build_sponsor(self):
        sponsors_path = os.path.join(db_data_dir, "sponsors.xlsx")
        self.sponsors_df = pd.read_excel(sponsors_path)
        records = self.sponsors_df.to_dict("records")
        try:
            [Sponsor.add_record(Sponsor(**records[i])) for i in range(len(records))]
            return 0
        except IntegrityError:
            db.session.rollback()
            db.session.flush()
            return 1

    def build_portfolios(self):
        portfolios_path = os.path.join(db_data_dir, "portfolios.xlsx")
        self.portfolios_df = pd.read_excel(portfolios_path)
        records = self.portfolios_df.to_dict("records")
        try:
            [Portfolio.add_record(Portfolio(**records[i])) for i in range(len(records))]
            return 0

        except IntegrityError:
            db.session.rollback()
            db.session.flush()
            return 1

    def build_asset_classes(self):
        asset_classes_path = os.path.join(db_data_dir, "asset_classes.xlsx")
        self.asset_classes_df = pd.read_excel(asset_classes_path)
        records = self.asset_classes_df.to_dict("records")
        try:
            [AssetClass.add_record(AssetClass(**records[i])) for i in range(len(records))]
            return 0
        except IntegrityError:
            db.session.rollback()
            db.session.flush()
            return 1

    def build_asset_categories(self):
        asset_categories_path = os.path.join(db_data_dir, "asset_categories.xlsx")
        self.asset_categories_df = pd.read_excel(asset_categories_path)
        records = self.asset_categories_df.to_dict("records")
        try:
            [AssetCategories.add_record(AssetCategories(**records[i])) for i in range(len(records))]
            return 0
        except IntegrityError:
            db.session.rollback()
            db.session.flush()
            return 1

    def build_states(self):
        states_path = os.path.join(db_data_dir, "states.xlsx")
        self.states_df = pd.read_excel(states_path)
        records = self.states_df.to_dict("records")
        try:
            [State.add_record(State(**records[i])) for i in range(len(records))]
            return 0
        except IntegrityError:
            db.session.rollback()
            db.session.flush()
            return 1

    def build_properties(self):
        """
        Note: using pandas to insert property data
        """
        properties_path = os.path.join(db_data_dir, "properties.xlsx")
        self.properties_df = pd.read_excel(properties_path, dtype={'state': str,
                                                                   'zip': str, })
        self.properties_df = self.properties_df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
        self.properties_df.to_sql('property', con=db.engine, if_exists='append', index=False)
        db.session.commit()

    def build_qr_table(self):
        qr_metrics_path = os.path.join(db_data_dir, "propertyreportmetrics.xlsx")
        self.qr_metrics_df = pd.read_excel(qr_metrics_path)

        records = self.qr_metrics_df.to_dict("records")
        for record in records:
            # query db for property
            res = Property.get_property_by_name(record["property"])
            if res.report_level == 1:
                record["date"] = datetime.date(2020, 6, 30)
                record["property_id"] = res.pid
                record.pop('property')
                QuarterlyReportMetrics.add_record(QuarterlyReportMetrics(**record))

    def build(self):
        if self.build_sponsor():
            print("Error")
        if self.build_portfolios():
            print("Error")
        if self.build_asset_categories():
            print("Error")
        if self.build_asset_classes():
            print("Error")
        if self.build_states():
            print("Error")
        if self.build_properties():
            print("Error")
        #self.build_qr_table()
        return 0



def build():
    db_build = DataBaseBuilder()
    db_build.build()