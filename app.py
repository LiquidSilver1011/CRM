from flask import Flask, render_template, request, redirect, url_for
import gspread
from google.oauth2 import service_account
from google.oauth2.service_account import Credentials
from auth import spreadsheet_service
from googleapiclient.discovery import build
import pandas as pd


app = Flask(__name__)

# Initialize the Sheets API service
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SERVICE_ACCOUNT_FILE = 'credentials.json'  # Your service account credentials file

credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
sheets_service = build('sheets', 'v4', credentials=credentials).spreadsheets()


client = gspread.authorize(credentials)

sheet = client.open_by_url('https://docs.google.com/spreadsheets/d/1GpKYtyMKnObkywhgJdyRayuISzav4eMY5RjXk7mk7sQ')
sheet_instance = sheet.get_worksheet(0)

# Constants to go here
expected_headers = ['S. No.', 'Name', 'Email ID', 'Phone no.', 'Address', 'Query message']
max_col_num = 6

# Initialization when loading the crud operation worksheet
@app.route('/crud')
def crud():
    sheet_instance = sheet.get_worksheet(0)
    serial_numbers = sheet_instance.col_values(1) # Loads all serial numbers through which main operations would take place on user interface
    return render_template('crud.html')


@app.route('/')
def login():
    return render_template('login.html')

@app.route('/submit', methods=['POST'])
def submit():
    username = request.form['username']
    password = request.form['password']
    # Validation for the username and password for login page would go here
    return redirect(url_for('crud'))


## VIEWING OPERATIONS

def view(index):
    # The code below returns the entire record/row values for a given serial number
    serial_numbers = sheet_instance.col_values(1)
    row_data = sheet_instance.row_values(index)
    return row_data

@app.route('/validate', methods = ['POST'])
def validate():
    # Validation when serial number entered for viewing operation
    serial_numbers = sheet_instance.col_values(1)
    serial_number = request.form['serial_number'] # Requests value of html input tag with 'serial_number' id
    if serial_number in serial_numbers:
        try:
            serial_number = int(serial_number)

            data = view(serial_number + 1)
            return render_template('crud.html', data = data) # Renders crud.html again with data for the row 
        
        except ValueError:
            return "Please enter a valid number"
    else:
        return "Serial number doesn't exist in the google sheet"


## ADDING OPERATIONS

@app.route('/add', methods = ['POST'])
def add():
    # Getting data from html form that is to be added to new row
    serial_numbers = sheet_instance.col_values(1)
    name = request.form['name']
    email = request.form['email']
    phone = request.form['phone']
    address = request.form['address']
    query_message = request.form['query_message']

    serial_number = int(serial_numbers[-1]) + 1
    
    sheet_instance.append_rows([[serial_number, name, email, phone, address, query_message]])
    return render_template('crud.html')
    

## DELETE OPERATIONS

@app.route('/delete', methods=['POST'])


def delete():
    serial_number = request.form['serial_number']
    confirm_serial_number = request.form['confirm_serial_number']

    # Validation
    if serial_number == confirm_serial_number:
        serial_numbers = sheet_instance.col_values(1)
        if serial_number in serial_numbers:
            row_to_delete = serial_numbers.index(serial_number) + 1  # Adding a 1 to serial_number to get row index (accounts for the first header row)
    
        else:
            return "Serial number doesn't exist"
    else:
        return "Serial numbers don't match"

    max_row = int(serial_numbers[-1]) + 1

    # It
    for i in range(row_to_delete, max_row):
        values = sheet_instance.row_values(i + 1)

        #Updating each individual cell in the row
        for j in range(2, max_col_num + 1):
            sheet_instance.update_cell(i, j, values[j-1])
        
    # Making the last row all null values to avoid duplicate rows    
    for j in range(1, max_col_num + 1):
        sheet_instance.update_cell(max_row, j, '')
    return render_template('crud.html')


## UPDATING OPERATIONS

@app.route('/update', methods=['POST'])
def update_record():
    serial_numbers = sheet_instance.col_values(1)
    serial_number = request.form['serial_number']
    column_header = request.form['column_header']
    new_value = request.form['new_value']
    
    # Validation
    if serial_number in serial_numbers:
        try:
            rowNum = int(serial_number) + 1
            colNum = int(column_header) + 1
            sheet_instance.update_cell(rowNum, colNum, new_value)

            return render_template('crud.html')
        except ValueError:
            return "Please enter a valid number"
    else:
        return "Serial number doesn't exist in the google sheet"
  


# MAIN APP LOADING
if __name__ == '__main__':
    app.run(debug=True)
