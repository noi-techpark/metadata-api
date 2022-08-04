import gspread
import threading
from flask import Flask
from waitress import serve
import os


app = Flask(__name__)

availability = {}

SCHEDULER_TIMEOUT = float(os.getenv("SCHEDULER_TIMEOUT", 10.0))
PORT = os.getenv("PORT", 8080)
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
SPREADSHEET_RANGE = os.getenv("SPREADSHEET_RANGE")

def get_mapping():
    gc = gspread.service_account(filename='./service-account.json')
    worksheet = gc.open_by_key(SPREADSHEET_ID).sheet1
    ws_range = worksheet.range(SPREADSHEET_RANGE)

    mapping = {}
    length = 9
    i = length
    current_dataset_name = ''
    current_station_type = ''
    current_source = ''
    current_open_data = ''

    for cell in ws_range:
        value = cell.value

        if i == length:
            i = 1
            if value != '':
                current_dataset_name = value
                mapping[current_dataset_name] = {}
        elif i == 5 and value != '':
            current_station_type = value
            mapping[current_dataset_name][current_station_type] = {}
        # elif i == 6 and value != '':
        #     current_source = value
        #     mapping[current_dataset_name][current_station_type][current_source] = {}
        elif i == 7 and value != '':
            current_open_data = value
        elif i == 8 and value != '':
            mapping[current_dataset_name]["note"] = value

        mapping[current_dataset_name][current_station_type] = current_open_data
        i += 1
    return mapping

def scheduler():
    global availability
    t = threading.Timer(SCHEDULER_TIMEOUT, scheduler)
    t.start()
    availability = get_mapping()

# initialize availability
availability = get_mapping()

# start scheduler (endless threading hack)
t = threading.Timer(SCHEDULER_TIMEOUT, scheduler)
t.start()

@app.route('/')
def get():
    return availability

if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=PORT)