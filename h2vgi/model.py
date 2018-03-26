import driving.basic_powertrain
import charging.uncontrolled
import charging.station
import result
import cPickle
import copy
import datetime


class Project(object):
    """V2G-Sim project holder. It contains all the vehicles, locations,
    car models and charging stations used in the project. It also includes
    statistics on input activities for the vehicles.

    Args:
        vehicles (list): vehicle objects
        car_models (list): car model objects
        locations (list): location objects
        charging_stations (list): charging_station objects
        description (string): description of the project
        vehicle_statistics (pandas.DataFrame): statistics for individual
            vehicles (distance traveled, ...)
        itinerary_statistics (pandas.DataFrame): statistics for specific
            itinerary combinaisons (number of vehicles, ...)
        timestep (int): simulation interval in [seconds]
    """

    def __init__(self, description='no description', timestep=60):
        self.vehicles = []
        self.car_models = []
        self.locations = []
        self.charging_stations = []
        self.description = description
        self.vehicle_statistics = None
        self.itinerary_statistics = None
        self.timestep = timestep
        self.date = datetime.datetime.now().replace(hour=0, minute=0,
                                                    second=0, microsecond=0)

    def check_integrity(self):
        """Launch tests on the project
        """
        pass

    def copy(self):
        """Deep copy the project and return the copy
        """
        return copy.deepcopy(self)

    def save(self, filename):
        """Save the project

        Args:
            filename (string): path to save the project (/../my_project.v2gsim)
        """
        with open(filename, "wb") as output:
            cPickle.dump(self, output, cPickle.HIGHEST_PROTOCOL)

    def load(self, filename):
        """Load a project

        Args:
            filename (string): path to a project (/../my_project.v2gsim)
        """
        with open(filename, "rb") as input:
            project = cPickle.load(input)

        return project


class FuelCell(object):
    """Basic fuel cell model
    """
    def __init__(self, name="Tuscon", maker="Hyundai", year=2016,
                 a=30.723, b=0.43859, c=0.021212, driving=driving.basic_powertrain.simulate_FCEV,
                 p1=1.5e-5, p2=9.0e-8, p3=2.5e-5, p4=9.0e-7, p5=-0.0774,
                 weight_lb=4500, FCEV_horsepower=134, fuel_type='hydrogen'):
        self.name = name
        self.maker = maker
        self.year = year
        self.a = a
        self.b = b
        self.c = c
        self.p1 = p1
        self.p2 = p2
        self.p3 = p3
        self.p4 = p4
        self.p5 = p5
        self.weight_lb = weight_lb  # in lbs
        self.FCEV_horsepower = FCEV_horsepower  # hp
        self.fuel_type = fuel_type  # 'gasoline', 'diesel', 'e85' or 'hydrogen'
        self.driving = driving
        self.tank_size = 4.2  # [kg]

    def __repr__(self):
        return "FuelCell car model: name({}) maker({})".format(
            self.name, self.maker)


class Vehicle(object):
    """Vehicle represents a single car with a specific model and set of
    activities throughout the day. Vehicles keep track of their hydrogen as well
    as their stranding log.

    Args:
        id (int): unique id
        initial_level (float): intital amount of hydrogen in tank [kg]
        activities (list): activities throughout the day
            (parked, driving, parked, ...)
        weight (float): how representative is a vehicle [0, 1]
        valid_activities (boolean): True if activities don't leave any
            gap of time, the end of an activity must correspond with the start
            of the next one
        stranding_log (list): time at which the vehicle has stranded [hour]
        car_model (BasicCarModel): car model associated to the vehicle
        result_function (func): function describing the way results are saved
        result (any): result structure returned by the result function
        battery_model (BatteryModel): model to represent battery degradation
    """

    def __init__(self, index, car_model, initial_level=4.2):
        self.id = index
        self.car_model = car_model
        self.hydrogen = [initial_level]
        self.activities = []
        self.weight = 1
        self.valid_activities = False
        self.stranding_log = []
        self.result_function = result.save_vehicle_state
        self.result = None

    def check_activities(self, start_date, end_date):
        """Verify if every activity start at the end of the previous activity
        """
        self.valid_activities = True
        if self.activities[0].start != start_date:
            self.valid_activities = False
            return False

        for i in range(0, len(self.activities) - 1):
            if self.activities[i].end != self.activities[i + 1].start:
                self.valid_activities = False
                return False

        if self.activities[-1].end != end_date:
            self.valid_activities = False
            return False

        return True

    def __repr__(self):
        string = ("Vehicle: id({}) car_model.name({}) ").format(self.id,
                                                                self.car_model.name)
        for activity in self.activities:
            string += "\n" + activity.__repr__()
        return string + "\n"


