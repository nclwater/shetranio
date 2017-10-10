import matplotlib.pyplot as plt
import numpy as np
import h5py
import os
from ipywidgets import interact, IntSlider, Layout


def plot_points(h5_file, hdf_group, timeseries_locations, n_layers, out_dir=None, interactive=True, timestep=0):
    """Using HDF file produces soil moisture profile plots of particular points.
            Each figure shows all the points at a particular time.
            There is a separate figure for each time.

                Args:
                    h5_file (str): Path to the input HDF5 file.
                    hdf_group (str): Name of HDF file output group.
                    out_dir (str): Folder to save the output PNG into.
                    timeseries_locations (str): Points that you want time series inputs for.
                    n_layers (int): Number of soil layers needing output for. Starting from the top.

                Returns:
                    None

    """
    def getElevations():
        tgroup = '/CONSTANTS'
        tsubgroup = 'surf_elv'

        group = fh5[tgroup]
        # print group

        for subgroup in group:  # iterate over subgroups
            # print subgroup
            if tsubgroup in subgroup:
                # print 'found required subgroup: ' , subgroup

                val = group[subgroup]
                dims = val.shape
                # Shetran adds extra column and row around grid. Only need dem in normal grid
                nrows = dims[0] - 1
                ncols = dims[1] - 1
                dem = val[0:nrows - 1, 0:ncols - 1, 0]

        return np.array(dem), nrows, ncols


    def getCellSziesFromPoint(j, i, nlayers):
        tgroup = '/CONSTANTS'
        tsubgroup = 'vert_thk'

        group = fh5[tgroup]

        for subgroup in group:  # iterate over subgroups
            if tsubgroup in subgroup:
                # print 'found required subgroup: ' , subgroup
                val = group[subgroup]

                # inputs[nrows:ncols:time] ie [j,i,:]
                data = val[j, i, 0, 0:nlayers]

        return data


    def FindNumberofLayers(HDFgroup):
        tgroup = '/VARIABLES'
        tsubgroup = HDFgroup

        group = fh5[tgroup]

        for subgroup in group:  # iterate over subgroups
            if tsubgroup in subgroup:
                # print 'found required subgroup: ' , subgroup
                val = group[subgroup + '/' + 'value']
                dims = val.shape
                nlayers = dims[2]

        return nlayers


    def getTimeSeriesFromPoint(j, i, HDFgroup):
        tgroup = '/VARIABLES'
        tsubgroup = HDFgroup

        group = fh5[tgroup]

        for subgroup in group:  # iterate over subgroups
            if tsubgroup in subgroup:
                # print 'found required subgroup: ' , subgroup
                val = group[subgroup + '/' + 'value']

                # inputs[nrows:ncols:nlayers:time]
                data = val[j, i, :, :]
                # no value set to nan
                data[data == -1.0] = np.nan

        return data


    def getmoisturetimes(HDFgroup):
        tgroup = '/VARIABLES'
        tsubgroup = HDFgroup

        group = fh5[tgroup]

        for subgroup in group:  # iterate over subgroups
            if tsubgroup in subgroup:
                # print 'found required subgroup: ' , subgroup
                times = group[subgroup + '/' + 'time']
                moisturetimes = times[:]

        return moisturetimes


    def timeseriesplot(moisturetimes, depth, data, ntimes, Npoints, row, col, elevation, minth, maxth, userspecNlayers):
        # time = 1
        # while time < ntimes:
        def plot(time):
            plotlabel = np.empty(Npoints, dtype=object)
            fig = plt.figure(figsize=[12.0, 5.0], dpi=300)
            plt.subplots_adjust(bottom=0.1, right=0.75)
            ax = plt.subplot(1, 1, 1)
            ax.set_ylabel('Depth(m)')
            ax.set_xlabel('Soil moisture content')
            points = 0

            while points < Npoints:
                if elevation[points] != -1:
                    plotlabel[points] = 'Col=' + str(int(col[points])) + ' Row=' + str(
                        int(row[points])) + ' Elev= %7.2f m' % elevation[points]
                    ax.plot(data[0:userspecNlayers - 1, time, points], depth[0:userspecNlayers - 1],
                            label=plotlabel[points])
                points += 1
            axes = plt.gca()
            axes.set_xlim([minth, maxth])
            plt.gca().invert_yaxis()
            legend = ax.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0., prop={'size': 8})
            plt.title("Profile. Time = %7.0f hours" % moisturetimes[time])
            if out_dir:
                if not os.path.exists(out_dir):
                    os.mkdir(out_dir)
                plt.savefig(out_dir + '/' + 'profile' + str(time) + '.png')
            plt.show()
            # time += 1
        if interactive:
            return interact(plot, time=IntSlider(value=timestep,
                                                         min=0,
                                                         max=ntimes-1,
                                                         step=1,
                                                         continuous_update=False,
                                                         description=' ',
                                                         readout_format='',
                                                         layout=Layout(width='100%')),
                            )
        else:
            plot(timestep)


    def minmaxmoisture(data, ntimes, Npoints):
        minth = 99999.0
        maxth = -99999.0
        minth = min(minth, np.nanmin(data[:, 1:ntimes, :]))
        maxth = max(maxth, np.nanmax(data[:, 1:ntimes, :]))

        return minth, maxth


    def getTimeSeriesNpoints(locations):
        # skip over the headers
        locations.readline()
        i = 0
        for line in locations:
            line.rstrip().split(",")
            i += 1
        return i


    def getTimeSeriesLocation(locations, Npoints):
        # skip over the headers
        locations.readline()
        i = 0
        x = np.zeros(shape=(Npoints))
        y = np.zeros(shape=(Npoints))
        for line in locations:
            x[i], y[i] = line.rstrip().split(",")
            i += 1
        return x, y


    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

    # make folder for graphs and outputs
    # if out_dir:
    #     if not os.path.exists(out_dir):
    #         os.mkdir(out_dir)

    # number of points (Npoints) in time series file
    locations = open(timeseries_locations, "r")
    Npoints = getTimeSeriesNpoints(locations)

    # go back to start of file and get locations
    locations.seek(0)
    col, row = getTimeSeriesLocation(locations, Npoints)
    fh5 = h5py.File(h5_file, 'r')
    # dem is row number(from top), column number
    dem, nrows, ncols = getElevations()

    # elevations correspond to the row number and column number in hdf file
    elevation = np.zeros(shape=(Npoints))
    i = 0
    while i < Npoints:

        elevation[i] = dem[int(row[i]), int(col[i])]
        # if elevation[i] == -1:
        #     print 'column ', int(col[i]), ' row ', int(row[i]), ' outside of catchment'

        i += 1

    # get times of output. ntimes is the final time
    moisturetimes = getmoisturetimes(hdf_group)
    dimstime = moisturetimes.shape
    ntimes = dimstime[0]
    assert 0 <= timestep < ntimes, 'Timestep must be between 0 and %s' % (int(ntimes) - 1)

    # get the number of layers for which output is defined. This is specified in the visulisation plan file and might not be all the layers
    nlayers = FindNumberofLayers(hdf_group)
    n_layers = min(nlayers, n_layers)

    # get the time series inputs
    data = np.zeros(shape=(nlayers, ntimes, Npoints))
    i = 0
    while i < Npoints:
        data[:, :, i] = getTimeSeriesFromPoint(row[i], col[i], hdf_group)
        i += 1

    # get the cell sizes of the layers. consider all the cells so that one is within the catchment
    thickness = np.zeros(shape=(nlayers))
    actThickness = np.zeros(shape=(nlayers))
    i = 0
    j = 0
    while i < Npoints:
        thickness[:] = getCellSziesFromPoint(row[i], col[i], nlayers)
        while j < nlayers:
            actThickness[j] = max(actThickness[j], thickness[j])
            j += 1
        i += 1

    # calculate depths from thicknesses
    depth = np.zeros(nlayers)
    i = 1
    depth[0] = actThickness[0] / 2.0
    while i < nlayers:
        depth[i] = depth[i - 1] + actThickness[i] / 2.0 + actThickness[i - 1] / 2.0
        i += 1

    # get min and max theta
    minth, maxth = minmaxmoisture(data, ntimes, Npoints)

    # time series plots.
    # print 'Profile plot'
    timeseriesplot(moisturetimes, depth, data, ntimes, Npoints, row, col, elevation, minth, maxth, n_layers)


