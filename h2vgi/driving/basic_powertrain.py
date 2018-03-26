from __future__ import division
import math
import numpy


def consumption(activity, vehicle, nb_interval, timestep, verbose=False):
    """Calculate the consumption when a vehicle is driving

    Args:
        activity (Driving): a driving activity
        vehicle (Vehicle): a Vehicle object to update with the driving
            activity consumption
        nb_interval (int): number of timestep for the driving activity
        timestep (int): calculation timestep

    Return:
        hydrogen (list): state of charge/
        power_demand (list): power demand/
        stranded (boolean): True if the vehicle run out of charge during the
        activity
        detail (any type): optional data
    """

    # Calculate the duration
    duration = nb_interval * timestep / 3600

    # Get the mean speed
    if duration > 0:
        mean_speed = activity.distance / duration
    else:
        if verbose:
            print('Activity duration is shorter than timestep')
        return [], [], False, False

    # Get the volume Liter consumption per km
    energyConsumption = _drivecycle_energy_per_distance(vehicle.car_model, mean_speed)

    # Set the total energy needed for the trip (L)
    energy = activity.distance * energyConsumption

    # Set the power demand for this driving activity L / sec
    constant_power_demand = energy / (nb_interval * timestep)
    power_demand = [constant_power_demand] * nb_interval

    return [vehicle.hydrogen[-1]] * nb_interval, power_demand, False, False


def _drivecycle_energy_per_distance(car_model, mean_speed):
    # Get the energy consumption per km

    # UDDS (Urban Dynamometer Driving Schedule) 12.07km
    # with maximum speed 91.25km/h and average speed
    # of 31.5km/h (19.6mph)
    UDDS = 31.5  # (km/h)

    # HWFET (Highway Fuel Economy Test) 16.45km
    # with average speed 77.7km/h (48.3mph)
    HWFET = 77.7  # (km/h)

    # US06 12.8km average speed 77.9km/h (48.4mph)with
    # a maximum speed at 129.2km/h
    # --> above HWFET

    # Delhi (no information) congested city drive cycle
    # --> below UDDS

    # Determine the right consumption (!) Need more linearity
    if mean_speed < UDDS:
        # Consumption for a slow driving cycle
        energy_consumption = car_model.UDDS
    elif mean_speed >= UDDS and mean_speed <= HWFET:
        # Mix between a UDDS and a HWFET drice cycle consumption
        energy_consumption = car_model.HWFET
    elif mean_speed > HWFET:
        # Consumption for a fast driving cycle
        energy_consumption = car_model.US06

    return energy_consumption


