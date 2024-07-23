#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 10 09:09:51 2024

@author: williamluik
"""

import json
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from Scheduler_final import run_scheduler
from API_interface_final import grab_sheet


SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SPREADSHEET_ID = "110KkeoBMKEB48OogS5E5X3LZN4liKbKEQJzpx8sYv8E"
SHEET_NAME = "Final_schedule"

def get_service():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "scheduler_credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    service = build("sheets", "v4", credentials=creds)
    return service

def load_data_from_json(filename):
    with open(filename, 'r') as f:
        data = json.load(f)
    return data

def update_sheet(service, spreadsheet_id, sheet_name, data):
    try:
        body = {
            "range": f"{sheet_name}!A1",
            "majorDimension": "ROWS",
            "values": data
        }
        result = service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id, range=f"{sheet_name}!A1",
            valueInputOption="RAW", body=body).execute()
        print(f"{result.get('updatedCells')} cells updated.")
    except HttpError as error:
        print(f"An error occurred: {error}")

def main():
    run_scheduler()
    service = get_service()
    data = load_data_from_json('schedule_data.json')
    update_sheet(service, SPREADSHEET_ID, SHEET_NAME, data)

if __name__ == "__main__":
    main()