class Activity(object):
    """ Activity is an abstract class that is implemented in Driving and Parked.

    Args:
        start (datetime): start time of the activity
        end (datetime): end time of the activity
    """

    def __init__(self, start, end):
        self.start = start
        self.end = end


class Parked(Activity):
    """ Parked activity inherits from Activity. It represents a car parked at
    a location.

    Args:
        location (Location): (required) location object at which the vehicle
            is parked
        charging_station (ChargingStation): charging station at which a
            vehicle is plugged
    """

    def __init__(self, start, end, location,
                 charging_station=None):
        Activity.__init__(self, start, end)
        self.location = location
        self.charging_station = charging_station

    def __repr__(self):
        string = ("Parked Activity: start({}) end({}) " +
                  "location({})").format(
                      self.start, self.end,
                      self.location.category)
        if self.charging_station:
            string += " charging_station({}W)".format(
                self.charging_station.maximum_power)
        return string


class Driving(Activity):
    """ Driving represents a drivecycle, it inherits from Activity.
    Note that units differ from the SI units since distance is in [km]
    and speed in [km/h]. Data is indexed with at project timestep rate.

    Args:
        distance (float): distance traveled in [km]
        speed (list): drive cycle speed in [km/h]
        terrain (list): grade along the drive cycle in [rad]
    """

    def __init__(self, start, end, distance):
        Activity.__init__(self, start, end)
        self.distance = distance
        self.speed = []
        self.terrain = []

    def __repr__(self):
        return "Driving: start({}) end({}) distance({}km)".format(
            self.start, self.end, self.distance)


class Location(object):
    """ Location physical place or a category of place.

    Args:
        name (string): (required) name of the location
        category (string): (required) type of location (Home, Work, ...)
        position (tuple): GPS position
        result (pandas.DataFrame): results
        result_function (func): function to create and update the result
            data frame
        available_charging_station (pandas.DataFrame): describe the
            availability of charging stations (charging_station,
            probability, available, total)
        assign_charging_station_function (func): function to assign a
            charging station to an incoming vehicle
    """

    def __init__(self, category, name, position=(0, 0),
                 assign_charging_station=charging.station.randomly_assign,
                 result_function=result.save_location_state):
        self.category = category
        self.name = name
        self.position = position
        self.result = None
        self.result_function = result_function
        self.available_charging_station = None
        self.assign_charging_station = assign_charging_station

    def __repr__(self):
        return ("Location: type({})" +
                " name({}) GPS({}))\n").format(self.category,
                                               self.name, self.position)


class ChargingStation(object):
    """ Charging station represents a type of infrastructure

    Args:
        name (string): name associated with the infrastructure
        charging (func): function to control
            the charging behavior
        post_simulation (boolean): True station can be subject to post processing
        maximum_power (float): maximum rate at which a vehicle can charge
        minimum_power (float): minimum rate at which a vehicle can charge
    """

    def __init__(self, charging=charging.uncontrolled.consumption,
                 maximum_power=1440, minimum_power=-1440, post_simulation=False,
                 name='charger'):
        self.name = name
        self.post_simulation = post_simulation
        self.charging = charging

    def __repr__(self):
        return ("Charging infrastructure: powerRateMax({})" +
                "powerRateMin({}) charging({})\n").format(
                    str(self.charging))


class ItineraryBin(object):
    """Hold statistics for specific itineraries

    Args:
        vehicles (list): vehicles having this itinerary combinaison
        statistics (pandas.DataFrame): statistics for individual activities (
            duration, distance, ...)
        weight (float): weight associated to this itinerary combinaison
    """

    def __init__(self, vehicles):
        self.vehicles = vehicles
        self.statistics = None
        self.weight = None
        # self.parameters = {'startTime': [], 'meanSpeed': [],
        #                    'duration': [], 'durationParked': []}

    def __repr__(self):
        return ("This ItineraryBin is composed of {} vehicles with {} " +
                "locations along the day \n").format(len(self.vehicle),
                                                     len(self.locationName))
