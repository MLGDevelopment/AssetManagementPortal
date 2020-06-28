import pandas as pd
import os


curr_dir = os.path.dirname(os.path.realpath(__file__))
data_dir = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..', 'data', "external"))

# LOAD DATA
CBSA = os.path.join(data_dir, "CBSA.xlsx")
COUNTIES = os.path.join(data_dir, "Counties.xlsx")
DIVISION = os.path.join(data_dir, "Division.xlsx")
REGIONS = os.path.join(data_dir, "Regions.xlsx")
STATES = os.path.join(data_dir, "States.xlsx")
ZCTA_CBSA = os.path.join(data_dir, "ZCTA_CBSA.xlsx")
ZCTA_COUNTY = os.path.join(data_dir, "ZCTA_County.xlsx")
ZIP_CODES = os.path.join(data_dir, "ZIP Codes.xlsx")

CBSA_DF = pd.read_excel(CBSA)
COUNTIES_DF = pd.read_excel(COUNTIES)
DIVISION_DF = pd.read_excel(DIVISION)
REGIONS_DF = pd.read_excel(REGIONS)
STATES_DF = pd.read_excel(STATES)
ZCTA_CBSA_DF = pd.read_excel(ZCTA_CBSA)
ZCTA_COUNTY_DF = pd.read_excel(ZCTA_COUNTY)
ZIP_CODES_DF = pd.read_excel(ZIP_CODES)

print