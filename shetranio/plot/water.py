import matplotlib.pyplot as plt
from ..hdf import Hdf
from ..dem import Dem
import datetime
import os
import numpy as np
from ipywidgets import interact, Dropdown

def balance(h5_file, timeseries_locations, start_date, out_dir=None, dem=None, interactive=True):
    """Using HDF file, produces Time Series of phreatic surface depth at timeseries locations

            Args:
                h5_file (str): Path to the input HDF5 file.
                hdf_group (str): Name of HDF file output group.
                timeseries_locations (str): Path to locations text file.
                start_date (datetime.datetime): Datetime object set to start of simulation period.
                out_dir (str, optional): Folder to save an output PNG into. Defaults to None.

            Returns:
                None

    """

    # Read in the x and y indices of the points
    with open(timeseries_locations) as f:
        # skip over the headers
        f.readline()
        col = []
        row = []
        for line in f:
            x_val, y_val = line.rstrip().split(",")
            col.append(int(x_val))
            row.append(int(y_val))

    number_of_points = len(col)

    if dem is not None:
        dem = Dem(dem)
        for i, (x, y)  in enumerate(zip(col, row)):
            col[i], row[i] = dem.get_index(x, y)

    # Open the HDF
    h5 = Hdf(h5_file)

    # Get the DEM from the HDF and take 1 off each end
    elevations = h5.surface_elevation.square[1:-1, 1:-1]

    # Get the times in hours from the HDF
    times = h5.soil_moisture.times[:]

    # Convert times in hours from run start to real times
    times = np.array([start_date + datetime.timedelta(hours=int(i)) for i in times])
    rain_times = np.array([start_date + datetime.timedelta(hours=int(i)) for i in h5.net_rain.times])

    def plot(point):
        # Read in the time series from the HDF

        net_rain = h5.net_rain.values[0, :].round(2)
        trnsp = np.array([round(m, 2) for m in h5.transpiration.values[row[point], col[point], :]])
        srf_evap = np.array([round(m, 2) for m in h5.surface_evaporation.values[row[point], col[point], :]])
        int_evap = np.array([round(m, 2) for m in h5.evaporation_from_interception.values[row[point], col[point], :]])
        total_evap = trnsp+srf_evap+int_evap
        theta = h5.soil_moisture.values[row[point], col[point], 0]

        # Create the plot
        # plt.subplots_adjust(bottom=0.2, right=0.75)
        fig, ax1 = plt.subplots(figsize=(12,5))
        ax2 = ax1.twinx()





        # Check if each elevation is inside the DEM and if so add to plot
        elevation = elevations[int(row[point]), int(col[point])]
        if elevation == -1:
            print('column', int(col[point]), 'row', int(row[point]), 'is outside of catchment')
        else:
            title = "Water Balance for Point {},{} at {}m"
            if dem is not None:

                plt.title(title.format(int(dem.x_coordinates[int(col[point])]), int(dem.y_coordinates[int(row[point])]), elevation))

            else:
                plt.title(title.format(int(col[point]), int(row[point]), elevation))
            ax1.bar(rain_times, net_rain, label='Rainfall', color='blue')
            ax2.plot(times, total_evap, label='Total Evaporation', color='green')
            # First value of soil moisture is replaced by NaN for plotting
            ax2.plot(times, np.append(np.array([np.nan]),theta[1:]), label='Surface Soil Moisture', color='orange')

        # ax.set_ylabel('Water Table Depth (m below ground)')
        ax1.set_ylabel('Net Rainfall (mm/hr)')
        ax2.set_ylabel('Soil Moisture (%)\nEvapotranspiration (mm/hour)')

        ax1.invert_yaxis()

        # Adjust plot settings
        plt.xticks(rotation=70)
        # plt.gca().invert_yaxis()
        h1, l1 = ax1.get_legend_handles_labels()
        h2, l2 = ax2.get_legend_handles_labels()

        ax1.legend(h1 + h2, l1 + l2,
            bbox_to_anchor=(0.5, -0.1),
            loc='center',
            # borderaxespad=0
            ncol=3,
        )

        # Save plot if out_dir set
        if out_dir:
            if not os.path.exists(out_dir):
                os.mkdir(out_dir)
            plt.savefig(os.path.join(out_dir,'waterbalance-timeseries-{}.png'.format(point)))

            with open(os.path.join(out_dir,'waterbalance-timeseries-{}.csv'.format(point)), 'w') as f:
                f.write('date,total_evaporation,soil_moisture\n')
                for i in range(len(times)):
                    f.write('{},{:.3f},{:.3f}\n'.format(times[i], total_evap[i], theta[i]))
            with open(os.path.join(out_dir,'waterbalance-timeseries-rainfall-{}.csv'.format(point)), 'w') as f:
                f.write('date,rainfall\n')
                for i in range(len(rain_times)):
                    f.write('{},{:.3f}\n'.format(rain_times[i], net_rain[i]))

        plt.show()

    if interactive:
        interact(plot,point=Dropdown(
            options = dict([(str(int(dem.x_coordinates[col[i]])) +',' + str(int(dem.y_coordinates[row[i]])), i)
                            for i in range(number_of_points)]),
            description='location:',
            continuous_update=False,
            readout_format='',
        ))
    else:
        for point in range(number_of_points):
            plot(point)