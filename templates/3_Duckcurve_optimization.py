

from __future__ import division
import matplotlib.pyplot as plt
import matplotlib
import pandas
import pdb, traceback, sys
import scipy
from scipy import signal
import numpy as np
import datetime
import cPickle as pickle
from pyomo.opt import SolverFactory
from pyomo.environ import *
from pyomo.opt import SolverStatus, TerminationCondition

# Imports useful for graphics
import matplotlib.pyplot as plt
import seaborn
seaborn.set_style("whitegrid")
seaborn.despine()
# get_ipython().magic(u'matplotlib inline')
# get_ipython().magic(u"config InlineBackend.figure_formats = {'svg',}")

# Give you access to all the V2G-Sim modules
import h2vgi



# Create a project that will hold other objects such as vehicles, locations
# car models, charging stations and some results. (see model.Project class)
project = h2vgi.model.Project()

# Use the itinerary module to import itineraries from an Excel file.
# Instantiate a project with the necessary information to run a simulation.
# Default values are assumed for the vehicle to model
# and the charging infrastructures to simulate.
project = h2vgi.itinerary.from_excel(project, '../data/NHTS/Tennessee.xlsx')
nb_of_days =30  # <<<<<<<<<<<<<<<<<<<<
project = h2vgi.itinerary.copy_append(project, nb_of_days_to_add=nb_of_days)

for vehicle in project.vehicles:
    vehicle.result_function = h2vgi.result.save_vehicle_power_demand

# Launch the simulation and save the results
h2vgi.core.run(project, date_from=project.date, date_to=project.date +  datetime.timedelta(days=nb_of_days))


# # total cumsumption
total_consumption = project.locations[0].result
for location in project.locations[1:]:
    total_consumption += location.result

total_consumption.to_csv('totalconsumption_Tennessee.csv')

