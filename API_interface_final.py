#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 10 16:50:28 2024

@author: williamluik
"""

import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


import sys
print(sys.prefix)


SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SPREADSHEET_ID = "1lUcZLprKmdDsDWWknsWbOfKq3VcXvKbTXUhF1FdmcOI"






def grab_sheet():
    credentials = None
    if os.path.exists("token.json"):
        credentials = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("scheduler_credentials.json", SCOPES)
            credentials = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(credentials.to_json())
    
    
    try:
        service = build("sheets", "v4", credentials = credentials)
        sheets = service.spreadsheets()
        
        result = sheets.values().get(spreadsheetId = SPREADSHEET_ID, range = "Back_end").execute()
        values = result.get("values", [])
        
        
        employee_names =[]
        employee_pref = {}
        ability ={}
        availability = {} 
        force_shift ={}
        allocated_max_hours ={}
        allocated_min_hours={}
        emp_num_shifts ={}
        start_shift_ranges={}
        emp_shift_len= {}
        
        
        
        def column_to_index(column):
            index = 0
            for char in column:
                index = index * 26 + (ord(char.upper()) - ord('A')) + 1
            return index - 1
        
        def get_cell_value(cell_location ):
            if service is None or SPREADSHEET_ID is None:
                raise ValueError("Service and Spreadsheet ID must be provided")
        
            try:
                cell_result = service.spreadsheets().values().get(
                    spreadsheetId=SPREADSHEET_ID , range=f"Back_end!{cell_location}").execute()
                cell_value = cell_result.get("values", [])[0][0] if cell_result.get("values", []) else None
                return cell_value
            except HttpError as error:
                print(f"An error occurred: {error}")
                return None
        
        def get_range_values(range_location, data_type=str):
            if service is None or SPREADSHEET_ID is None:
                raise ValueError("Service and Spreadsheet ID must be provided")
        
            try:
                range_result = service.spreadsheets().values().get(
                    spreadsheetId=SPREADSHEET_ID, range=f"Back_end!{range_location}"
                ).execute()
                range_values = range_result.get("values", [])[0] if range_result.get("values", []) else []
        
                # Filter out empty values and convert the remaining values to the specified data type
                if data_type == int:
                    range_values = [int(value) for value in range_values if value]
                elif data_type == float:
                    range_values = [float(value) for value in range_values if value]
                else:
                    range_values = [str(value) for value in range_values if value]
        
                return range_values
            except HttpError as error:
                print(f"An error occurred: {error}")
                return []


        
        days_considering = get_range_values("AIR12:AIX12")

        
        def process_day_availability_and_force_shift(day, employee, row, availability, force_shift, col_start, col_end, col_force_start, col_force_end, col_shift_type, days_considering):
            if day in days_considering:
                # Process availability
                if employee not in availability:
                    availability[employee] = {}
        
                day_list = []
                for avail in row[col_start:col_end]:
                    if avail == "0" or avail == "1":
                        day_list.append(int(avail))
                availability[employee][day] = day_list
        
                # Process force shift
                force_list = []
                for force_time in row[col_force_start:col_force_end]:
                    if force_time == "0" or force_time == "1":
                        force_list.append(int(force_time))
        
                if force_list:
                    if employee not in force_shift:
                        force_shift[employee] = {}
                    force_shift[employee][day] = {"segments": force_list}
                    if row[col_shift_type] == "FP":
                        force_shift[employee][day]["job_type"] = 0
                    elif row[col_shift_type] == "BM":
                        force_shift[employee][day]["job_type"] = 1
                    elif row[col_shift_type] == "O":
                        force_shift[employee][day]["job_type"] = 2
                    elif row[col_shift_type] == "HYB":
                        force_shift[employee][day]["job_type"] = 3
                        
        def populate_hourly_requirements_BM(values, end_req_col):
            day_column_map = {
                "Sunday": "AJG",
                "Monday": "AJA",
                "Tuesday": "AJB",
                "Wednesday": "AJC",
                "Thursday": "AJD",
                "Friday": "AJE",
                "Saturday": "AJF"
            }
            
            days_considering_list = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
            hourly_requirements_BM = {day: [] for day in days_considering_list}
            
            if values:
                for row in values[2:end_req_col]:  # Ensure this includes the ending
                    for day in days_considering_list:
                        day_column = day_column_map[day]
                        if len(row) > column_to_index(day_column):
                            day_info = row[column_to_index(day_column)]
                            if day_info is not None:
                                hourly_requirements_BM[day].append(int(day_info))
            
            return hourly_requirements_BM
        
                
        def process_shift_lengths(values, days_considering):
            shift_len_columns = {
                "Sunday": "AJL",
                "Monday": "AJM",
                "Tuesday": "AJN",
                "Wednesday": "AJO",
                "Thursday": "AJP",
                "Friday": "AJQ",
                "Saturday": "AJR"
            }
        
            shift_lengths = {}
        
            def column_to_index(column):
                index = 0
                for char in column:
                    index = index * 26 + (ord(char.upper()) - ord('A')) + 1
                return index - 1
        
            for row in values[4:]:
                employee = row[0] if row[0] else None
                if employee:
                    shift_lengths[employee] = {}
                    for day, column in shift_len_columns.items():
                        if day in days_considering:
                            col_index = column_to_index(column)
                            shift_length = float(row[col_index]) if col_index < len(row) and row[col_index] != '' else None
                            if shift_length is not None:
                                shift_lengths[employee][day] = shift_length
            return shift_lengths


        





        end_roster_col = int(get_cell_value("B3")) +4 +1  
        
        column_index_AJI = column_to_index("AJI")
        column_index_AJJ = column_to_index("AJJ")
        
        shift_len_sunday_col = column_to_index("AJL")
        shift_len_monday_col = column_to_index("AJM")
        shift_len_tuesday_col = column_to_index("AJN")
        shift_len_wednesday_col = column_to_index("AJO")
        shift_len_thursday_col = column_to_index("AJP")
        shift_len_friday_col = column_to_index("AJQ")
        shift_len_saturday_col = column_to_index("AJJR")
        
        if values:
            shift_lengths= process_shift_lengths(values, days_considering)
            for row in values[4: end_roster_col]:
                employee = row[0] if row[0] else None
                pref = float(row[1]) if row[1] else None
                FP_check = row[3] if row[3] else None
                BM_check =row[4] if row[4] else None
                O_check = row[5] if row[5] else None
                allocated_min_hour = float(row[6]) if row[6] else None
                allocated_max_hour= float (row[7]) if row[7] else None
                num_shifts = int(row[2]) if row[2] is not None and row[2] != '' else None
                
                start_start_shift_range = float (row[column_index_AJI]) if column_index_AJI < len(row) and row[column_index_AJI] else None
                end_start_shift_range =float(row[column_index_AJJ]) if column_index_AJJ < len(row) and row[column_index_AJJ] else None
                
                shift_len_sunday = float (row[shift_len_sunday_col]) if shift_len_sunday_col < len(row) and row[shift_len_sunday_col] else None
                shift_len_monday =float (row[shift_len_monday_col]) if shift_len_monday_col < len(row) and row[shift_len_monday_col] else None
                shift_len_tuesday =  float (row[shift_len_tuesday_col]) if shift_len_tuesday_col < len(row) and row[shift_len_tuesday_col] else None
                shift_len_wednesday = float (row[shift_len_wednesday_col]) if shift_len_wednesday_col < len(row) and row[shift_len_wednesday_col] else None
                shift_len_thursday =float (row[shift_len_thursday_col]) if shift_len_thursday_col < len(row) and row[shift_len_thursday_col] else None
                shift_len_friday =float (row[shift_len_friday_col]) if shift_len_friday_col < len(row) and row[shift_len_friday_col] else None
                shift_len_saturday= float (row[shift_len_saturday_col]) if shift_len_saturday_col < len(row) and row[shift_len_saturday_col] else None
                
                
                
                
                # Adding emp info to datasets only if data is not None
                if employee is not None :
                    employee_names.append(employee)
                if  pref is not None:
                    employee_pref[employee] = pref
                    
                if FP_check and BM_check and O_check is not None:
                    if employee not in ability: #initalize the emp info
                        ability[employee] = {"FP": 0, "BM": 0, "O":0}
                    if FP_check == "TRUE":
                        ability[employee]["FP"] = 1
                    if BM_check == "TRUE":
                        ability[employee]["BM"] = 1
                    if O_check =="TRUE":
                        ability[employee]["O"] = 1
                
                if allocated_min_hour is not None:
                    allocated_min_hours[employee] = ( allocated_min_hour)
                if allocated_max_hour is not None:
                    allocated_max_hours[employee] =  (allocated_max_hour)
                if num_shifts is not None:
                    emp_num_shifts[employee] = (num_shifts)
                if start_start_shift_range is not None and end_start_shift_range is not None:
                    start_shift_ranges[employee] = [start_start_shift_range, end_start_shift_range]
                # for shift_len in [shift_len_sunday, shift_len_monday , shift_len_tuesday , shift_len_wednesday , shift_len_thursday , shift_len_friday ,shift_len_saturday]:
                #     emp_shift_len[employee][]
                        
                #_______________________________________________________________________________________________
                #_______________________________________________________________________________________________
                        


                # Example usage within your main code
                days = {
                    "Sunday": {"avail_start": 'I', "avail_end": 'BU', "force_start": 'BV', "force_end": 'EH', "shift_type": 'EI'},
                    "Monday": {"avail_start": 'EJ', "avail_end": 'GV', "force_start": 'GW', "force_end": 'JI', "shift_type": 'JJ'},
                    "Tuesday": {"avail_start": 'JK', "avail_end": 'LW', "force_start": 'LX', "force_end": 'OJ', "shift_type": 'OK'},
                    "Wednesday": {"avail_start": 'OL', "avail_end": 'QX', "force_start": 'QY', "force_end": 'TK', "shift_type": 'TL'},
                    "Thursday": {"avail_start": 'TM', "avail_end": 'VY', "force_start": 'VZ', "force_end": 'YL', "shift_type": 'YM'},
                    "Friday": {"avail_start": 'YN', "avail_end": 'AAZ', "force_start": 'ABA', "force_end": 'ADM', "shift_type": 'ADN'},
                    "Saturday": {"avail_start": 'ADO', "avail_end": 'AGA', "force_start": 'AGB', "force_end": 'AIN', "shift_type": 'AIO'}
                }

                for day, columns in days.items():
                    process_day_availability_and_force_shift(
                        day,
                        employee,
                        row,
                        availability,
                        force_shift,
                        column_to_index(columns["avail_start"]),
                        column_to_index(columns["avail_end"]),
                        column_to_index(columns["force_start"]),
                        column_to_index(columns["force_end"]),
                        column_to_index(columns["shift_type"]),
                        days_considering
                    )


                
                #_______________________________________________________________________________________________
  
            #_______________________________________________________________________________________________
            #_______________________________________________________________________________________________
            #Operations information
            #tab in because we need to look through the rows again:
            
            

            
            min_shift_len_hrs = float(get_cell_value("AIR3"))
            max_shift_len_hrs = float(get_cell_value("AIR4"))
            hrs_until_break = float(get_cell_value("AIR5"))
            break_len = float (get_cell_value("AIR6"))
            start_hour = float (get_cell_value("AIR7"))
            end_hour = float (get_cell_value("AIR8"))
            min_weekly_FP_hrs = float(get_cell_value("AIR11"))
            sheets_time_limit = int(get_cell_value("AIR16"))
            earliest_shift_end = float (get_cell_value("AIR17"))
            latest_shift_start = float(get_cell_value("AIR18") )
            earliest_latest_flag = str(get_cell_value("AIR19"))
            FP_latest_hr = int(get_cell_value("AIR21"))
            latest_FP_flag = str(get_cell_value("AIR22"))
            

            
            
            
            FP_cutoff_hour= float (get_cell_value("AIR9"))

            total_labor_hour_limit = float (get_cell_value("AIR10"))
            
            
            job_type = get_range_values("AIR13:AIT13")

            min_morning_FP_hrs = get_range_values("AIR14:AIX14", float)
            min_daily_FP_hrs = get_range_values("AIR15:AIX15", float)
            max_daily_O_hrs = get_range_values("AIR20:AIX20", float)

            # print("min_daily_FP", min_daily_FP)
            # print("min_morning_FP", min_morning_FP)



            # print("min_shift_len_hrs", min_shift_len_hrs)
            # print("max_shift_len_hrs", max_shift_len_hrs)
            # print("hours until break", hrs_until_break)
            # print("break_len",break_len)
            # print("start_hour", start_hour)
            # # print("end_hour", end_hour)
            # print("FP cutoff_hour", FP_cutoff_hour)
            # print("min_morning_FP", min_morning_FP_hrs)
            
                    
                        
                        
                        
                
            # print("Employees:", employee_names)
            # print("_____________________________________________")
            # print("Employees Preferences:", employee_pref)
            # print("_____________________________________________")
            # print ("Emp ability:", ability)
            # print("_____________________________________________")
            # print("Allocated min hours", allocated_min_hours)
            # print("_____________________________________________")
            # print("Allocated max hours", allocated_max_hours)
            # print("_____________________________________________")
            # print("force shifts", force_shift)
            # print("_____________________________________________")
            # print("Avilability", availability)
            # print (len(availability["Leah Lem"]["Tuesday"]))
 
            # print("_____________________________________________")
            # print (availability["Jose Juarez"]["Sunday"])
            # print("Days considering", days_considering)
            # print("Job Types:", job_type)


            
        #_______________________________________________________________________________________________
        #_______________________________________________________________________________________________
        #Hours BM Requirement information



        
        end_req_col = int(get_cell_value("AJD1")) + 2  
        
        # Assuming values is defined and fetched from somewhere
        hourly_requirements_BM = populate_hourly_requirements_BM(values, end_req_col)



            
        return {
            "hourly_requirements_BM": hourly_requirements_BM,
            "job_type": job_type,
            "days_considering": days_considering,
            "total_labor_hour_limit": total_labor_hour_limit,
            "min_morning_FP_hrs": min_morning_FP_hrs,
            "FP_cutoff_hour": FP_cutoff_hour,
            "end_hour": end_hour,
            "start_hour": start_hour,
            "break_len": break_len,
            "hrs_until_break": hrs_until_break,
            "max_shift_len_hrs": max_shift_len_hrs,
            "min_shift_len_hrs": min_shift_len_hrs,
            "availability": availability,
            "force_shift": force_shift,
            "allocated_max_hours": allocated_max_hours,
            "allocated_min_hours": allocated_min_hours,
            "ability": ability,
            "employee_pref": employee_pref,
            "employee_names": employee_names,
            "min_daily_FP_hrs": min_daily_FP_hrs, 
            "min_weekly_FP_hrs": min_weekly_FP_hrs, 
            "sheets_time_limit": sheets_time_limit,
            "latest_shift_start": latest_shift_start,
            "earliest_shift_end": earliest_shift_end, 
            "earliest_latest_flag": earliest_latest_flag, 
            "max_daily_O_hrs": max_daily_O_hrs, 
            "FP_latest_hr": FP_latest_hr, 
            "latest_FP_flag": latest_FP_flag, 
            "emp_num_shifts": emp_num_shifts,
            "start_shift_ranges": start_shift_ranges, 
            "shift_lengths": shift_lengths
            
            
        }

     
        
    except HttpError as error:
        print(error)
        
grab_sheet()      
# print(grab_sheet())