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

# Define the battery
Capacity = 5838000/1 # [kWh]  # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
init_SOC = 0.5 # [kg]  # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
P_max = 3583278/1   # [kW] <<<<<<<<<<<<<<

#Load the net load data
number_of_days = 1
finalResult = pandas.DataFrame()
filename = '../data/netload/2025.pickle'
with open(filename, 'rb') as fp:
    temp_net_load = pickle.load(fp)
day = datetime.datetime(2025, 3, 15)
temp_net_load = pandas.DataFrame(temp_net_load[day: day + datetime.timedelta(days=number_of_days,minutes=-5)]['netload'])

temp_index = pandas.DataFrame(range(0, len(temp_net_load)), columns=['index'])
net_load = temp_net_load.copy()
net_load = net_load.set_index(temp_index['index'])

net_load = net_load *1000 + 2041754.751014  #in kW  new netload should plus the fuel cell ev demand

# Launch optimization
with SolverFactory('gurobi') as opt:
    model = ConcreteModel()

    # Set
    model.t = Set(initialize=range(0, 24 * 12), doc='Time', ordered=True)
    last_t = model.t.last()

    # Parameters
    # Net load
    model.d = Param(model.t, initialize = net_load.to_dict()['netload'], doc='Net load')
    model.p_max = Param(initialize=P_max, doc='P max')
    model.p_min = Param(initialize=-P_max, doc='P min')
    model.v_min = Param(initialize=0, doc='E min')
    model.v_max = Param(initialize=Capacity, doc='E max')

    # Variables
    model.p = Var(model.t, domain=Reals, doc='Battery operation results')

    # Rules
    def maximum_power_rule(model, t):
        return model.p[t] <= model.p_max
    model.power_max_rule = Constraint(model.t, rule=maximum_power_rule, doc='P max rule')

    def minimum_power_rule(model, t):
        return model.p[t] >= model.p_min
    model.power_min_rule = Constraint(model.t, rule=minimum_power_rule, doc='P min rule')

    def minimum_energy_rule(model, t):
        return init_SOC * Capacity + sum(model.p[i]/12 for i in range(0, t + 1)) >= model.v_min
    model.minimum_energy_rule = Constraint(model.t, rule=minimum_energy_rule, doc='E min rule')

    def maximum_energy_rule(model, t):
        return init_SOC * Capacity + sum(model.p[i]/12 for i in range(0, t + 1)) <= model.v_max
    model.maximum_energy_rule = Constraint(model.t, rule=maximum_energy_rule, doc='E max rule')


    model.final = Constraint(expr=sum(model.p[i] for i in model.t) == 0)


    # def objective_rule(model):
    #     return sum([(model.d[t] + model.p[t])**2 for t in model.t])
    # model.objective = Objective(rule=objective_rule, sense=minimize, doc='Define objective function')

    def objective_rule(model):
        return sum([(model.d[t + 1] - model.d[t] + model.p[t+1]-model.p[t])**2 for t in model.t if t != last_t])
    model.objective = Objective(rule=objective_rule, sense=minimize, doc='Define objective function')

    results = opt.solve(model)

    print value(model.objective)
    model.load(results) # Loading solution into results object

    if (results.solver.status == SolverStatus.ok) and (results.solver.termination_condition == TerminationCondition.optimal):
        print 'Got the optimal solution!'
    elif (results.solver.termination_condition == TerminationCondition.infeasible):
                print 'No infeasible solution!'
    else:
                # Something else is wrong
        print ('Solver Status:', results.solver.status)



df = pandas.DataFrame(index=['battery'], data=model.p.get_values()).transpose()

# print df
#df.to_csv('p.csv')

temp_station = df # [kW]
#temp_station = temp_station.rename(columns={0: 'station'})
temp_station['index'] = range(0, len(temp_station))
temp_station = temp_station.set_index(['index'], drop=True)

# plt.plot(temp_station['station'] * len(project.vehicles), label='station')
# plt.title('station powerload')
# plt.ylabel('Total power')
# plt.xlabel('Time')
# plt.show()

temp_netload = net_load.copy()
temp_netload = temp_netload.head(len(temp_station))
tempIndex = temp_netload.index
temp_netload['index'] = range(0, len(temp_station))
temp_netload = temp_netload.set_index(['index'], drop=True)

temp_result = pandas.DataFrame(temp_netload['netload'] + temp_station['battery'])
#temp_result = temp_netload.add(temp_station,fill_value=0)
temp_result = temp_result.rename(columns={0: 'netload'})
temp_result = temp_result.set_index(tempIndex)
temp_netload = temp_netload.set_index(tempIndex)
temp_station = temp_station.set_index(tempIndex)



# print the peak and valley

# print temp_netload.loc[temp_netload['netload'].idxmax()] / 1000
# print temp_result.loc[temp_result['netload'].idxmax()] / 1000
#
# print temp_netload.loc[temp_netload['netload'].idxmin()] / 1000
# print temp_result.loc[temp_result['netload'].idxmin()] / 1000

#plt.plot(temp_result['netload']-temp_netload['netload'])

#print temp_result['netload']-temp_netload['netload']
#Save ramp data
ramp_netload = np.diff(temp_result['netload'])
ramp_netload = np.append(ramp_netload,0)
temp_result['ramp'] = ramp_netload

ramp_netload = np.diff(temp_netload['netload'])
ramp_netload = np.append(ramp_netload,0)
temp_netload['ramp'] = ramp_netload

#
# # # find the maximum ramp up
# print temp_netload['ramp'].idxmax()
# print temp_result['ramp'].idxmax()
print temp_netload.loc[temp_netload['ramp'].idxmax()] / 1000 * 12
print temp_result.loc[temp_result['ramp'].idxmax()] / 1000 * 12

#
# # find the maximum ramp down
# # find the maximum ramp
# print temp_netload['ramp'].idxmin()
# print temp_result['ramp'].idxmin()
print temp_netload.loc[temp_netload['ramp'].idxmin()] / 1000 * 12
print temp_result.loc[temp_result['ramp'].idxmin()] / 1000 * 12

plt.plot(temp_netload['netload']/1000, label='Netload + uncontrolled FCEV')
plt.plot(temp_result['netload']/1000, label='Netload + stationary battery')
plt.xticks(range(0,number_of_days*12*24+1,12),range(0,number_of_days *24 + 1),fontsize = 12)
plt.yticks(fontsize = 12)
plt.ylabel('Load Profile (MW)',fontsize = 14)
plt.xlabel('Time (hour)',fontsize = 14)
plt.legend(loc = 'best',fontsize = 14)
plt.show()
# plt.show()