def plot_times(h5_file, hdf_group, timeseries_locations, n_layers, interactive=True, out_dir=None, point=0):
    """Using HDF file produces soil moisture profile plots of particular points.
                Each figure shows a single points with all times.
                There is a separate figure for each point.

                    Args:
                        h5_file (str): Path to the input HDF5 file.
                        hdf_group (str): Name of HDF file output group.
                        out_dir (str): Folder to save the output PNG into.
                        timeseries_locations (str): Points that you want time series inputs for.
                        n_layers (int): Number of soil layers needing output for. Starting from the top.

                    Returns:
                        None

                """

    def getElevations():

        tgroup = '/CONSTANTS'
        tsubgroup = 'surf_elv'

        group = fh5[tgroup]
        # print group

        for subgroup in group:  # iterate over subgroups
            # print subgroup
            if tsubgroup in subgroup:
                # print 'found required subgroup: ' , subgroup

                val = group[subgroup]
                dims = val.shape
                # Shetran adds extra column and row around grid. Only need dem in normal grid
                nrows = dims[0] - 1
                ncols = dims[1] - 1
                dem = val[0:nrows - 1, 0:ncols - 1, 0]

        return np.array(dem), nrows, ncols

    def getCellSziesFromPoint(j, i, nlayers):

        tgroup = '/CONSTANTS'
        tsubgroup = 'vert_thk'

        group = fh5[tgroup]

        for subgroup in group:  # iterate over subgroups
            if tsubgroup in subgroup:
                # print 'found required subgroup: ' , subgroup
                val = group[subgroup]

                # inputs[nrows:ncols:time] ie [j,i,:]
                data = val[j, i, 0, 0:nlayers]

        return data

    def FindNumberofLayers(HDFgroup):

        tgroup = '/VARIABLES'
        tsubgroup = HDFgroup

        group = fh5[tgroup]

        for subgroup in group:  # iterate over subgroups
            if tsubgroup in subgroup:
                # print 'found required subgroup: ' , subgroup
                val = group[subgroup + '/' + 'value']
                dims = val.shape
                nlayers = dims[2]

        return nlayers

    def getTimeSeriesFromPoint(j, i, HDFgroup):

        tgroup = '/VARIABLES'
        tsubgroup = HDFgroup

        group = fh5[tgroup]

        for subgroup in group:  # iterate over subgroups
            if tsubgroup in subgroup:
                # print 'found required subgroup: ' , subgroup
                val = group[subgroup + '/' + 'value']

                # inputs[nrows:ncols:nlayers:time]
                data = val[j, i, :, :]
                # no value set to nan
                data[data == -1.0] = np.nan

        return data

    def getmoisturetimes(HDFgroup):

        tgroup = '/VARIABLES'
        tsubgroup = HDFgroup

        group = fh5[tgroup]

        for subgroup in group:  # iterate over subgroups
            if tsubgroup in subgroup:
                # print 'found required subgroup: ' , subgroup
                times = group[subgroup + '/' + 'time']
                moisturetimes = times[:]

        return moisturetimes

    def timeseriesplot(moisturetimes, depth, data, ntimes, Npoints, row, col, elevation, minth, maxth, userspecNlayers):
        # points = 0
        # while points < Npoints:
        def plot(point):
            if elevation[point] != -1:
                plotlabel = np.empty(ntimes, dtype=object)
                plt.figure(figsize=[12.0, 5.0], dpi=300)
                plt.subplots_adjust(bottom=0.1, right=0.75)
                ax = plt.subplot(1, 1, 1)
                ax.set_ylabel('Depth(m)')
                ax.set_xlabel('Soil moisture content')

                time = 1
                while time < ntimes:
                    plotlabel[time] = 'Time=' + str(int(moisturetimes[time])) + ' hours'
                    ax.plot(data[0:userspecNlayers - 1, time, point], depth[0:userspecNlayers - 1],
                            label=plotlabel[time])
                    time += 1
                axes = plt.gca()
                axes.set_xlim([minth, maxth])
                plt.gca().invert_yaxis()
                legend = ax.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0., prop={'size': 8})
                plt.title(
                    "Profile. " + 'Col=' + str(int(col[point])) + ' Row=' + str(int(row[point])) + ' Elev= %7.2f m' %
                    elevation[point])

                if out_dir:
                    if not os.path.exists(out_dir):
                        os.mkdir(out_dir)
                    plt.savefig(out_dir + '/' + 'profile' + str(point) + '.png')
                plt.show()
                # time += 1

        if interactive:
            return interact(plot, point=IntSlider(value=point,
                                                 min=0,
                                                 max=Npoints-1,
                                                 step=1,
                                                 continuous_update=False,
                                                 description=' ',
                                                 readout_format='',
                                                 layout=Layout(width='100%')),
                            )
        else:
            plot(point)

            # points += 1

        # return

    def minmaxmoisture(data, ntimes, Npoints):
        minth = 99999.0
        maxth = -99999.0
        minth = min(minth, np.nanmin(data[:, 1:ntimes, :]))
        maxth = max(maxth, np.nanmax(data[:, 1:ntimes, :]))

        return minth, maxth

    def getTimeSeriesNpoints(locations):
        # skip over the headers
        locations.readline()
        i = 0
        for line in locations:
            line.rstrip().split(",")
            i += 1
        return i

    def getTimeSeriesLocation(locations, Npoints):
        # skip over the headers
        locations.readline()
        i = 0
        x = np.zeros(shape=(Npoints))
        y = np.zeros(shape=(Npoints))
        for line in locations:
            x[i], y[i] = line.rstrip().split(",")
            i += 1
        return x, y

    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

    # # make folder for graphs and outputs
    # if not os.path.exists(out_dir):
    #     os.mkdir(out_dir)

    # number of points (Npoints) in time series file
    locations = open(timeseries_locations, "r")
    Npoints = getTimeSeriesNpoints(locations)

    # go back to start of file and get locations
    locations.seek(0)
    col, row = getTimeSeriesLocation(locations, Npoints)
    fh5 = h5py.File(h5_file, 'r')
    # dem is row number(from top), column number
    dem, nrows, ncols = getElevations()

    # elevations correspond to the row number and column number in hdf file
    elevation = np.zeros(shape=(Npoints))
    i = 0
    while i < Npoints:

        elevation[i] = dem[int(row[i]), int(col[i])]
        # if elevation[i] == -1:
        #     print 'column ', int(col[i]), ' row ', int(row[i]), ' outside of catchment'

        i += 1

    # get times of output. ntimes is the final time
    moisturetimes = getmoisturetimes(hdf_group)
    dimstime = moisturetimes.shape
    ntimes = dimstime[0]

    # get the number of layers for which output is defined. This is specified in the visulisation plan file and might not be all the layers
    nlayers = FindNumberofLayers(hdf_group)
    n_layers = min(nlayers, n_layers)

    # get the time series inputs
    data = np.zeros(shape=(nlayers, ntimes, Npoints))
    i = 0
    while i < Npoints:
        data[:, :, i] = getTimeSeriesFromPoint(row[i], col[i], hdf_group)
        i += 1

    # get the cell sizes of the layers. consider all the cells so that one is within the catchment
    thickness = np.zeros(shape=(nlayers))
    actThickness = np.zeros(shape=(nlayers))
    i = 0
    j = 0
    while i < Npoints:
        thickness[:] = getCellSziesFromPoint(row[i], col[i], nlayers)
        while j < nlayers:
            actThickness[j] = max(actThickness[j], thickness[j])
            j += 1
        i += 1

    # calculate depths from thicknesses
    depth = np.zeros(nlayers)
    i = 1
    depth[0] = actThickness[0] / 2.0
    while i < nlayers:
        depth[i] = depth[i - 1] + actThickness[i] / 2.0 + actThickness[i - 1] / 2.0
        i += 1

    # get min and max theta
    minth, maxth = minmaxmoisture(data, ntimes, Npoints)

    # time series plots.
    # print 'Profile plot'
    timeseriesplot(moisturetimes, depth, data, ntimes, Npoints, row, col, elevation, minth, maxth, n_layers)



