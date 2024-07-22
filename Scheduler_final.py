#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jul 15 07:53:18 2024

@author: williamluik
"""


import json
import pulp as lp
from API_interface_final import grab_sheet
import datetime
import os

def lp_solver():
    def print_with_timestamp(message):
        # Get the current date and time
        current_time = datetime.datetime.now()
        # Format the time as a string
        timestamp = current_time.strftime("%Y-%m-%d %H:%M:%S")
        # Print the message with the timestamp
        print(f"[{timestamp}] {message}")
    
    
    
    
    data = grab_sheet()
    
    hourly_requirements_BM = data["hourly_requirements_BM"]
    job_type = data["job_type"]
    days_considering = data["days_considering"]
    total_labor_hour_limit = data["total_labor_hour_limit"]
    min_morning_FP_hrs = data["min_morning_FP_hrs"]
    FP_cutoff_hour = data["FP_cutoff_hour"]
    end_hour = data["end_hour"]
    start_hour = data["start_hour"]
    break_len = data["break_len"]
    hrs_until_break = data["hrs_until_break"]
    max_shift_len_hrs = data["max_shift_len_hrs"]
    min_shift_len_hrs = data["min_shift_len_hrs"]
    availability = data["availability"]
    force_shift = data["force_shift"]
    allocated_max_hours = data["allocated_max_hours"]
    allocated_min_hours = data["allocated_min_hours"]
    ability = data["ability"]
    employee_pref = data["employee_pref"]
    employee_names = data["employee_names"]
    min_daily_FP_hrs = data["min_daily_FP_hrs"]
    min_weekly_FP_hrs = data["min_weekly_FP_hrs"]
    sheets_time_limit = data["sheets_time_limit"]
    
    
    print("_______Operations info check________")
    print("days_considering", days_considering)
    print("total_labor_hour_limit", total_labor_hour_limit)
    print("min_morning_FP_hrs______________", min_morning_FP_hrs)
    print("FP_cutoff_hour",FP_cutoff_hour, " AM")
    
    # Define data for hours. based on 24 hour time
    
    print("__________________________________________________")
    print("Run optimization software")
    print("__________________________________________________")
    print_with_timestamp("start time of run")
    print( "Software will run for", sheets_time_limit/60, " minutes" )
    print(sheets_time_limit )
    

    
    end_hour_backend =22
    start_hour_backend = 6
    
    num_hours = end_hour_backend - start_hour_backend   # Number of hours in the specified range
    segment_minutes =15
    num_segments = int(((num_hours) * (60 / segment_minutes)))  # Number of 15-minute segments. 
    



    # Create min_morning_FP by multiplying each element in min_morning_FP_hrs by (60 / segment_minutes)
    min_morning_FP = [hours * (60 / segment_minutes) for hours in min_morning_FP_hrs]
    

    
    num_days = len(days_considering)  

    num_job = len(job_type)
    
    # min max shift hours
    min_shift_len = min_shift_len_hrs *(60/segment_minutes)
    max_shift_len = max_shift_len_hrs *(60/segment_minutes)
    
    # Calculate min_daily_FP_hrs by multiplying min_daily_FP by (60 / segment_minutes)
    min_daily_FP = [hours * (60 / segment_minutes) for hours in min_daily_FP_hrs]
    min_weekly_FP = min_weekly_FP_hrs * (60 / segment_minutes)
    
    #names
    num_employees = len(employee_names)
    
    
    
    # Calculate the indices for hours before the cutoff hour
    hours_before_cutoff = [j for j in range(int(( FP_cutoff_hour - start_hour_backend ) * (60/segment_minutes)))] # plus 1 so that we include the cutooff hour. Range is not inclusive
    
    
    # Initialize the LP problem
    prob = lp.LpProblem("Employee_Scheduling", lp.LpMinimize)
    
    # Decision variables
    # x[i][d][j] is 1 if employee i works during hour j on day d, 0 otherwise
    x = [[[[lp.LpVariable(f"x_{i}_{d}_{j}_{a}", cat=lp.LpBinary) for a in range(num_job)] for j in range(num_segments)] for d in range(num_days)] for i in range(num_employees)]
    
    # y[i][d] is 1 if employee i works any hours at all on day d, 0 otherwise
    y = [[lp.LpVariable(f"y_{i}_{d}", cat=lp.LpBinary) for d in range(num_days)] for i in range(num_employees)]
    
    # f[i][d][j] is 1 for the one hour when they start to work on day d. This is the start flag so only consecutive shifts
    f = [[[lp.LpVariable(f"f_{i}_{d}_{j}", cat=lp.LpBinary) for j in range(num_segments)] for d in range(num_days)] for i in range(num_employees)]
    
    # # Objective function: minimize the total number of hours team works
    # prob += lp.lpSum(x[i][d][j] for i in range(num_employees) for d in range(num_days) for j in range(num_segments))
    
    # #Objective function: minimize the total number of people working
    # prob+= lp.lpSum(f[i][d][j]  for i in range(num_employees) for d in range(num_days) for j in range(num_segments))
    
    # # Objective function: minimize the hours worked
    # prob += lp.lpSum(x[i][d][j][a] for i in range(num_employees) for d in range(num_days) for j in range(num_segments) for a in range(num_job))
    
    #______when changing objective functions need to consider changing LPMaximize to LPMinimize
    # Objective function: maximize the preference minus hour worked. It is on 2 lines bc so long. we can make this weighted as well is we care more about one over the other
    prob += - (lp.lpSum(employee_pref [employee_names[i]] * lp.lpSum(x[i][d][j][a] for d in range(num_days) for j in range(num_segments)) for i in range(num_employees) for a in range(num_job))/5) \
      + (lp.lpSum(x[i][d][j][a] for i in range(num_employees) for d in range(num_days) for j in range(num_segments) for a in range(num_job)))
    
    
    
    
    #Constraints:
    for i in range(num_employees):
        # Constraint: total hours worked over the days must be under the maximum allowed hours per employee
        prob += lp.lpSum(x[i][d][j][a] for d in range(num_days) for j in range(num_segments) for a in range(num_job)) <=  allocated_max_hours [employee_names[i]] *(int (60/segment_minutes))
        prob += lp.lpSum(x[i][d][j][a] for d in range(num_days) for j in range(num_segments) for a in range(num_job)) >=  allocated_min_hours [employee_names[i]] *(int(60/segment_minutes))
        for d in range(num_days):
            for a in range(num_job):
                # Constraint: if employee starts working at start time (7 am), then f[i][d][0] = 1 for any job type 'a'
                prob += f[i][d][0] >= x[i][d][0][a]  # Ensure f[i][d][0] is set to 1 if x[i][d][0][a] is 1 for job type 'a'
                
            #Constraint: Min & Max hours per emploee per day or none hours at all
            prob += lp.lpSum(x[i][d][j][a] for j in range(num_segments) for a in range(num_job)) >= min_shift_len * y[i][d]  # Minimum hours if y[i][d] == 1
            prob += lp.lpSum(x[i][d][j][a] for j in range(num_segments) for a in range(num_job)) <= max_shift_len * y[i][d]  # Maximum hours if y[i][d] == 1
            
            # Constraints: ensure f[i][d][j] sums to 1 for each employee per day. Can only start once
            prob += lp.lpSum(f[i][d][j] for j in range(num_segments)) == y[i][d]
            for j in range(num_segments) : 
                prob += lp.lpSum(x[i][d][j][a] for a in range(num_job)) <=1  #Constraint: can only work one shift type at a time
                
                #Constraint: Consider skill abilities If employee does not have FP ability, they cannot be assigned to FP tasks (job_type[0])
                if ability[employee_names[i]]["FP"] == 0:
                    prob += x[i][d][j][0] == 0
                # If employee does not have BM ability, they cannot be assigned to BM tasks (job_type[1])
                if ability[employee_names[i]]["BM"] == 0:
                    prob += x[i][d][j][1] == 0
                
                #Constraint: emp can only work during available hours
                if availability[employee_names[i]][days_considering[d]][j] == 0:  
                    for a in range(num_job):
                        prob += x[i][d][j][a] == 0
                 
    
    
    # Constraints: enforce f[i][d][j+1] == 1 when total x[i][d][j] == 0 and total x[i][d][j+1] == 1 across all job types
    for i in range(num_employees):
        for d in range(num_days):
            for j in range(num_segments - 1):
                # Sum over all job types to check if there's a transition from 0 to 1 in total working hours
                prob += f[i][d][j+1] >= lp.lpSum(x[i][d][j+1][a] for a in range(num_job)) - lp.lpSum(x[i][d][j][a] for a in range(num_job))
    
    
    
    
    for d in range(num_days):
        #Constraint: have more than the min # of FP hrs per day
        prob += lp.lpSum(x[i][d][j][0] for j in range(num_segments) for i in range(num_employees)) >= min_daily_FP[d]
        
        # Constraint: Ensure at least a certain number of hours are worked for FP before the cutoff hour
        prob += lp.lpSum(x[i][d][j][0] for i in range(num_employees) for j in hours_before_cutoff) >= min_morning_FP[d]
                         
        for j in range(num_segments):
            # Constraint: Ensure more than the specified number of people are working BM each hour

            prob += lp.lpSum(x[i][d][j][1] for i in range(num_employees)) >=  hourly_requirements_BM[days_considering [d]][j]
    
    
    
    
    #Constraint: be above the min weekly FP hours
    prob += lp.lpSum(x[i][d][j][0] for i in range(num_employees) for j in range(num_segments) for d in range(num_days)) >= min_weekly_FP
                   
    # Constraint: total hours worked over the days must be under the total labor hour limit
    prob += lp.lpSum(x[i][d][j][a] for i in range(num_employees) for d in range(num_days) for j in range(num_segments) for a in range(num_job)) <=  total_labor_hour_limit * (60/segment_minutes)
    
    
    
    # Constraint: Force people in the "force_shift" to be a part of said shift for a specific job type 'a'
    for employee, shifts in force_shift.items():
        i = employee_names.index(employee)
        for day, details in shifts.items():
            d = days_considering.index(day)
            segments = details["segments"]
            job_type = details["job_type"]
            for j, forced in enumerate(segments):
                if forced == 1:
                    prob += x[i][d][j][job_type] == 1  # Force employee to work job type 'a' during specified segments
    
    
    
    # Set a time limit in seconds 
    time_limit_seconds = sheets_time_limit
    
    # Solve the LP problem with CBC and a time limit
    status = prob.solve(lp.PULP_CBC_CMD(timeLimit=time_limit_seconds))
    
    
    
    
    # Output results
    print("Status:", lp.LpStatus[prob.status])
    

    
    
    def prepare_schedule_data(employee_names, days_considering, num_employees, num_days, num_segments, num_job , segment_minutes, y, x, f, employee_pref):
        data = []
        headers = ["Employee", "Day", "Start Time", "Job Type", "Total Hours"]
        data.append(headers)
        start_hour_index =6
        total_team_hours = 0
        day_off_count = 0
    
        for i in range(num_employees):
            total_weekly_hours = 0
            for d in range(num_days):
                total_day_hours = 0
                if lp.value(y[i][d]) == 1:
                    for j in range(num_segments):
                        for a in range(num_job):
                            if lp.value(x[i][d][j][a]) == 1:
                                total_day_hours += 1
                                total_weekly_hours += 1
                                total_team_hours += 1
                            
                                job_type = "FP" if a == 0 else "BM" if a == 1 else "Unknown"
                                hour = int(start_hour_index + (j * segment_minutes) // 60)
                                minute = int((j * segment_minutes) % 60)
                                time_str = f"{hour:02d}:{minute:02d}"
                                data.append([employee_names[i], days_considering[d], time_str, job_type, total_day_hours / (60/segment_minutes)])
                else:
                    data.append([employee_names[i], days_considering[d], "Off", "", 0])
            
            total_weekly_hours = total_weekly_hours / (60/segment_minutes)
            data.append([employee_names[i], "Total Hours for the week", "", "", total_weekly_hours])
    
        total_team_hours = total_team_hours / (60/segment_minutes)
        summary = [
            ["Total team hours this week", total_team_hours],
            ["Total number of people who had day off and were available", day_off_count]
        ]
        data.extend(summary)
        return data
        
    def save_data_to_json(data, filename):
        """
        Save data to a JSON file. If the file exists, it will be overwritten.
        If the file does not exist, a new one will be created.
    
        Args:
            data (dict): The data to be saved.
            filename (str): The name of the file where data will be saved.
        """
        # Get the absolute path of the file
        abs_path = os.path.abspath(filename)
        
        try:
            with open(abs_path, 'w') as f:
                json.dump(data, f, indent=4)
            print(f"Data successfully saved to {abs_path}")
        except Exception as e:
            print(f"An error occurred while saving data to {abs_path}: {e}")
                
    def scheduler_run():
        # Assuming you have the required arguments already defined here
        data = prepare_schedule_data(
            employee_names, days_considering, num_employees, num_days, 
            num_segments, num_job, segment_minutes, y, x, f, employee_pref
        )
        save_data_to_json(data, 'schedule_data.json')
    
        return lp.LpStatus[prob.status]


    scheduler_run()

