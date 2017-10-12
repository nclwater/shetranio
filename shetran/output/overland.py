import numpy as np
import matplotlib.pyplot as plt
import os
from .. import hdf
import datetime

def plot(h5_file, hdf_group, timeseries_locations, start_date, out_dir=None):
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
    h5 = hdf.Hdf(h5_file)

    # ovr_flow reference is [channel number:face:time]

    with open(timeseries_locations, 'r') as f:
        points = [int(point) for point in f.readlines()[1:]]

    number_of_points = len(points)

    # find location and elevation of each channel link
    # river links in Shetran flow along the edge of the grid squares. The number starts at the bottom left then considers each row in turn going upwards.
    # There are north-south and east-west channels
    ColRowLocation1, ColRowLocation2, ColRowLocation3, ColRowLocation4 = h5.number[:,:,5], h5.number[:,:,6], h5.number[:,:,7], h5.number[:,:,8]
    Elevation1, Elevation2 = h5.surface_elevation[:,:,5], h5.surface_elevation[:,:,6]
    elevation_link = np.zeros(shape=number_of_points)
    for i in range(number_of_points):
        p1 = np.where(ColRowLocation1 == int(points[i]))
        p2 = np.where(ColRowLocation2 == int(points[i]))
        p3 = np.where(ColRowLocation3 == int(points[i]))
        p4 = np.where(ColRowLocation4 == int(points[i]))
        if p1[0] > 0:
            elevation_link[i] = Elevation1[p1]
            # print str(int(OverlandLoc[i])) + ' is a E-W channel on column ' + str(p1[1])[1:-1] + ' between rows ' + str(
            #     p3[0])[1:-1] + ' and ' + str(p1[0])[1:-1] + ' with elevation = ' + str(Elevation1[p1])[1:-1]
        elif p2[0] > 0:
            elevation_link[i] = Elevation2[p2]
            # print str(int(OverlandLoc[i])) + ' is a N-S channel on row ' + str(p2[0])[1:-1] + ' between columns ' + str(
            #     p2[1])[1:-1] + ' and  ' + str(p4[1])[1:-1] + ' with elevation = ' + str(Elevation2[p2])[1:-1]
        else:
            elevation_link[i] = -999
            # print str(int(OverlandLoc[i])) + ' is not a Shetran link number'
        i += 1

    number_of_time_steps = len(h5.overland_flow_time)

    # setup a datetime array. there must be a better way than this
    times = np.array([start_date + datetime.timedelta(hours=int(h5.overland_flow_time[:][i]))
                      for i in range(number_of_time_steps)])

    # get the time series inputs
    # discharge is specifed at 4 faces. We want the maximum absolute discharge
    discharge_at_all_faces = np.zeros(shape=(number_of_points, 4, number_of_time_steps))
    maximum_absolute_discharge = np.zeros(shape=(number_of_points, number_of_time_steps))

    for i in range(number_of_points):
        if elevation_link[i] != -999:
            discharge_at_all_faces[i, :, :] = h5.overland_flow_value[points[i] - 1, :, :]
        i += 1
    for i in range(number_of_points):
        for j in range(0, number_of_time_steps):
            maximum_absolute_discharge[i, j] = np.amax(abs(discharge_at_all_faces[i, :, j]))

    labels = np.empty(number_of_points, dtype=object)
    plt.figure(figsize=[12.0, 5.0],
               dpi=300)
    plt.subplots_adjust(bottom=0.2, right=0.75)
    ax = plt.subplot(1, 1, 1)

    for idx in range(number_of_points):
        if elevation_link[idx] != -999:
            labels[idx] = 'River Link= %4s' % str(int(points[idx])) + ' Elev= %7.2f m' % elevation_link[idx]
            # plot m below ground
            ax.plot(times, maximum_absolute_discharge[idx, :], label=labels[idx])
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