import matplotlib.pyplot as plt
from ..hdf import Hdf
from ..dem import Dem
import datetime
import os
import numpy as np
from ipywidgets import interact, Dropdown

def components(h5_file, timeseries_locations, start_date, out_dir=None, dem=None, interactive=True):
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
    times = h5.ph_depth.times[:]

    # Convert times in hours from run start to real times
    times = np.array([start_date + datetime.timedelta(hours=int(i)) for i in times])

    def plot(point):
        # Read in the time series from the HDF

        can_stor = [round(m, 2) for m in h5.canopy_storage.values[row[point], col[point], :]]
        trnsp = np.array([round(m, 2) for m in h5.transpiration.values[row[point], col[point], :]])
        srf_evap = np.array([round(m, 2) for m in h5.surface_evaporation.values[row[point], col[point], :]])
        int_evap = np.array([round(m, 2) for m in h5.evaporation_from_interception.values[row[point], col[point], :]])
        total_evap = trnsp+srf_evap+int_evap

        # Create the plot
        # plt.subplots_adjust(bottom=0.2, right=0.75)
        fig, ax1 = plt.subplots(figsize=(12,5))
        ax2 = ax1.twinx()

        # Check if each elevation is inside the DEM and if so add to plot
        elevation = elevations[int(row[point]), int(col[point])]
        if elevation == -1:
            print('column', int(col[point]), 'row', int(row[point]), 'is outside of catchment')
        else:
            if dem is not None:
                label = str(int(dem.x_coordinates[int(col[point])])) + ',' + str(int(dem.y_coordinates[int(row[point])])) +\
                    ' Elev:%.2f m' % elevation
            else:
                label = 'Col=' + str(int(col[point])) + ' Row=' + str(int(row[point])) + ' Elev= %7.2f m' % elevation[point]
            ax1.plot(times, can_stor, label='Canopy Storage', color='orange')
            ax2.plot(times, trnsp, label='Transpiration', color='green')
            ax2.plot(times, srf_evap, label='Surface Evaporation', color='blue')
            ax2.plot(times, int_evap, label='Evaporation from Interception', color='red')
            ax2.plot(times, total_evap, label='Total Evaporation', color='black')

        # ax.set_ylabel('Water Table Depth (m below ground)')
        ax1.set_ylabel('Canopy Storage (mm)')
        ax2.set_ylabel('Evaporation / Transpiration (mm/hr)')

        # Adjust plot settings
        plt.xticks(rotation=70)
        # plt.gca().invert_yaxis()
        h1, l1 = ax1.get_legend_handles_labels()
        h2, l2 = ax2.get_legend_handles_labels()

        ax1.legend(h1 + h2, l1 + l2,
            bbox_to_anchor=(0.5, -0.2),
            loc=9,
            ncol=2,
        )

        # Save plot if out_dir set
        if out_dir:
            if not os.path.exists(out_dir):
                os.mkdir(out_dir)
            plt.savefig(os.path.join(out_dir,'Water-ET-{}.png'.format(point)))
            with open(os.path.join(out_dir,'Water-ET-{}.csv'.format(point)), 'w') as f:
                f.write('dates,'
                        'canopy_storage,'
                        'transpiration,'
                        'surface_elevation,'
                        'evaporation_from_interception,'
                        'total_evaporation\n')

                for idx in range(len(times)):
                    f.write('{},{:.2f},{:.2f},{:.2f},{:.2f},{:.2f}\n'.format(
                        times[idx],
                        can_stor[idx],
                        trnsp[idx],
                        srf_evap[idx],
                        int_evap[idx],
                        total_evap[idx]))

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