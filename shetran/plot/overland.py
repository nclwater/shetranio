import numpy as np
import matplotlib.pyplot as plt
import os
from ..hdf import Hdf
import datetime

def numbers(h5_file, timeseries_locations, start_date, out_dir=None):
    """Using HDF file, produces Time Series of discharge at specified Shetran channel numbers

        Args:
            h5_file (str): Path to the input HDF5 file.
            hdf_group (str): Name of HDF file output group.
            timeseries_locations (str): Path to locations text file.
            start_date (datetime.datetime): Datetime object set to start of simulation period.
            out_dir (str, optional): Folder to save an output PNG into. Defaults to None.

        Returns:
            None

    """
    h5 = Hdf(h5_file)

    # ovr_flow reference is [channel number:face:time]

    with open(timeseries_locations, 'r') as f:
        points = [int(point) for point in f.readlines()[1:]]

    # This is where conversion from coordinates to element numbers needs to happen
    # Need the lower left coordinates of the grid, then get the nearest cell to the given coordinates

    number_of_points = len(points)

    # find location and elevation of each channel link
    # river links in Shetran flow along the edge of the grid squares. The number starts at the bottom left then considers each row in turn going upwards.
    # There are north-south and east-west channels
    # number[x_index,y_index,channel_direction]
    # 5 seems to be north-south channels and 6 east west
    # The same applies to surface elevation
    # This section seems to just check if the cells are channels or not
    north_south_element_numbers, east_west_element_numbers = h5.number[:,:,5], h5.number[:,:,6]

    Elevation1, Elevation2 = h5.surface_elevation[:,:,5], h5.surface_elevation[:,:,6]
    elevation_links = []
    for point in points:

        if point in north_south_element_numbers:
            north_south_element_index = np.where(north_south_element_numbers == point)
            elevation_links.append(Elevation1[north_south_element_index])
            # print str(int(OverlandLoc[i])) + ' is a E-W channel on column ' + str(p1[1])[1:-1] + ' between rows ' + str(
            #     p3[0])[1:-1] + ' and ' + str(p1[0])[1:-1] + ' with elevation = ' + str(Elevation1[p1])[1:-1]
        elif point in east_west_element_numbers:
            east_west_element_index = np.where(east_west_element_numbers == point)
            elevation_links.append(Elevation2[east_west_element_index])
            # print str(int(OverlandLoc[i])) + ' is a N-S channel on row ' + str(p2[0])[1:-1] + ' between columns ' + str(
            #     p2[1])[1:-1] + ' and  ' + str(p4[1])[1:-1] + ' with elevation = ' + str(Elevation2[p2])[1:-1]
        else:
            elevation_links.append(-999)
            # print str(int(OverlandLoc[i])) + ' is not a Shetran link number'

    number_of_time_steps = len(h5.overland_flow_time)

    # setup a datetime array. there must be a better way than this
    times = np.array([start_date + datetime.timedelta(hours=int(h5.overland_flow_time[:][i]))
                      for i in range(number_of_time_steps)])

    # get the time series inputs
    # discharge is specifed at 4 faces. We want the maximum absolute discharge
    discharge_at_all_faces = np.zeros(shape=(number_of_points, 4, number_of_time_steps))
    maximum_absolute_discharge = np.zeros(shape=(number_of_points, number_of_time_steps))

    for i in range(number_of_points):
        if elevation_links[i] != -999:
            # Why is 1 being subtracted from the element number?
            discharge_at_all_faces[i, :, :] = h5.overland_flow_value[points[i] - 1, :, :]
        i += 1
    for i in range(number_of_points):
        for j in range(0, number_of_time_steps):
            maximum_absolute_discharge[i, j] = np.amax(abs(discharge_at_all_faces[i, :, j]))

    plt.figure(figsize=[12.0, 5.0],
               dpi=300)
    plt.subplots_adjust(bottom=0.2, right=0.75)
    ax = plt.subplot(1, 1, 1)

    for idx in range(number_of_points):
        if elevation_links[idx] != -999:
            # plot m below ground
            ax.plot(times, maximum_absolute_discharge[idx, :],
                    label='River Link= %4s' % str(int(points[idx])) + ' Elev= %7.2f m' % elevation_links[idx])
            # plot absolute elevation
            # ax.plot(psltimes,elevation[i]-inputs[i,:],label=plotlabel[i])
    # plot m below ground
    ax.set_ylabel('Discharge (m$^3$/s)')
    plt.xticks(rotation=70)
    ax.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0., prop={'size': 8})
    if out_dir:
        if not os.path.exists(out_dir):
            os.mkdir(out_dir)
        plt.savefig(os.path.join(out_dir, 'Discharge-timeseries.png'))
    plt.show()

