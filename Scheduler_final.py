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
from math import floor

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
    earliest_shift_end_hrs =data["earliest_shift_end"]
    latest_shift_start_hrs= data["latest_shift_start"]
    earliest_latest_flag = data["earliest_latest_flag"]
    max_daily_O_hrs = data["max_daily_O_hrs"]
    FP_latest_hr = data["FP_latest_hr"]
    latest_FP_flag= data["latest_FP_flag"]
    emp_num_shifts = data["emp_num_shifts"]
    start_shift_ranges = data["start_shift_ranges"]
    shift_lengths = data["shift_lengths"]
    
    
    
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

    

    
    end_hour_backend =22
    start_hour_backend = 6
    
    num_hours = end_hour_backend - start_hour_backend   # Number of hours in the specified range
    segment_minutes =15
    num_segments = int(((num_hours) * (60 / segment_minutes)))  # Number of 15-minute segments. 
    end_hour_backend_segs = int (end_hour_backend * (60 / segment_minutes))
    
    #change ealiest and latest shift star/end to 15-min segments
    earliest_shift_end = int((earliest_shift_end_hrs- start_hour_backend)  * (60 / segment_minutes))
    latest_shift_start= int((latest_shift_start_hrs- start_hour_backend)  * (60 / segment_minutes))
    
    #segment the shift lengths
    def convert_shift_lengths_to_segments(shift_lengths, segment_minutes):
        shift_lengths_segs = {}
        factor = 60 / segment_minutes
    
        for employee, days in shift_lengths.items():
            shift_lengths_segs[employee] = {}
            for day, length in days.items():
                shift_lengths_segs[employee][day] = int(length * factor)
    
        return shift_lengths_segs
    shift_lengths_segs = convert_shift_lengths_to_segments(shift_lengths, segment_minutes)

    


    # Create min_morning_FP by multiplying each element in min_morning_FP_hrs by (60 / segment_minutes)
    min_morning_FP = [hours * (60 / segment_minutes) for hours in min_morning_FP_hrs]
    
    #change the start range listing into proper segments
    start_shift_ranges_segs = {
        employee: [
            int((start_time - start_hour_backend) * (60 // segment_minutes)),
           int(1+ (end_time - start_hour_backend) * (60 // segment_minutes))
        ]
        for employee, (start_time, end_time) in start_shift_ranges.items()
        }



    
    
    #change FP latest hr to the 15 min segment on the j range. must subtract from start hr backend
    FP_latest = int((FP_latest_hr- start_hour_backend)  * (60 / segment_minutes))

    #change Hrs until break into 15 min segments 
    segs_until_break = int( hrs_until_break * (60 / segment_minutes))
    
    num_days = len(days_considering)  

    num_job = len(job_type) + 1 # add one to include job types as they are not grabbed from the google sheet
    
    # min max shift hours
    min_shift_len = min_shift_len_hrs *(60/segment_minutes)
    max_shift_len = max_shift_len_hrs *(60/segment_minutes)
    
    # Calculate min_daily_FP_hrs by multiplying min_daily_FP by (60 / segment_minutes)
    min_daily_FP = [hours * (60 / segment_minutes) for hours in min_daily_FP_hrs]
    min_weekly_FP = min_weekly_FP_hrs * (60 / segment_minutes)
    
    #calculate min daily oven hours into segments 
    max_daily_O = [int(hours * (60 / segment_minutes)) for hours in max_daily_O_hrs]
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
    
    #bk[i][d] is 1 if someone is granted a break for that day. Only granted if shift len > hrs until break
    bk = [[lp.LpVariable(f"bk_{i}_{d}", cat=lp.LpBinary) for d in range(num_days)] for i in range(num_employees)]
    
    floor_segments = [[lp.LpVariable(f"floor_segments_{i}_{d}", cat=lp.LpInteger) for d in range(num_days)] for i in range(num_employees)]
    
    

    # Objective function: minimize the hours worked
    prob += lp.lpSum(x[i][d][j][a] for i in range(num_employees) for d in range(num_days) for j in range(num_segments) for a in range(num_job))
    

    
    
    #Constraints:
    for i in range(num_employees):
        # Constraint: total hours worked over the days must be under the maximum allowed hours per employee
        prob += lp.lpSum(x[i][d][j][a] for d in range(num_days) for j in range(num_segments) for a in range(num_job)) <=  allocated_max_hours [employee_names[i]] *(int (60/segment_minutes))
        prob += lp.lpSum(x[i][d][j][a] for d in range(num_days) for j in range(num_segments) for a in range(num_job)) >=  allocated_min_hours [employee_names[i]] *(int(60/segment_minutes))
        for d in range(num_days):
            #Constraint: Min & Max hours per emploee per day or none hours at all
            prob += lp.lpSum(x[i][d][j][a] for j in range(num_segments) for a in range(num_job)) >= min_shift_len * y[i][d]  # Minimum hours if y[i][d] == 1
            prob += lp.lpSum(x[i][d][j][a] for j in range(num_segments) for a in range(num_job)) <= max_shift_len * y[i][d]  # Maximum hours if y[i][d] == 1
            
            # ensure starting shift properly accounted for for edge effects
            prob += f[i][d][0] == lp.lpSum(x[i][d][0][a] for a in range(num_job))
            
            # Constraint to calculate the number of segments worked
            prob += floor_segments[i][d] == lp.lpSum(x[i][d][j][a] for j in range(num_segments) for a in range(num_job - 1))  # Exclude breaks
            
            # Constraint: Allocate breaks only if segments worked > 24
            prob += floor_segments[i][d] >= 25 * bk[i][d]
            prob += floor_segments[i][d] <= 25 * bk[i][d] + 24  # Ensure break only if segments are > 24
            
            # Constraint: Ensure exactly 2 break segments if bk[i][d] == 1
            prob += lp.lpSum(x[i][d][j][num_job-1] for j in range(num_segments)) == 2 * bk[i][d]
    
            for j in range(num_segments - 1):
                # Sum over all job types to check if there's a transition from 0 to 1 in total working hours
                prob += f[i][d][j+1] >= lp.lpSum(x[i][d][j+1][a] for a in range(num_job)) - lp.lpSum(x[i][d][j][a] for a in range(num_job))
            
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
                # DO not consider ppl for ovens if they are not available to do it
                if ability[employee_names[i]]["O"] == 0:
                    prob += x[i][d][j][2] == 0
                
                #Constraint: emp can only work during available hours
                if availability[employee_names[i]][days_considering[d]][j] == 0:  
                    for a in range(num_job):
                        prob += x[i][d][j][a] == 0
            #Constraint to make sure that food preps are not working past a certain time at Allen most specifically 
            if latest_FP_flag =="TRUE":
                if ability[employee_names[i]]["BM"] ==0: #only constrain the people whos are soly Food preps. For Allen this is only 2 specific people we dont want working late. AKA the good food prepers
                    for j in range(FP_latest, num_segments ):
                        for a in range(num_job-1):
                            prob += x[i][d][j][a] ==0
    

    # Constraint for forcing some people to only work a specified number of days
    for i in range(num_employees):
        employee_name = employee_names[i]  # Assuming you have a list of employee names
        if employee_name in emp_num_shifts:
            prob += lp.lpSum(y[i][d] for d in range(num_days)) == emp_num_shifts[employee_name]

    #COnstraint: make some people stat in a specified range
    for i in range(num_employees):
        employee_name = employee_names[i]
        for d in range(num_days):
            if employee_name in start_shift_ranges_segs:
                #so I am making it so that the start time will be within this range if they are working. if not working then y ==0 and this start time has to be 0 for the range
                prob += lp.lpSum(f[i][d][j] for j in range (start_shift_ranges_segs[employee_name][0], start_shift_ranges_segs[employee_name][1] )) == y[i][d]  
                # prob += lp.lpSum(x[i][d][j][a] for j in range(start_shift_ranges_segs[employee_name][0], start_shift_ranges_segs[employee_name][1]) for a in range(num_job)) >= y[i][d]




    if earliest_latest_flag == "TRUE":
        for i in range (num_employees):
                for d in range(num_days):
                    prob += lp.lpSum(x[i][d][j][a] for j in range(latest_shift_start, earliest_shift_end) for a in range(num_job)) >= y[i][d] * (earliest_shift_end - latest_shift_start)
       
                 
    
    for d in range(num_days):
        #Constraint: have more than the min # of FP hrs and O per day
        prob += lp.lpSum(x[i][d][j][0] for j in range(num_segments) for i in range(num_employees)) >= min_daily_FP[d]
        prob += lp.lpSum(x[i][d][j][2] for j in range(num_segments) for i in range(num_employees)) == max_daily_O[d]
        # Constraint: Ensure at least a certain number of hours are worked for FP before the cutoff hour
        prob += lp.lpSum(x[i][d][j][0] for i in range(num_employees) for j in hours_before_cutoff) >= min_morning_FP[d]
                         
        for j in range(num_segments):
            # Constraint: Ensure more than the specified number of people are working BM each hour
            prob += lp.lpSum(x[i][d][j][1] for i in range(num_employees)) >=  hourly_requirements_BM[days_considering [d]][j]
            #Constraint that only 1 person can be working at the Oven at a time
            prob +=lp.lpSum(x[i][d][j][2] for i in range(num_employees)) <= 1
        
    
    

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
            if job_type in [0, 1, 2]:  # This means they are forced to specifically be a BM, FP, or O
                for j, forced in enumerate(segments):
                    if forced == 1:
                        prob += x[i][d][j][job_type] == 1  # Force employee to work job type 'a' during specified segments
            elif job_type == 3:  # This means they can be either BM or FP
                for j, forced in enumerate(segments):
                    if forced == 1:
                        prob += lp.lpSum([x[i][d][j][a] for a in range(2)]) == 1  # Force employee to work either BM or FP


    # Constraint: Ensure total hours worked per day for each employee matches the shift_lengths_segs value
    for i in range(num_employees):
        employee_name = employee_names[i]
        if employee_name in shift_lengths_segs:
            for d in range(num_days):
                if days_considering[d] in shift_lengths_segs[employee_name]:
                    shift_length = shift_lengths_segs[employee_name][days_considering[d]]
                    prob += lp.lpSum(x[i][d][j][a] for j in range(num_segments) for a in range(num_job)) == shift_length
                    
        
    
    
    
    # Set a time limit in seconds 
    time_limit_seconds = sheets_time_limit
    
    # Solve the LP problem with CBC and a time limit
    status = prob.solve(lp.PULP_CBC_CMD(timeLimit=time_limit_seconds))
    
    
    
    
    # Output results
    print("Status:", lp.LpStatus[prob.status])
    return status, employee_names, days_considering, num_employees, num_days, num_segments, num_job, start_hour, segment_minutes, y, x, f, employee_pref
    

def get_lp_solver_outputs():
    return lp_solver()

    
    
def prepare_schedule_data(employee_names, days_considering, num_employees, num_days, num_segments, num_job, start_hour, segment_minutes, y, x, f, employee_pref):
    data = []
    headers = ["Employee", "Day", "Start Time", "Job Type", "Total Hours"]
    data.append(headers)

    total_team_hours = 0
    day_off_count = 0
    start_hour_index=6

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

                            job_type = "FP" if a == 0 else "BM" if a == 1 else "O" if a ==2 else "BK" if a == 3 else "Unknown"
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
    with open(filename, 'w') as f:
        json.dump(data, f)

def scheduler(status, employee_names, days_considering, num_employees, num_days, num_segments, num_job, start_hour, segment_minutes, y, x, f, employee_pref):
    if status != lp.LpStatusOptimal:
        print("Optimization did not find an optimal solution.")
        return

    data = prepare_schedule_data(
        employee_names, days_considering, num_employees, num_days, 
        num_segments, num_job, start_hour, segment_minutes, y, x, f, employee_pref
    )
    save_data_to_json(data, 'schedule_data.json')

def run_scheduler():
    status, employee_names, days_considering, num_employees, num_days, num_segments, num_job, start_hour, segment_minutes, y, x, f, employee_pref = get_lp_solver_outputs()
    scheduler(status, employee_names, days_considering, num_employees, num_days, num_segments, num_job, start_hour, segment_minutes, y, x, f, employee_pref)




