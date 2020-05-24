# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np


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

def get_geometry(geo_json, data_json):
    for geo in range(len(geo_json['features'])):
        for name in range(len(data_json)):
            if geo_json['features'][geo]['properties']['name'] == data_json[name]['COMMNAME']:
                data_json[name].update(geo_json['features'][geo]) #change update function
                del data_json[name]['properties'] #change update function

    return data_json


app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index_2.html")

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
    all_data_city['COMMNAME'] = all_data_city['COMMNAME'].map(lambda x: x.lstrip('City of '))
    all_data_city['COMMNAME'] = all_data_city['COMMNAME'].map(lambda x: x.lstrip('Unincorporated - '))
    all_data_city = all_data_city[['COMMNAME','Tot_r_10','Tot_r_20','Tot_r_50','ht_ami', 'population', 'co2_per_hh', 'autos_per_', 'pct_transi', 'res_densit', 'emp_gravit','emp_ndx','h_cost','Black_Afri','Hispanic','White_Alon']]

    cols = ['Tot_r_20', 'population', 'pct_transi', 'Black_Afri','Hispanic','White_Alon']
    all_data_city[cols] = all_data_city[cols].applymap(np.int64)
    all_data_city['Tot_r_20_seg'] = all_data_city['Tot_r_20'].apply(lambda Tot_r_20: get_accessibility_segment(Tot_r_20))
    all_data_city['ht_ami_seg'] = all_data_city['ht_ami'].apply(lambda ht_ami: get_ht_ami_segment(ht_ami))
    cols_to_keep = ['COMMNAME', 'Tot_r_20', 'population', 'pct_transi', 'Black_Afri','Hispanic','White_Alon', 'Tot_r_20_seg', 'ht_ami_seg']
    df_clean = all_data_city[cols_to_keep].dropna()

    data_json = json.loads(df_clean.to_json(orient='records', force_ascii=False))

    with open(data_path + 'geojson/la-county-neighborhoods-v6.geojson') as data_file:
        geo_json = json.load(data_file)

    with open(data_path + 'geojson/data_geo.json', 'w') as data_geo_out:
        data_json = get_geometry(geo_json, data_json)
        json.dump(data_json, data_geo_out)

    return json.dumps(data_json)

if __name__ == "__main__":
    app.run(host='0.0.0.0',port=5005,debug=True)
