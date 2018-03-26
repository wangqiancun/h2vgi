from __future__ import division
import model
import driving.drivecycle.generator as g
import datetime
import progressbar
import pandas


def run(project, charging_option=None, date_from=None, date_to=None,
        reset_charging_station=False, assign_drivecycle=True):
    """Launch a simulation in a decoupled manner, vehicle don't take other
    vehicle's actions into consideration. The simulation goes throught each
    activity one by one for each vehicle and number of iteration desired.
    When the simulation enters a driving activity, it computes the power demand
    and save time a which vehicles have stranded. When the simulation enters a
    parked activity, it first determines what is the charging station assigned
    and then compute the corresponding power demand from the grid.

    Args:
        project (Project): project to simulate
        date_from (datetime.datetime): date to start recording power demand
        date_to (datetime.datetime): date to end recording power demand
        charging_option (any): pass some object to the charging function
        reset_charging_station (boolean): reset charging stations to None
    """

    if date_from is None:
        date_from = project.date
    if date_to is None:
        date_to = project.date + datetime.timedelta(days=1)

    # Itinitialize result placeholders and reset charging stations to None
    project = _pre_run(project, date_from, date_to, reset=reset_charging_station)

    # Create the progress bar
    progress = progressbar.ProgressBar(widgets=['core.run: ',
                                                progressbar.Percentage(),
                                                progressbar.Bar()],
                                       maxval=len(project.vehicles)).start()

    # Load drivecycles
    if assign_drivecycle:
        UDDS, HWFT, US06 = g.load_EPA_drivecycle()

    # ####################### Simulation #####################################
    # For each vehicle
    inputid = []
    inputtime = []
    inputsoc = []
    for indexV, vehicle in enumerate(project.vehicles):
        # Assign drive-cycles
        if assign_drivecycle:
            g.assign_EPA_drivecyle(vehicle, UDDS, HWFT, US06, const_grade=0, verbose=False)

        # For each activity
        for indexA, activity in enumerate(vehicle.activities):
            # Calculate the duration of the activity
            nb_interval = int((activity.end - activity.start).total_seconds() / project.timestep)
            if isinstance(activity, model.Driving):
                hydrogen, power_demand, stranded, detail = vehicle.car_model.driving(activity,
                                                                                     vehicle,
                                                                                     nb_interval,
                                                                                     project.timestep)
                vehicle.hydrogen.append(vehicle.hydrogen[-1] - hydrogen[-1])
                # Log stranded vehicles
                if stranded:
                    vehicle.stranding_log.append(activity.end)

            elif isinstance(activity, model.Parked):
                # Get the charging station if not already assigned
                if activity.charging_station is None:
                    activity.charging_station = activity.location.assign_charging_station(indexA,
                                                                                          activity,
                                                                                          vehicle)

                # Compute the consumption at the charging station
                detail = False
                hydrogen, power_demand = activity.charging_station.charging(activity,
                                                                            vehicle,
                                                                            nb_interval,
                                                                            project.timestep,
                                                                            charging_option)

                vehicle.hydrogen.append(hydrogen[-1])


                # Save power demand at location
                if len(power_demand) != 0:
                    activity.location.result_function(activity.location,
                                                      project.timestep,
                                                      date_from, date_to,
                                                      vehicle, activity,
                                                      power_demand, hydrogen,
                                                      nb_interval, run=True)

            vehicle.result_function(vehicle, project.timestep, date_from,
                                    date_to, activity, power_demand, hydrogen,
                                    detail, nb_interval, run=True)

        # Remove initial hydrogen?
        # del vehicle.hydrogen[0]

        # Remove drivecycle
        g.remove_drivecyle(vehicle)

        # Update the progress bar
        progress.update(indexV + 1)
        # d = {'id' : inputid,'time' : inputtime, 'soc' : inputsoc}
        # df = pandas.DataFrame(d)
        # print df
    # ########################################################################

    # Post process result (change format, ...)
    project = _post_run(project, date_from, date_to)
    progress.finish()
    print('')


def _pre_run(project, date_from, date_to, reset):
    # Reset location result before starting computation
    for location in project.locations:
        location.result_function(location, project.timestep,
                                 date_from, date_to, init=True)

    # Reset activity charging station and vehicle results
    for vehicle in project.vehicles:
        vehicle.result_function(vehicle, project.timestep, date_from,
                                date_to, init=True)
        if reset:
            for activity in vehicle.activities:
                if isinstance(activity, model.Parked):
                    activity.charging_station = None

    return project


def _post_run(project, date_from, date_to):
    # Result post processing
    for location in project.locations:
        location.result_function(location, project.timestep, date_from, date_to,
                                 post=True)

    for vehicle in project.vehicles:
        vehicle.result_function(vehicle, project.timestep, date_from,
                                date_to, post=True)

    return project
