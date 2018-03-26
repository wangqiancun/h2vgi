from __future__ import division
import numpy


def randomly_assign(activity_index, activity, vehicle):
    """Implement some smartness about assigning a station when level of H2 are low

    Args:
        activity_index (int): current activity index from vehicle.activities
        activity (Parked): activity to be assigned with a charging station
        vehicle (Vehicle): needed to lookup charging station used previously at
            the same location

    Return:
        a charging station object to be assign to the parked activity
    """
    # Randomly decide which charger will be assigned
    return numpy.random.choice(
        activity.location.available_charging_station['charging_station'].values.tolist(),
        p=activity.location.available_charging_station['probability'].values.tolist(),
        size=1,)[0]
