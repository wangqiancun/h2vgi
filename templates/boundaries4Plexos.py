from __future__ import division
import matplotlib.pyplot as plt
import pandas
import pdb, traceback, sys
import scipy
from scipy import signal
import numpy as np
import datetime
# from pyomo.opt import SolverFactory
# from pyomo.environ import *

# Imports useful for graphics
import matplotlib.pyplot as plt
import seaborn
seaborn.set_style("whitegrid")
seaborn.despine()
# %matplotlib inline
# %config InlineBackend.figure_formats = {'svg',}

# Give you access to all the V2G-Sim modules
# import h2vgi
#
# project = h2vgi.model.Project()
#
# # Use the itinerary module to import itineraries from an Excel file.
# # Instantiate a project with the necessary information to run a simulation.
# # Default values are assumed for the vehicle to model
# # and the charging infrastructures to simulate.
# project = h2vgi.itinerary.from_excel(project, '../data/NHTS/Tennessee_100.xlsx') # <<<<<<<<<<<<<<
# nb_of_days = 10 #<<<<<<<
# project = h2vgi.itinerary.copy_append(project, nb_of_days_to_add=nb_of_days)
#
# for vehicle in project.vehicles:
#     vehicle.result_function = h2vgi.result.save_vehicle_power_demand
#
# # Launch the simulation and save the results
# h2vgi.core.run(project, date_from=project.date, date_to=project.date +  datetime.timedelta(days=nb_of_days))
#
# # total cumsumption
# total_consumption = project.locations[0].result
# for location in project.locations[1:]:
#     total_consumption += location.result

total_consumption = pandas.read_excel('../data/totalconsumption.xlsx')

# plt.figure(figsize=(12, 5), dpi=60)
# plt.plot(total_consumption.power_demand.cumsum() * 60)
# #plt.title('Hydrogen consumption at the pump for ' + str(len(project.vehicles)) + ' vehicles')
# plt.ylabel('Total consumption [kg]')
# plt.xlabel('Time')
# plt.show()
timestep = 5 # minutes <<<<<<<<<<<<
number_of_days = 1  # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
off_set_day = 20  # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
times = range(0, number_of_days * 24 * 12)
CF = 0.8  # capacity factor <<<<<<<<<<<<<<

# Select consumption
temp_start = total_consumption.index[0] + datetime.timedelta(days=off_set_day)
temp_end = temp_start + datetime.timedelta(days=number_of_days, minutes=-5)
temp = pandas.DataFrame(total_consumption.power_demand.ix[temp_start:temp_end].cumsum() * 60)
temp = temp.resample('5T',how='first')
temp['index'] = times
temp = temp.set_index(['index'])

efinal = temp.iloc[-1,-1]

# Prep constraints data
pmin = 0  # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
pmax = efinal / (24 * 60 / timestep) / CF # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
pmax_temp = pmax
pmin = pandas.DataFrame(index=times, data={'pmin': [pmin] * len(times)})
pmax = pandas.DataFrame(index=times, data={'pmax': [pmax] * len(times)})  # [kg/h]

# Find time t_stop where the electrolyzer stops production
t_stop = round(efinal / pmax_temp, 0)
print t_stop
#creat vmax
vmax1 = np.linspace(0.0, efinal, num=t_stop, endpoint=False)   # produce h2 at the maximum rate from the beginning
vmax2 = np.ones(len(times)-t_stop) * efinal      # after meeting the h2 demand, the electrolyzer will halt.
vmax = np.append(vmax1,vmax2)             # combine them together

vmin = temp


plt.plot(vmin,label='lowerbound')
plt.plot(vmax,label='upperbound')
plt.ylabel('cumulative production [kg]')
plt.xlabel('Time')
plt.show()