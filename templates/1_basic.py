from __future__ import division
import matplotlib.pyplot as plt
import pdb
import datetime

# Give you access to all the V2G-Sim modules
import h2vgi

# Create a project that will hold other objects such as vehicles, locations
# car models, charging stations and some results. (see model.Project class)
project = h2vgi.model.Project()

# Use the itinerary module to import itineraries from an Excel file.
# Instantiate a project with the necessary information to run a simulation.
# Default values are assumed for the vehicle to model
# and the charging infrastructures to simulate.
project = h2vgi.itinerary.from_excel(project, '../data/NHTS/Connecticut.xlsx')

for vehicle in project.vehicles:
    vehicle.result_function = h2vgi.result.save_vehicle_power_demand

# Get speed profiles and terrain profiles
#h2vgi.driving.drivecycle.generator.assign_EPA_cycle(project)
nb_of_days =5
project = h2vgi.itinerary.copy_append(project,nb_of_days_to_add=nb_of_days)
#print project.date
# Launch the simulation and save the results
h2vgi.core.run(project, date_from=project.date - datetime.timedelta(days=1), date_to=project.date +  datetime.timedelta(days=nb_of_days-1))


# Stop the script at the end, and let you explore the project structure.
# Perhaps you can checkout "project.vehicles[0]"
# print('Press c and then enter to quit debugger')
# pdb.set_trace()
