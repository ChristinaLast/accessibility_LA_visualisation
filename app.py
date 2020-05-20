# -*- coding: utf-8 -*-

import pandas as pd
import geopandas as gpd

import fiona
# Enable fiona driver
gpd.io.file.fiona.drvsupport.supported_drivers['KML'] = 'rw'

from shapely.geometry import MultiPolygon, shape

from flask import Flask
from flask import render_template
import json


data_path = './input/'

def get_accessibility_segment(Tot_r_20):
    if Tot_r_20 <= 200000:
        return '200000-'
    elif Tot_r_20 <= 350000:
        return '200000-350000'
    elif Tot_r_20 <= 500000:
        return '350000-500000'
    elif Tot_r_20 <= 650000:
        return '500000-650000'
    elif Tot_r_20 <= 750000:
        return '650000-750000'
    else:
        return '750000+'
def get_ht_ami_segment(ht_ami):
    if ht_ami <= 45:
        return '45%-'
    elif ht_ami <= 55:
        return '45%-55%'
    elif ht_ami <= 65:
        return '55%-65%'
    elif ht_ami <= 75:
        return '65%-75%'
    elif ht_ami <= 85:
        return '75%-85%'
    else:
        return '85%+'

def get_location(geometry, city_json):

    geometry = MultiPolygon(geometry)

    for record in city_json['features']:
        polygon = shape(record['geometry'])
        if polygon.contains(MultiPolygon):
            return record['properties']['name']
    return 'other'

with open(data_path + 'geojson/Los_Angeles_Neighborhood_Map.geojson') as data_file:
    city_json = json.load(data_file)

city_json
app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/data")
def get_data():
    all_data_block = pd.read_csv(data_path + 'Spatial_weights_pred.csv')
    pd.set_option('display.max_columns', None)
    all_data_city = all_data_block.drop(['Unnamed: 0','CB10','OBJECTID_1','GEOID10','CTCB10','BG10','X_CENTER','Y_CENTER','Shape_Leng','Shape_Area','BlockId','BlockgroupId','TractId'], axis=1)
    all_data_city_mean = all_data_city.groupby('COMMNAME').mean().reset_index().drop(['Black_Afri','Hispanic','White_Alon'],axis=1)
    all_data_ethnicity = all_data_city[['COMMNAME', 'Black_Afri','Hispanic','White_Alon']]
    all_data_ethnicity_sum = all_data_ethnicity.groupby('COMMNAME').sum().reset_index()
    all_data_city = all_data_city_mean.merge(all_data_ethnicity_sum, on='COMMNAME')
    all_data_city = all_data_city.reset_index(drop=True)
    all_data_city
    all_data_city['COMMNAME'] = all_data_city['COMMNAME'].map(lambda x: x.lstrip('City of '))
    all_data_city['COMMNAME'] = all_data_city['COMMNAME'].map(lambda x: x.lstrip('Unincorporated - '))
    # Read file
    city_geo = gpd.read_file('input/shape/Los Angeles Neighborhood Map.kml', driver='KML')

    city_data_geo = pd.merge(all_data_city, city_geo, left_on='COMMNAME', right_on='Name')
    city_data_geo = city_data_geo[['COMMNAME','Tot_r_10','Tot_r_20','Tot_r_50','ht_ami', 'population', 'co2_per_hh', 'autos_per_', 'pct_transi', 'res_densit', 'emp_gravit','emp_ndx','h_cost','Black_Afri','Hispanic','White_Alon','geometry']]

    city_data_geo['Tot_r_20_seg'] = city_data_geo['Tot_r_20'].apply(lambda Tot_r_20: get_accessibility_segment(Tot_r_20))


    cols_to_keep = ['timestamp', 'longitude', 'latitude', 'phone_brand_en', 'gender', 'age_segment', 'geometry']
    df_clean = city_data_geo[cols_to_keep].dropna()

    return df_clean.to_json(orient='records')


if __name__ == "__main__":
    app.run(host='0.0.0.0',port=5000,debug=True)
