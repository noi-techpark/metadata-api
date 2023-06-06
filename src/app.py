# SPDX-FileCopyrightText: NOI Techpark <digital@noi.bz.it>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import gspread
import threading
from flask import Flask
from flask_cors import CORS
from waitress import serve
import os
import logging
import requests
import time


logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)
app = Flask(__name__)
CORS(app)

availability = {}

API_URL = os.getenv(
    "API_URL", "https://mobility.api.opendatahub.testingmachine.eu/v2/flat,node/")
SCHEDULER_TIMEOUT = float(os.getenv("SCHEDULER_TIMEOUT", 360.0))
PORT = os.getenv("PORT", 8080)
SPREADSHEET_ID = os.getenv(
    "SPREADSHEET_ID", "1ES48HODXtPH6sdWV2EinI-n1IEY2hHOD7arRQ10Mb7E")
SPREADSHEET_RANGE = os.getenv("SPREADSHEET_RANGE", "A1:K500")
SPREADSHEET_MOBILITY = os.getenv("SPREADSHEET_MOBILITY", "GeneratedMobility")



def generate_sheet(mapping):
    gc = gspread.service_account(filename='../service-account.json')

    array = []
    for key in mapping.keys():
        for value in mapping[key].keys():
            array.append([key,value,mapping[key][value]])

    worksheet = gc.open_by_key(SPREADSHEET_ID).worksheet(SPREADSHEET_MOBILITY)
    worksheet.update('B2:D255', array)


def api_get(url):
    headers = {}
    response = requests.get(url, headers=headers)
    logging.debug("get: " + url)
    # sleep 1s because of quota
    time.sleep(1)
    return response.json()


def get_mapping():
    global API_URL
    mapping = {}
    station_types = api_get(API_URL)

    for station_type in station_types:
        origins = api_get(station_type["self.stations"] +
                      "?select=sorigin&where=sactive.eq.true")["data"]

        if len(origins) > 0:
            mapping[station_type["id"]] = {}
            for origin in origins:
                data = api_get(station_type["self.stations+datatypes+measurements"] +
                           "?where=sorigin.eq." + str(origin["sorigin"]))["data"]

                mapping[station_type["id"]][origin["sorigin"]] = "closed"
                if len(data) > 0:
                    mapping[station_type["id"]][origin["sorigin"]] = "open"

    return mapping


def scheduler():
    global availability
    t = threading.Timer(SCHEDULER_TIMEOUT, scheduler)
    t.start()
    availability = get_mapping()
    generate_sheet(availability)


# initialize availability
availability = get_mapping()
generate_sheet(availability)


# start scheduler (endless threading hack)
t = threading.Timer(SCHEDULER_TIMEOUT, scheduler)
t.start()


@app.route('/')
def get():
    logging.info("GET request")
    return availability


if __name__ == "__main__":
    logging.info("Start server")
    serve(app, host="0.0.0.0", port=PORT)
