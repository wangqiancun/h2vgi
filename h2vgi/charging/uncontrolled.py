from __future__ import division
import random
import pandas


def consumption(activity, vehicle, nb_interval, timestep, charging_option):
    """Fuel cell vehicles do not refill

    Args:
        activity (Parked): Parked activity to get charging station capabilities
        vehicle (Vehicle): Vehicle object to get current hydrogen and physical
            constraints (maximum hydrogen, ...)
        nb_interval (int): number of timestep for the parked activity
        timestep (int): calculation timestep
        charging_option (any): not used

    Returns:
        hydrogen (list): state of charge
        power_demand (list): power demand
    """
    if nb_interval == 0:
        return [vehicle.hydrogen[-1]], [0]

    # Percentage of the tank
    level = vehicle.hydrogen[-1] / vehicle.car_model.tank_size
    if level < 0:
        level = 0.1

    # # Find out if I should refuel? level --> [0, 1] original settings
    # if level <= 0.1:
    #     probability = 1.0
    # elif level <= 0.5:
    #     probability = -2 * level + 1.0
    # else:
    #     probability = -1.0


    # Find out if I should refuel? level --> [0, 1] new settings based on nrel data
    if level <= 0.08:
        probability = 1.0
    elif 0.08 < level <= 0.16:
        probability = -0.70625 * level + 1.056
    elif 0.16 < level <= 0.25:
        probability = -1.6711 * level + 1.2108
    elif 0.25 < level <= 0.33:
        probability = -2.70125 * level + 1.4684125
    elif 0.33 < level <= 0.41:
        probability = -2.41 * level + 1.3723
    elif 0.41 < level <= 0.50:
        probability = -1.6088 * level + 1.0438
    elif 0.5 < level <= 0.58:
        probability = -1.26 * level + 0.8694
    elif 0.58 < level <= 0.66:
        probability = -0.8275 * level + 0.61855
    elif 0.66 < level <= 0.75:
        probability = -0.42 * level + 0.3496
    elif 0.75 < level <= 0.83:
        probability = -0.29 * level + 0.2521
    else:
        probability = -1.0

    refuel = random.random() <= probability

    # Refuel function
    if refuel:
        #print activity.start
        #print level
        # Check if activity faster than 10 minutes
        if nb_interval * timestep <= 10 * 60:
            # Refuel at a faster rate to reach full tank <-- need to change but fine for now
            power_demand = [(0.8-level)  * vehicle.car_model.tank_size / (nb_interval * timestep)] * nb_interval
        else:
            # Refuel for 10min and then do nothing
            interval_10min = int((10 * 60) / timestep)
            power_demand = [(1-level) * vehicle.car_model.tank_size / (interval_10min * timestep)] * interval_10min
            missing_interval = nb_interval - interval_10min
            power_demand.extend([0] * missing_interval)
        hydrogen = [vehicle.car_model.tank_size] * nb_interval


    # Do not refuel
    else:
        hydrogen = [vehicle.hydrogen[-1]] * nb_interval
        power_demand = [0] * nb_interval



    return  hydrogen, power_demand  # [kg/s] and not per timestep