def simulate_FCEV(activity, vehicle, nb_interval, timestep, verbose=False):
    """ Calculate the drive cycle fuel consumption for the chosen FCEV vehicle

    Args:
        activity (Driving): a driving activity
        vehicle (Vehicle): a Vehicle object to update with the driving
            activity consumption
        nb_interval (int): number of timestep for the driving activity
        timestep (int): calculation timestep

    Outputs:
    FC_instant = List of instantaneous fuel consumption rate [kg fuel/s]
    FC_cum = List of cumulative fuel consumption rate [kg fuel]

    """
    if nb_interval == 0:
        return [vehicle.hydrogen[-1]], [0], False, False

    velocity_profile = activity.speed
    theta_profile = numpy.interp(numpy.arange(0, len(activity.speed), 1),
                                 numpy.arange(0, len(activity.speed), len(activity.speed) - 1),
                                 activity.terrain)
    virtual_fueltank_init_level = 0
    m_veh = vehicle.car_model.weight_lb * 0.453592  # From lb to kg
    target_A = vehicle.car_model.a
    target_B = vehicle.car_model.b
    target_C = vehicle.car_model.c
    parameter_p1 = vehicle.car_model.p1
    parameter_p2 = vehicle.car_model.p2
    parameter_p3 = vehicle.car_model.p3
    parameter_p4 = vehicle.car_model.p4
    parameter_p5 = vehicle.car_model.p5
    FCEV_horsepower = vehicle.car_model.FCEV_horsepower
    dt = 1  # Use a 1-second timestep
    g = 9.80665  # Acceleration due to gravity [m/s^2]
    fuel_LHV = 120210  # kJ/kg

    # Calculate fueling limits
    FC_limit_dema = 260  # Demarcation point for calculating fuel limits [horsepower]
    if FCEV_horsepower < FC_limit_dema:
        FC_limit_A = -2.517e-05
        FC_limit_B = 0.03847
        FC_limit_C = 2.834
    elif FCEV_horsepower >= FC_limit_dema:
        FC_limit_A = -1.329e-05
        FC_limit_B = 0.0291
        FC_limit_C = 5.068

    FC_limit_lower = (FCEV_horsepower * 0.735) / (0.85 * fuel_LHV)  # [kg/s]
    FC_limit_upper = (FCEV_horsepower * 0.735) / (0.40 * fuel_LHV)  # [kg/s]

    FC_limit = 0.001 * (FC_limit_A * (FCEV_horsepower**2) + FC_limit_B * FCEV_horsepower + FC_limit_C)  # kg/s
    if FC_limit > FC_limit_upper:
        FC_limit = FC_limit_upper
    elif FC_limit < FC_limit_lower:
        FC_limit = FC_limit_lower

    acceleration_profile = calculate_acceleration(velocity_profile)
    FC_rate = []
    FC_total = []

    for i in range(0, len(velocity_profile)):  # Drive cycle simulation
        a = acceleration_profile[i]
        v = velocity_profile[i]
        theta = theta_profile[i]

        # Tractive power
        P_trac = ((m_veh * a * v) + (target_A + target_B * (v * 2.2369) + target_C * (v * 2.2369)**2) * v * 4.448 + m_veh * g * math.sin(theta) * v) / 1000  # Tractive power at timestep i [kW]

        # Instantaneous fuel consumption rate
        if P_trac >= 0:
            FC_rate_instant = parameter_p2 * (P_trac**2) + parameter_p1 * P_trac  # kg/s
        elif P_trac < 0:
            FC_rate_instant = (parameter_p4 * (P_trac**2) + parameter_p3 * P_trac) * parameter_p5  # kg/s

        if FC_rate_instant > FC_limit:
            FC_rate_instant = FC_limit
        elif FC_rate_instant < -FC_limit:
            FC_rate_instant = -FC_limit

        if FC_rate_instant > 0:
            FC_rate_instant_kg = FC_rate_instant
            FC_rate.append(FC_rate_instant_kg)
        elif FC_rate_instant <= 0:
            FC_rate.append(0.0)

        # Calculate cumulative fuel consumption in kg, accounting for virtual tank fuel usage
        if i == 0:
            VT = virtual_fueltank_init_level  # kg fuel initially within the virtual tank
            FC_cumu = 0.0

        elif i > 0:
            if FC_rate_instant < 0:  # Fuel is deposited into the virtual fuel tank during negative tractive power (regenerative braking or downhill)
                VT = -FC_rate_instant * dt + VT  # kg, kg fuel that remains in the virtual tank
                FC_cumu = FC_cumu + 0.0  # No change in cumulative (real) fuel consumed, kg fuel

            elif FC_rate_instant >= 0:  # Fuel is consumed from the actual or the virtual fuel tank during positive tractive power
                if FC_rate_instant * dt <= VT:  # All instantaneous fuel consumption comes from the virtual fuel tank
                    VT = VT - FC_rate_instant * dt  # Use fuel from the virtual tank [kg]
                    FC_cumu = FC_cumu + 0.0  # No real fuel is used [kg]

                elif FC_rate_instant * dt > VT:  # Virtual tank has some fuel, but not enough for the instantaneous fuel requirements
                    FC_rate_temp = ((FC_rate_instant * dt) - VT) / dt  # Calculate how much fuel rate requirement remains after using all fuel in the virtual tank [kg/s]
                    VT = 0.0  # All fuel from the virtual tank is consumed, leaving zero fuel in the virtual tank [kg]
                    FC_cumu = FC_cumu + FC_rate_temp * dt  # Total cumulative fuel that has been consumed so far from the real tank [kg]

        FC_total.append(FC_cumu)  # kg fuel consumed
        # virtual_fueltank_final_level = VT  # kg fuel remaining in the virtual tank

    # Interpolate the result at the right sample time (assuming speed is in seconds)
    FC_total = numpy.interp([value * timestep for value in range(0, nb_interval)],
                            range(0, len(velocity_profile)), FC_total)
    FC_rate = numpy.interp([value * timestep for value in range(0, nb_interval)],
                           range(0, len(velocity_profile)), FC_rate)
    return FC_total, FC_rate, False, False


def calculate_acceleration(velocity_profile):
    """ Calculate drive cycle acceleration profile.
    Assumes 1-second timesteps of the input velocity profile

    Inputs:
    velocity_profile = List of drive cycle velocity profile at each timestep [m/s]
    Outputs:
    acceleration_profile = List of drive cycle acceleration profile at each timestamp [m/s^2]
    """
    dt = 1  # Use a 1-second timestep
    acceleration_profile = []
    for i in range(0, len(velocity_profile)):
        if i == 0:
            a = 0  # Set acceleration to zero in first timestamp
        elif i > 0:
            a = (velocity_profile[i] - velocity_profile[i - 1]) / dt
        acceleration_profile.append(a)

    return acceleration_profile
