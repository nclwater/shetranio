import matplotlib.pyplot as plt
import numpy as np
import h5py
import os
import datetime
from matplotlib import cm
from mpl_toolkits.mplot3d import Axes3D
from ipywidgets import interact, IntSlider, Layout


def plot(h5_file, hdf_group, timeseries_locations, start_date, out_dir=None):
    """Using HDF file, produces Time Series of phreatic surface depth at timeseriesLocations

            Args:
                h5_file (str): Path to the input HDF5 file.
                hdf_group (str): Name of HDF file output group.
                timeseries_locations (str): Path to locations text file.
                start_date (datetime.datetime): Datetime object set to start of simulation period.
                out_dir (str, optional): Folder to save an output PNG into. Defaults to None.

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


    def getTimeSeriesFromPoint(j, i, HDFgroup):
        tgroup = '/VARIABLES'
        tsubgroup = HDFgroup

        group = fh5[tgroup]

        for subgroup in group:  # iterate over subgroups
            if tsubgroup in subgroup:
                # print 'found required subgroup: ' , subgroup
                val = group[subgroup + '/' + 'value']

                # inputs[nrows:ncols:time] ie [j,i,:]
                data = val[j, i, :]

        data = [round(m, 2) for m in data]
        return data


    def getpsltimes(HDFgroup):
        tgroup = '/VARIABLES'
        tsubgroup = HDFgroup

        group = fh5[tgroup]

        for subgroup in group:  # iterate over subgroups
            if tsubgroup in subgroup:
                # print 'found required subgroup: ' , subgroup
                times = group[subgroup + '/' + 'time']
                psltimes = times[:]

        return psltimes


    def timeseriesplot(psltimes, data, Npoints, row, col, elevation):
        plotlabel = np.empty(Npoints, dtype=object)
        fig = plt.figure(figsize=[12.0, 5.0], dpi=300)
        plt.subplots_adjust(bottom=0.2, right=0.75)
        ax = plt.subplot(1, 1, 1)
        i = 0
        while i < Npoints:
            if elevation[i] != -1:
                plotlabel[i] = 'Col=' + str(int(col[i])) + ' Row=' + str(int(row[i])) + ' Elev= %7.2f m' % elevation[i]
                # plot m below ground
                ax.plot(psltimes, data[i, :], label=plotlabel[i])
                # plot absolute elevation
                # ax.plot(psltimes,elevation[i]-inputs[i,:],label=plotlabel[i])
            i += 1
        # plot m below ground
        ax.set_ylabel('Water Table Depth (m below ground)')
        # plot absolute elevation
        # ax.set_ylabel('Phreatic Surface Level (m ASl)')
        plt.xticks(rotation=70)
        plt.gca().invert_yaxis()
        ax.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0., prop={'size': 8})
        plt.savefig(out_dir + '/' + 'watertable-timeseries.png')
        if out_dir:
            if not os.path.exists(out_dir):
                os.mkdir(out_dir)
            plt.savefig(os.path.join(out_dir,'watertable-timeseries.png'))

        plt.show()


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

    # number of points (Npoints) in tuime series file
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
    psltimes = getpsltimes(hdf_group)
    dimstime = psltimes.shape
    ntimes = dimstime[0]

    # setup a datetime array. there must be a better way than this
    datetimes = np.array([start_date + datetime.timedelta(hours=i) for i in xrange(ntimes)])
    i = 0
    while i < ntimes:
        datetimes[i] = start_date + datetime.timedelta(hours=int(psltimes[i]))
        i += 1

    # get the time series inputs
    data = np.zeros(shape=(Npoints, ntimes))
    i = 0
    while i < Npoints:
        data[i, :] = getTimeSeriesFromPoint(row[i], col[i], hdf_group)
        i += 1

    # time series plots.
    # print 'time series plot'
    timeseriesplot(datetimes, data, Npoints, row, col, elevation)

def plot2d(h5_file, hdf_group, out_dir=None, interactive=True, timestep=0, time_interval=1):
    """Using HDF file, produces 2d plots of phreatic surface depth at regular timesteps

        Args:
            h5_file (str): Path to the input HDF5 file.
            hdf_group (str): Name of HDF file output group.
            out_dir (str, optional): Folder to save an output PNG into. Defaults to None.
            interactive (bool, optional): Whether to return an ipython slider with the plot. Defaults to True.
            timestep (int, optional): The index of the timestep to create the plot at. Defaults to 0.
            time_interval (int, optional): Number of timesteps between plots. Defaults to 1.

        Returns:
            None

    """

    # assume grid size is the same everywhere (this is not necessarily true but is usual)
    def getGridSize():

        tgroup = '/CONSTANTS'
        tsubgroup = 'grid_dxy'

        group = fh5[tgroup]
        # print group

        for subgroup in group:  # iterate over subgroups
            # print subgroup
            if tsubgroup in subgroup:
                # print 'found required subgroup: ' , subgroup

                val = group[subgroup]
                Gridsize = np.nanmax(val)
                # print Gridsize

        return Gridsize

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
                dem = val[1:nrows, 1:ncols, 0]

        return np.array(dem), nrows, ncols

    def getpsl(t, nrows, ncols, HDFgroup):

        tgroup = '/VARIABLES'
        tsubgroup = HDFgroup

        group = fh5[tgroup]

        for subgroup in group:  # iterate over subgroups
            if tsubgroup in subgroup:
                # print 'found required subgroup: ' , subgroup
                val = group[subgroup + '/' + 'value']

                # inputs[nrows:ncols:time] ie [j,i,:]
                data = val[1:nrows, 1:ncols, t]

        return data

    def getpsltimes(HDFgroup):

        tgroup = '/VARIABLES'
        tsubgroup = HDFgroup

        group = fh5[tgroup]

        for subgroup in group:  # iterate over subgroups
            if tsubgroup in subgroup:
                # print 'found required subgroup: ' , subgroup
                times = group[subgroup + '/' + 'time']
                psltimes = times[:]

        return psltimes

    def TwoDPlot(ntimes, nrows, ncols, minpsl, maxpsl, GridSize, HDFgroup):
        # while time < ntimes:

        def plot(current_time):
            fig = plt.figure(figsize=[12.0, 5.0], dpi=300)
            h5datapsl2d = getpsl(current_time, nrows, ncols, HDFgroup)
            h5datapsl2d[h5datapsl2d == -1.0] = np.nan

            ax = plt.subplot(1, 1, 1)
            ax.axis([0, GridSize * ncols, 0, GridSize * nrows])
            ax.set_xlabel('Distance(m)')
            ax.set_ylabel('Distance(m)')
            cax = ax.imshow(h5datapsl2d, extent=[0, GridSize * ncols, 0, GridSize * nrows], interpolation='none',
                            vmin=minpsl, vmax=maxpsl, cmap='Blues_r')
            # cbar = fig.colorbar(cax,ticks=[-1,0,1,2],fraction=0.04, pad=0.10)
            fig.colorbar(cax, fraction=0.04, pad=0.10)
            # plt.subplots_adjust(wspace=0.4)

            plt.title("Water Table depth - meters below ground. Time = %7.0f hours" % psltimes[current_time],
                         # fontsize=14,
                         # fontweight='bold'
                         )
            if out_dir:
                if not os.path.exists(out_dir):
                    os.mkdir(out_dir)
                plt.savefig(out_dir + '/' + 'WaterTable-2d-time' + str(current_time) + '.png')
            plt.show()

            # time += timeinterval
        if interactive:
            interact(plot, current_time=IntSlider(value=timestep,
                                                         min=0,
                                                         max=ntimes-1,
                                                         step=time_interval,
                                                         continuous_update=False,
                                                         description=' ',
                                                         readout_format='',
                                                         layout=Layout(width='100%')),
                            )
        else:
            plot(timestep)

    def maxminpsl(nrows, ncols, ntimes, timeinterval):
        minpsl = 99999.0
        maxpsl = -99999.0
        time = 0
        while time < ntimes:
            h5datapsl2d = getpsl(time, nrows, ncols, hdf_group)
            h5datapsl2d[h5datapsl2d == -1.0] = np.nan
            minpsl = min(minpsl, np.nanmin(h5datapsl2d))
            maxpsl = max(maxpsl, np.nanmax(h5datapsl2d))
            # print minpsl,maxpsl

            time += timeinterval
        return minpsl, maxpsl

    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


    fh5 = h5py.File(h5_file, 'r')
    dem, nrows, ncols = getElevations()

    GridSize = getGridSize()

    # get times of output. ntimes is the final time
    psltimes = getpsltimes(hdf_group)
    dimstime = psltimes.shape
    ntimes = dimstime[0]
    assert 0 <= timestep < ntimes, 'Timestep must be between 0 and %s' % (int(ntimes)-1)

    # obtain max and min psl
    minpsl, maxpsl = maxminpsl(nrows, ncols, ntimes, time_interval)

    # 2d plots. The numbers produced depend on the time interval
    # print '2d plot'
    return TwoDPlot(ntimes, nrows, ncols, minpsl, maxpsl, GridSize, hdf_group)

def plot3d(h5_file, hdf_group, out_dir=None, interactive=True, azi=0):
    """Using HDF file, produces 3d plots of water table or phreatic surface depth.
        The face colour corresponds to the phreatic depth.
        By default it is produced at the final timestep (ntimes) with views every 10 degrees.

            Args:
                h5_file (str): Path to the input HDF5 file.
                hdf_group (str): Name of HDF file output group.
                out_dir (str, optional): Folder to save an output PNG into. Defaults to None.
                interactive (bool, optional): Whether to return an ipython slider with the plot. Defaults to True.
                azi (int, optional): The azimuth used to create the plot. Defaults to 0.

            Returns:
                None

     """
    assert 0<=azi<=360, 'Azimuth must be between 0 and 360'

    # assume grid size is the same everywhere (this is not necessarily true but is usual)
    def getGridSize():

        tgroup = '/CONSTANTS'
        tsubgroup = 'grid_dxy'

        group = fh5[tgroup]
        # print group

        for subgroup in group:  # iterate over subgroups
            # print subgroup
            if tsubgroup in subgroup:
                # print 'found required subgroup: ' , subgroup

                val = group[subgroup]
                Gridsize = np.nanmax(val)
                # print Gridsize

        return Gridsize

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
                dem = val[1:nrows, 1:ncols, 0]

        return np.array(dem), nrows, ncols

    def getpsl(t, nrows, ncols, HDFgroup):

        tgroup = '/VARIABLES'
        tsubgroup = HDFgroup

        group = fh5[tgroup]

        for subgroup in group:  # iterate over subgroups
            if tsubgroup in subgroup:
                # print 'found required subgroup: ' , subgroup
                val = group[subgroup + '/' + 'value']

                # inputs[nrows:ncols:time] ie [j,i,:]
                data = val[1:nrows, 1:ncols, t]

        return data

    def getpsltimes(HDFgroup):

        tgroup = '/VARIABLES'
        tsubgroup = HDFgroup

        group = fh5[tgroup]

        for subgroup in group:  # iterate over subgroups
            if tsubgroup in subgroup:
                # print 'found required subgroup: ' , subgroup
                times = group[subgroup + '/' + 'time']
                psltimes = times[:]

        return psltimes

    def ThreeDPlot(ntimes, nrows, ncols, GridSize, mindem, maxdem, dem, HDFgroup, outfilefolder):

        X = np.arange(0, (ncols - 1) * GridSize, GridSize)
        # print X.shape
        # X = np.arange(1,ncols)
        # print X.shape
        Y = np.arange(0, (nrows - 1) * GridSize, GridSize)
        X, Y = np.meshgrid(X, Y)

        # repeated to produce a plot for each direction (azi)
        # print '3d plot'
        # starting direction
        # azi = 0
        # while azi < 360:
        def plot(azi):
            fig = plt.figure(figsize=[12.0, 5.0], dpi=300)

            # ax = plt.subplot(1, 1, 1, projection='3d')
            ax = Axes3D(fig)
            plt.title('Water Table Depth (m below ground)')
            h5datapsl = getpsl(ntimes - 1, nrows, ncols, HDFgroup)
            r1 = h5datapsl / h5datapsl.max()

            # plot phreatic levels (m above ground)
            # r2=dem-h5datapsl
            # r3=r2/np.nanmax(r2)
            # surf = ax.plot_surface(Y, X, dem, rstride=1, cstride=1, facecolors=cm.Blues_r(r3), shade=False)

            surf = ax.plot_surface(Y, X, dem, rstride=1, cstride=1, facecolors=cm.Blues_r(r1), shade=False)
            ax.view_init(elev=20., azim=azi)
            ax.set_zlim(mindem, maxdem)
            ax.set_xlabel('Distance(m)')
            ax.set_ylabel('Distance(m)')
            ax.set_zlabel('Elevation(m)')

            # ax.yaxis.set_major_locator(LinearLocator(4))
            # ax.xaxis.set_major_locator(LinearLocator(4))

            # sets the scale bar. This is a bit of a fiddle
            h5datapsl[h5datapsl == -1.0] = np.nan
            min3dpsl = np.nanmin(h5datapsl)
            max3dpsl = np.nanmax(h5datapsl)
            scale = np.zeros(shape=(nrows - 1, ncols - 1))
            scale[scale == 0.0] = min3dpsl
            scale[0, 0] = max3dpsl
            # m = cm.ScalarMappable(cmap=cm.YlGnBu)
            m = cm.ScalarMappable(cmap=cm.Blues_r)
            m.set_array(scale)
            plt.colorbar(m)
            if out_dir:
                if not os.path.exists(out_dir):
                    os.mkdir(out_dir)
                plt.savefig(outfilefolder + '/' + 'WaterTable-3d-view' + str(azi) + '.png')
            plt.show()
            # azi += 10
            # return
        if interactive:
            interact(plot, azi=IntSlider(value=azi,
                                         min=0,
                                         max=360,
                                         step=10,
                                         continuous_update=False,
                                         description=' ',
                                         readout_format='',
                                         layout=Layout(width='100%')))


    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


    fh5 = h5py.File(h5_file, 'r')
    dem, nrows, ncols = getElevations()

    # sets values outside mask to nan
    dem[dem == -1] = np.nan
    mindem = np.nanmin(dem)
    maxdem = np.nanmax(dem)

    GridSize = getGridSize()

    # get times of output. ntimes is the final time
    psltimes = getpsltimes(hdf_group)
    dimstime = psltimes.shape
    ntimes = dimstime[0]

    # 3D surface plots - by default produced at final time
    # figures produced by default at ntimes (this can be changed)
    return ThreeDPlot(ntimes, nrows, ncols, GridSize, mindem, maxdem, dem, hdf_group, out_dir)