def xy(h5_file, timeseries_locations, start_date, dem_file, out_dir=None):
    """Using HDF file, produces Time Series of discharge at specified locations

        Args:
            h5_file (str): Path to the input HDF5 file.
            hdf_group (str): Name of HDF file output group.
            timeseries_locations (str): Path to locations text file.
            start_date (datetime.datetime): Datetime object set to start of simulation period.
            dem_file (str): Path to an ASCII text file of the input DEM.
            out_dir (str, optional): Folder to save an output PNG into. Defaults to None.

        Returns:
            None

    """
    # Read in the h5 file to an Hdf object
    h5 = Hdf(h5_file)

    # Read in the file with locations and directions
    # point_locations is a list of tuples as (x coordinate, y coordinate, direction)
    with open(timeseries_locations, 'r') as f:
        point_locations = [(float(point.split(',')[0]),
                            float(point.split(',')[1]),
                            str(point.split(',')[2].strip()))
                  for point in f.readlines()[1:]]

    # Setup variables to hold the SHETRAN element numbers of the points and their elevations
    point_element_numbers = []
    point_elevations = []

    # Get the element numbers of each point and check that they aren't -1
    for point_location in point_locations:
        x = point_location[0]
        y = point_location[1]
        direction = point_location[2]
        point_element_numbers.append(h5.get_channel_link_number(dem_file,(x,y),direction))
        assert point_element_numbers[-1] != -1, 'There is no ' +str(point_location[2])+' link at '+str(point_location[:2])

    # Get the elevations for the channel links
    directions = [i[2] for i in point_locations]
    for point_element_number, direction in zip(point_element_numbers, directions):
        point_elevations.append(h5.surface_elevation.get_link(direction)
                                [np.where(h5.number.get_link(direction) == point_element_number)])

    number_of_points = len(point_element_numbers)

    number_of_time_steps = len(h5.overland_flow_time)

    # Create an array of dates from the start date based on hours in the HDF file
    times = np.array([start_date + datetime.timedelta(hours=int(h5.overland_flow_time[:][i]))
                      for i in range(number_of_time_steps)])

    # Create arrays to hold the discharge at all faces and the maximum absolute discharge
    discharge_at_all_faces = np.zeros(shape=(number_of_points, 4, number_of_time_steps))
    maximum_absolute_discharge = np.zeros(shape=(number_of_points, number_of_time_steps))

    # Get the discharges from the HDF file
    for i in range(number_of_points):
        # Subtract one from the element number to convert to index?
        discharge_at_all_faces[i, :, :] = h5.overland_flow_value[point_element_numbers[i] - 1, :, :]

    # Calculate the maximum
    for i in range(number_of_points):
        for j in range(number_of_time_steps):
            maximum_absolute_discharge[i, j] = np.amax(abs(discharge_at_all_faces[i, :, j]))

    # Create the figure
    plt.figure(figsize=[12.0, 5.0], dpi=300)
    plt.subplots_adjust(bottom=0.2, right=0.75)
    ax = plt.subplot(1, 1, 1)

    # Plot a line for each point
    for idx in range(number_of_points):
        ax.plot(times, maximum_absolute_discharge[idx, :],
                label='River Link= %s Elev= %.2fm' % (str(int(point_element_numbers[idx])), point_elevations[idx])
                )

    # Adjust figure
    ax.set_ylabel('Discharge (m$^3$/s)')
    plt.xticks(rotation=70)
    ax.legend( )

    # Save if out_dir is specified
    if out_dir:
        if not os.path.exists(out_dir):
            os.mkdir(out_dir)
        plt.savefig(os.path.join(out_dir, 'Discharge-timeseries.png'))
    plt.show()