# # read energy consumption data
# total_consumption = pandas.read_excel('../data/totalconsumption.xlsx')
#
# vehicle_number=2094
# real_number_FCEV = 800000
#
# nb_of_days = 30
# timestep = 60
# # labels = range(0, nb_of_days+1)
# # plt.figure(figsize=(12, 5), dpi=60)
# # plt.plot(total_consumption.power_demand.cumsum() * timestep * real_number_FCEV/vehicle_number)
# # plt.xticks(np.arange(0, 3600/timestep *nb_of_days * 24 + 1, 3600/timestep*24), labels, fontsize = 12)
# # plt.yticks(fontsize = 12)
# # #plt.title('Hydrogen consumption at the pump for ' + str(len(project.vehicles)) + ' vehicles')
# # plt.title('Hydrogen consumption at the pump for ' +str(real_number_FCEV) + ' vehicles',fontsize=14)
# # plt.ylabel('Total H2 consumption [kg]',fontsize=14)
# # plt.xlabel('Time (Day)',fontsize=14)
# # plt.show()
#
#
#
#
# # Select a time frame for the simulation
# number_of_days = 1  # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
# off_set_day = 28 # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
# cap_factor = 1
# times = range(0, number_of_days * 24 * 12)
# #e_consumption = 60.2889626913    #kwh/kg
# e_consumption = 67.3
#
#
#
# # Select consumption
# temp_start = total_consumption.index[0] + datetime.timedelta(days=off_set_day)
# temp_end = temp_start + datetime.timedelta(days=number_of_days, minutes=-5)
# temp = pandas.DataFrame(total_consumption.power_demand.ix[temp_start:temp_end].cumsum() * timestep / 2)
# temp = temp.resample('5T',how='first')
# temp['index'] = times
# temp = temp.set_index(['index'])
#
# #get the last value of temp as efinal
# efinal = temp.iloc[-1,-1]*real_number_FCEV/vehicle_number
# # print efinal
# # print(efinal*e_consumption/24/cap_factor)
# cumulative_profile = total_consumption.power_demand.ix[temp_start:temp_end].cumsum() * timestep *real_number_FCEV/vehicle_number/2
# cumulative_profile = cumulative_profile.resample('5T')
# cumulative_profile.to_csv('cumulativeprofile.csv')
# # plt.plot(demand_profile)
# # #plt.title('Hydrogen consumption at the pump for ' +str(real_number_FCEV) + ' vehicles',fontsize=14)
# # plt.ylabel('H2 consumption rate',fontsize=14)
# # plt.xlabel('Time',fontsize=14)
# # plt.show()
#
# # plt.plot(cumulative_profile)
# # #plt.title('Hydrogen consumption at the pump for ' +str(real_number_FCEV) + ' vehicles',fontsize=14)
# # plt.ylabel('Cumulative H2 consumption [kg]',fontsize=14)
# # plt.xlabel('Time',fontsize=14)
# # plt.show()
# #print(efinal)
# # Prep constraints data
# pmax = efinal/24/12/number_of_days/cap_factor # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
# pmin = -efinal/24/12/number_of_days/cap_factor  # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
# #pmin = pmax * 0.1
#
# #print efinal/24/cap_factor*e_consumption
# pmin = pandas.DataFrame(index=times, data={'pmin': [pmin] * len(times)})
# pmax = pandas.DataFrame(index=times, data={'pmax': [pmax] * len(times)})  # [kg/h]
#
#
# # Create Vmin and Vmax
# minimum_tank = 0  # [kg]  # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
# maximum_tank = efinal  # [kg]  # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
# init_tank = 0.5 * maximum_tank # [kg]  # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
# vmin = temp * real_number_FCEV/vehicle_number + minimum_tank - init_tank      #<<<<<<<<<<<<<<
# vmax= temp * real_number_FCEV/vehicle_number + maximum_tank - init_tank       #<<<<<<<<<<<<<<<
#
# plt.plot(vmin * e_consumption, label='energy_lower_bound')
# plt.plot(vmax * e_consumption, label='energy_upper_bound')
# plt.xticks(range(0,number_of_days*12*24+1,12),range(0,number_of_days * 24 + 1))
# plt.xlabel('Time (hour)')
# plt.ylabel('Cumulative electricity consumption (kWh)')
# plt.title('Boundaries of cumulative fuel consumption')
# plt.legend()
# plt.show()
# #
# # plt.plot(pmin * e_consumption, label='power_lower_bound')
# # plt.plot(pmax * e_consumption, label='power_upper_bound')
# # plt.xticks(range(0,number_of_days*12*24+1,12),range(0,number_of_days * 24 + 1))
# # plt.xlabel('Time (hour)')
# # plt.ylabel('Power (kW)')
# # plt.legend()
# # plt.show()
#
#
# # prepare the netlad data for 2030 and 2050
# # Prep the price data
# # day = datetime.datetime(2016, 7, 11)  # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
# # loaddata2030 = pandas.read_excel('../data/netload/Net_load_California_2012-2016.xlsx')
# # start = datetime.datetime(2016, 1, 1)
# # end = datetime.datetime(2017, 1, 1)
# # i = pandas.date_range(start=start, end=end,
# #                       freq='60T', closed='left')
# #
# # loaddata2030 = loaddata2030.set_index(i)
# # loaddata2030 = loaddata2030.resample('5T')
# # temp_net_load = pandas.DataFrame(loaddata2030[day: day + datetime.timedelta(days=number_of_days,minutes=-5)]['netload'])
# # temp_net_load = temp_net_load.interpolate(method='spline', order=2)
#
# #Load the net load data
# finalResult = pandas.DataFrame()
# filename = '../data/netload/2025.pickle'
# with open(filename, 'rb') as fp:
#     temp_net_load = pickle.load(fp)
# day = datetime.datetime(2025, 7, 8)
# temp_net_load = pandas.DataFrame(temp_net_load[day: day + datetime.timedelta(days=number_of_days,minutes=-5)]['netload'])
#
# temp_index = pandas.DataFrame(range(0, len(temp_net_load)), columns=['index'])
# net_load = temp_net_load.copy()
# net_load = net_load.set_index(temp_index['index'])
# #net_load = net_load.resample('5T', how='first')
# # scale_up = e_consumption * 200000/len(project.vehicles)
# net_load = net_load *1000 / e_consumption /12  #in kg
# final_net_load = net_load * e_consumption * 12
# #print net_load
# # Launch optimization
# with SolverFactory('gurobi') as opt:
#     model = ConcreteModel()
#
#     # Set
#     model.t = Set(initialize=times, doc='Time', ordered=True)
#     last_t = model.t.last()
#
#     # Parameters
#                 # Net load
#     model.d = Param(model.t, initialize = net_load.to_dict()['netload'], doc='Net load')
#     model.p_max = Param(model.t, initialize=pmax.to_dict()['pmax'], doc='P max')
#     model.p_min = Param(model.t, initialize=pmin.to_dict()['pmin'], doc='P min')
#     model.v_min = Param(model.t, initialize=vmin.to_dict()['power_demand'], doc='E min')
#     model.v_max = Param(model.t, initialize=vmax.to_dict()['power_demand'], doc='E max')
#
#     # Variables
#     model.p = Var(model.t, domain=Reals, doc='electricity to hydrogen')
#
#     # Rules
#     def maximum_power_rule(model, t):
#         return model.p[t] <= model.p_max[t]
#     model.power_max_rule = Constraint(model.t, rule=maximum_power_rule, doc='P max rule')
#
#     def minimum_power_rule(model, t):
#         return model.p[t] >= model.p_min[t]
#     model.power_min_rule = Constraint(model.t, rule=minimum_power_rule, doc='P min rule')
#
#     # def minimum_energy_rule(model, t):
#     #     return sum(model.p[i] for i in range(0, t + 1)) >= model.v_min[t]
#     # model.minimum_energy_rule = Constraint(model.t, rule=minimum_energy_rule, doc='E min rule')
#     #
#     # def maximum_energy_rule(model, t):
#     #     return sum(model.p[i] for i in range(0, t + 1)) <= model.v_max[t]
#     # model.maximum_energy_rule = Constraint(model.t, rule=maximum_energy_rule, doc='E max rule')
#     #
#     # def final_energy_balance(model):
#     #     return sum(model.p[i] for i in model.t)  >=  efinal
#     # model.final_energy_rule = Constraint()
#
#     model.final = Constraint(expr=sum(model.p[i] for i in model.t) == efinal)
#
#
#     def objective_rule(model):
#         return sum([(model.d[t] + model.p[t])**2 for t in model.t])
#     model.objective = Objective(rule=objective_rule, sense=minimize, doc='Define objective function')
#
#     # def objective_rule(model):
#     #     return sum([(model.d[t + 1] - model.d[t] + model.p[t+1]-model.p[t])**2 for t in model.t if t != last_t])
#     # model.objective = Objective(rule=objective_rule, sense=minimize, doc='Define objective function')
#
#     results = opt.solve(model)
#
#     #print value(model.objective)
#     model.load(results) # Loading solution into results object
#
#     if (results.solver.status == SolverStatus.ok) and (results.solver.termination_condition == TerminationCondition.optimal):
#         print 'Got the optimal solution!'
#     elif (results.solver.termination_condition == TerminationCondition.infeasible):
#                 print 'No infeasible solution!'
#     else:
#                 # Something else is wrong
#         print ('Solver Status:', results.solver.status)
#
#
#
#
# df = pandas.DataFrame(index=['station'], data=model.p.get_values()).transpose()
#
# #print df
# hydrogeproduction = df
#
# result_kg = df.copy()
# result_tank = hydrogeproduction.cumsum()
# df = df * e_consumption * 12 # [kWh/kg]
# temp_station = df # [kW]
# #temp_station = temp_station.rename(columns={0: 'station'})
# temp_station['index'] = range(0, len(temp_station))
# temp_station = temp_station.set_index(['index'], drop=True)
#
# result_tank.to_csv('cumulativeproduction.csv')
# # plt.plot(result_tank)
# # plt.ylabel('Cumulative hydrogen production')
# # plt.xlabel('Time')
# # plt.show()
# #
# # plt.plot(hydrogeproduction)
# # plt.ylabel('hydrogen production rate')
# # plt.xlabel('Time')
# # plt.show()
#
# temp_netload = final_net_load.copy()
# temp_netload = temp_netload.head(len(temp_station))
# tempIndex = temp_netload.index
# temp_netload['index'] = range(0, len(temp_station))
# temp_netload = temp_netload.set_index(['index'], drop=True)
#
# temp_result = pandas.DataFrame(temp_netload['netload'] + temp_station['station'])
# #temp_result = temp_netload.add(temp_station,fill_value=0)
# temp_result = temp_result.rename(columns={0: 'netload'})
# temp_result = temp_result.set_index(tempIndex)
# temp_netload = temp_netload.set_index(tempIndex)
# temp_station = temp_station.set_index(tempIndex)
#
# delta = efinal/24*e_consumption
#
# print delta
#
# temp_netload_FCEV = final_net_load.copy() + delta
# temp_netload_FCEV = temp_netload_FCEV.head(len(temp_station))
# tempIndex = temp_netload_FCEV.index
# temp_netload_FCEV['index'] = range(0, len(temp_station))
# temp_netload_FCEV = temp_netload_FCEV.set_index(['index'], drop=True)
#
# # print the peak and valley
#
# # print temp_netload.loc[temp_netload['netload'].idxmax()] / 1000
# # print temp_result.loc[temp_result['netload'].idxmax()] / 1000
# # print temp_netload_FCEV.loc[temp_netload_FCEV['netload'].idxmax()] / 1000
# #
# # print temp_netload.loc[temp_netload['netload'].idxmin()] / 1000
# # print temp_result.loc[temp_result['netload'].idxmin()] / 1000
# # print temp_netload_FCEV.loc[temp_netload_FCEV['netload'].idxmin()] / 1000
#
# #print temp_result['netload']-temp_netload['netload']
# #Save ramp data
# ramp_netload = np.diff(temp_result['netload'])
# ramp_netload = np.append(ramp_netload,0)
# temp_result['ramp'] = ramp_netload
#
# ramp_netload = np.diff(temp_netload['netload'])
# ramp_netload = np.append(ramp_netload,0)
# temp_netload['ramp'] = ramp_netload
#
# ramp_netload_FCEV = np.diff(temp_netload_FCEV['netload'])
# ramp_netload_FCEV = np.append(ramp_netload_FCEV,0)
# temp_netload_FCEV['ramp'] = ramp_netload_FCEV
# #
# # # # find the maximum ramp up
# # print temp_netload['ramp'].idxmax()
# # print temp_result['ramp'].idxmax()
# # print temp_netload.loc[temp_netload['ramp'].idxmax()] / 1000 * 12
# # print temp_result.loc[temp_result['ramp'].idxmax()] / 1000 * 12
# # print temp_netload_FCEV.loc[temp_netload_FCEV['ramp'].idxmax()] / 1000 * 12
#
# #
# # # find the maximum ramp down
# # # find the maximum ramp
# # print temp_netload['ramp'].idxmin()
# # print temp_result['ramp'].idxmin()
# # print temp_netload.loc[temp_netload['ramp'].idxmin()] / 1000 * 12
# # print temp_result.loc[temp_result['ramp'].idxmin()] / 1000 * 12
# # print temp_netload_FCEV.loc[temp_netload_FCEV['ramp'].idxmin()] / 1000 * 12
# #
# # # temp_netload['ramp'].to_csv('netload_ramp.csv')
# # #temp_result['ramp'].to_csv('netload+FC0.8EV0.8mv2g_ramp.csv')
# #
# # #####plot ramp
# # plt.plot(temp_netload['ramp']/1000*12, label='Netload without FCEV')
# # plt.plot(temp_result['ramp']/1000*12, label='Netload + FCEV')
# # plt.xticks(range(0,number_of_days*12*24+1,12),range(0,number_of_days *24 + 1),fontsize = 12)
# # plt.yticks(fontsize = 12)
# # plt.ylabel('Ramp Rate (MW/h)',fontsize = 14)
# # plt.xlabel('Time (hour)',fontsize = 14)
# # plt.legend(loc = 'best',fontsize = 14)
# # plt.show()
# #
# # temp_netload['netload'].to_csv('netload.csv')
# # temp_netload_FCEV['netload'].to_csv('uncontrolledload.csv')
# #temp_result['netload'].to_csv('netload+controlledload.csv')
#
#
# # plt.plot(temp_netload['netload']/1000, label='Netload without FCEV')
# # plt.plot(temp_result['netload']/1000, label='Netload + controlled FCEV')
# # plt.plot(temp_netload_FCEV['netload']/1000, label='Netload + uncontrolled FCEV')
# # plt.xticks(range(0,number_of_days*12*24+1,12),range(0,number_of_days *24 + 1),fontsize = 12)
# # plt.yticks(fontsize = 12)
# # plt.ylabel('Load Profile (MW)',fontsize = 14)
# # plt.xlabel('Time (hour)',fontsize = 14)
# # plt.legend(loc = 'best',fontsize = 14)
# # plt.show()






