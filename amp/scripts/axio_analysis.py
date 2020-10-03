import os
import sys
import pandas as pd

packages_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.append(os.path.join(packages_path, 'Scraping'))
sys.path.append(os.path.join(packages_path, 'dbConn'))
from axioDB import session, AxioProperty, RentComp, AxioPropertyOccupancy

all_properties = AxioProperty.fetch_all_property_data()
all_properties = AxioProperty.rows2dict(all_properties)
all_rent_data = RentComp.fetch_all_rent_data()
all_rent_data = RentComp.rows2dict(all_rent_data)
all_occupancy_data = AxioPropertyOccupancy.fetch_all_occ_data()
all_occupancy_data = AxioPropertyOccupancy.rows2dict(all_occupancy_data)

df_properties = pd.DataFrame(all_properties)
df_rent_data = pd.DataFrame(all_rent_data)
rent_data_cols = df_rent_data.columns.drop("property_id").drop('date_added').drop("type")
df_rent_data[rent_data_cols] = df_rent_data[rent_data_cols].apply(pd.to_numeric, errors='coerce')
df_occpancies = pd.DataFrame(all_occupancy_data)
df_occpancies["occupancy"] = df_occpancies["occupancy"].apply(pd.to_numeric, errors='coerce')


df_msa_submarkets = df_properties[['msa', 'submarket_name']].sort_values("msa")
df_rent_data['concessions'] = df_rent_data['avg_market_rent'] - df_rent_data['avg_effective_rent']



print


if __name__ == '__main__':
    pass