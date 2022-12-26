import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
import json
import requests
import time
import urllib.parse
from base64 import b64encode
import hmac
import hashlib
import binascii
import datetime
from dotenv import load_dotenv
import os

#---------------------Fleet config ---------------------#

logo = st.sidebar.image('logo.jpg')

d = st.sidebar.date_input("Plan", datetime.date.today())
st.write('Tour planning for:', str(d)+"T"+"07:00"+":00.000Z")

form = st.sidebar.form("tpa_form")

fixed_cost = form.slider('Fixed cost', 0, 10, 5)
distance_cost = form.slider('Distance cost (per km)', 0, 10, 5)
time_cost = form.slider('Time cost (per Hour)', 0, 20, 10)

vehicle_capacity = form.text_input('Vehicle capacity (Boxes)', 20)
vehicle_amount = form.text_input('Nr. of Vehicles', 10)

vehicle_profile = form.selectbox('Vehicle Profile',('car', 'truck'))

shift = form.slider("Vehicle shift:", 0, 23, (6, 23))

show_json = form.checkbox('Show Request/Response')

form.form_submit_button("Submit")

# Tour Planning Request
uploaded_file = st.file_uploader("Choose a file")

if uploaded_file is not None:
    df_plan = pd.read_excel(uploaded_file, sheet_name='plan')
    df_fleet = pd.read_excel(uploaded_file, sheet_name='fleet')
    valid_file = True
else:
    st.write("Please upload valid excel file.")
    valid_file = False

if valid_file:

    st.subheader("Plan")
    st.dataframe(df_plan)

    st.subheader("Fleet")
    st.dataframe(df_fleet)

    trp_fleet = {'types': [], 'profiles': []}
    trp_plan = {'jobs': [], 'relations': []}


    #job start and end
    shift_start_timestamp = str(d)+"T"+str(shift[0]).zfill(2)+":00:00Z"
    shifts_end_timestamp = str(d)+"T"+str(shift[1]).zfill(2)+":00:00Z"


    car_shift_start = {'time': shift_start_timestamp,
                       'location': {'lat': float(df_fleet['shift_start_lat'][0]),
                                    'lng': float(df_fleet['shift_start_lng'][0])
                                    }}

    car_shift_end = {'time': shifts_end_timestamp,
                      'location': {'lat': float(df_fleet['shift_end_lat'][0]),
                                   'lng': float(df_fleet['shift_end_lng'][0])
                                   }}



    if vehicle_profile == 'car':

        vehicle_description = {'id': 'vehicle_1',
                              'profile': 'sprinter',
                              'costs': {'fixed': (float(fixed_cost)),
                                        'distance': distance_cost/float(1000),
                                        'time': time_cost/float(3600)
                                        },
                              'shifts': [{'start': car_shift_start,
                                          'end': car_shift_end}],
                              'capacity': [int(vehicle_capacity)],
                              'amount': int(vehicle_amount)}

        vehicle_profile_description = {'type': 'car', 'name': 'sprinter'}

    elif vehicle_profile == 'truck':

        vehicle_description = {'id': 'truck1',
                              'profile': 'scania',
                              'costs': {'fixed': (float(fixed_cost)),
                                        'distance': (float(distance_cost)),
                                        'time': (float(time_cost))
                                        },
                              'shifts': [{'start': car_shift_start,
                                          'end': car_shift_end}],
                              'capacity': [vehicle_capacity],
                              'amount': vehicle_amount}

        vehicle_profile_description = {'type': 'truck', 'name': 'scania'}

    trp_fleet['types'] = [vehicle_description]
    trp_fleet['profiles'] = [vehicle_profile_description]

    # Plan
    my_jobs = []

    i = 0
    for _, row in df_plan.iterrows():
        place = {}
        #job start and end
        job_start_timestamp = str(d)+"T"+str(row['job_start'])+".000Z"
        job_end_timestamp = str(d)+"T"+str(row['job_end'])+".000Z"

        if row['job_type'] == 'delivery':
            place = {'deliveries' : []}
            place['deliveries'].append({'times':[[job_start_timestamp, job_end_timestamp]],
                                               'location': {'lat': row['job_lat'], 'lng': row['job_lng']},
                                               'duration': row['job_duration'],
                                               'demand': [row['job_demand']]})

        if row['job_type'] == 'pickup':
            place = {'pickups' : []}
            place['pickups'].append({'times':[[job_start_timestamp, job_end_timestamp]],
                                               'location': {'lat': row['job_lat'], 'lng': row['job_lng']},
                                               'duration': row['job_duration'],
                                               'demand': [row['job_demand']]})

        my_jobs.append({'id': row['job_id'], 'places': place})


    trp_plans = {'jobs': my_jobs}

    trp_request = {'id': 'request1',
                   'fleet': trp_fleet,
                   'plan': trp_plans}

    trp_request_json = json.dumps(trp_request)

    if show_json:
        st.subheader("Request")
        st.json(trp_request_json)

    # visualization
    centroid_lat = df_plan['job_lat'].mean()
    centroid_lng = df_plan['job_lng'].mean()

    if show_json:
        st.subheader("Response")
        st.json(tpa_response.text)

    st.subheader("Solution")
