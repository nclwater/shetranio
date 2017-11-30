import matplotlib.pyplot as plt
import numpy as np
import h5py
from ..hdf import Hdf
from..dem import Dem
import os
import datetime
from matplotlib import cm
from mpl_toolkits.mplot3d import Axes3D
from ipywidgets import interact, IntSlider, Layout, SelectionSlider


def points(h5_file, timeseries_locations, start_date, out_dir=None, dem=None):
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

    # Read in the time series from the HDF
    data = np.zeros(shape=(number_of_points, times.shape[0]))
    for i in range(number_of_points):
        point_data = h5.ph_depth.values[row[i], col[i], :]
        point_data = [round(m, 2) for m in point_data]
        data[i, :] = point_data

    # Create the plot
    plt.figure(figsize=[12.0, 5.0], dpi=300)
    plt.subplots_adjust(bottom=0.2, right=0.75)
    ax = plt.subplot(1, 1, 1)

    # Check if each elevation is inside the DEM and if so add to plot
    for i in range(number_of_points):
        elevation = elevations[int(row[i]), int(col[i])]
        if elevation == -1:
            print 'column', int(col[i]), 'row', int(row[i]), 'is outside of catchment'
        else:
            if dem is not None:
                label = str(int(dem.x_coordinates[int(col[i])])) + ',' + str(int(dem.y_coordinates[int(row[i])])) +\
                    ' Elev:%.2f m' % elevation
            else:
                label = 'Col=' + str(int(col[i])) + ' Row=' + str(int(row[i])) + ' Elev= %7.2f m' % elevation[i]
            ax.plot(times, data[i, :], label=label)

    ax.set_ylabel('Water Table Depth (m below ground)')

    # Adjust plot settings
    plt.xticks(rotation=70)
    plt.gca().invert_yaxis()
    ax.legend(
        bbox_to_anchor=(0.5, -0.2),
        loc=9,
        ncol=2,
    )

    # Save plot if out_dir set
    if out_dir:
        if not os.path.exists(out_dir):
            os.mkdir(out_dir)
        plt.savefig(os.path.join(out_dir,'watertable-timeseries.png'))

    plt.show()

def area(h5_file, dem=None, out_dir=None, interactive=True, timestep=0, time_interval=1, video=False, use_elevation=False):
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
    plt.clf()
    h5 = Hdf(h5_file)

    elevations = h5.surface_elevation.square[1:-1, 1:-1]
    nrows, ncols = elevations.shape

    grid_size = np.nanmax(h5.grid_dxy)

    psltimes = h5.ph_depth.times
    dimstime = psltimes.shape
    ntimes = dimstime[0]
    assert 0 <= timestep < ntimes, 'Timestep must be between 0 and %s' % (int(ntimes)-1)

    minpsl = 99999.0
    maxpsl = -99999.0
    for i in range(0, ntimes, time_interval):

        h5datapsl2d = h5.ph_depth.values[1:-1, 1:-1, i]
        h5datapsl2d[h5datapsl2d == -1.0] = np.nan
        if use_elevation:
            h5datapsl2d = elevations - h5datapsl2d
        minpsl = min(minpsl, np.nanmin(h5datapsl2d))
        maxpsl = max(maxpsl, np.nanmax(h5datapsl2d))

    def plot(current_time):
        fig = plt.figure(figsize=[12.0, 5.0], dpi=300)
        h5datapsl2d = h5.ph_depth.values[1:-1, 1:-1, current_time]
        h5datapsl2d[h5datapsl2d == -1.0] = np.nan
        if use_elevation:
            h5datapsl2d = elevations - h5datapsl2d

        ax = plt.subplot(1, 1, 1)
        ax.axis([0, grid_size * ncols, 0, grid_size * nrows])
        ax.set_xlabel('Distance(m)')
        ax.set_ylabel('Distance(m)')
        ax = plt.subplot(1, 1, 1)
        if dem is not None:
            grid = Dem(dem)
            ax.set_xlim(grid.x_coordinates.min(), grid.x_coordinates.max())
            ax.set_ylim(grid.y_coordinates.min(), grid.y_coordinates.max())
            ax.set_xlabel('OSGB X Coordinate (m)')
            ax.set_ylabel('OSGB Y Coordinate (m)')
            cax = ax.imshow(h5datapsl2d,
                            extent=[grid.x_coordinates.min(),
                                    grid.x_coordinates.max(),
                                    grid.y_coordinates.min(),
                                    grid.y_coordinates.max()],
                            interpolation='none',
                            vmin=minpsl, vmax=maxpsl, cmap='Blues_r')
        else:
            cax = ax.imshow(h5datapsl2d,
                            extent=[0,
                                    ncols*grid_size,
                                    0,
                                    nrows*grid_size],
                            interpolation='none',
                            vmin=minpsl, vmax=maxpsl, cmap='Blues_r'
                            )

        fig.colorbar(cax, fraction=0.04, pad=0.10)

        plt.title("Water Table depth - meters below ground. Time = %7.0f hours" % psltimes[current_time],
                     # fontsize=14,
                     # fontweight='bold'
                     )
        if out_dir:
            if not os.path.exists(out_dir):
                os.mkdir(out_dir)
            plt.savefig(out_dir + '/' + 'WaterTable-2d-time' + str(current_time) + '.png')
        plt.show()

    if interactive and not video:
        interact(plot, current_time=SelectionSlider(
        options = [("%7.0f hours" % psltimes[i],i) for i in range(ntimes)],
         continuous_update=False,
         description=' ',
         readout_format='',
         layout=Layout(width='100%')))

    elif video:
        from matplotlib import animation, rc
        from IPython.display import HTML

        rc('animation', html='html5')
        fig = plt.figure(figsize=[12, 5])


        ax = plt.subplot(1, 1, 1)
        ax.axis([0, grid_size * ncols, 0, grid_size * nrows])
        ax.set_xlabel('Distance(m)')
        ax.set_ylabel('Distance(m)')
        ax = plt.subplot(1, 1, 1)
        if dem is not None:
            grid = Dem(dem)
            ax.set_xlim(grid.x_coordinates.min(), grid.x_coordinates.max())
            ax.set_ylim(grid.y_coordinates.min(), grid.y_coordinates.max())
            ax.set_xlabel('OSGB X Coordinate (m)')
            ax.set_ylabel('OSGB Y Coordinate (m)')

            cax = ax.imshow(np.zeros((10,10)),
                            extent=[grid.x_coordinates.min(),
                                    grid.x_coordinates.max(),
                                    grid.y_coordinates.min(),
                                    grid.y_coordinates.max()],
                            interpolation='none',
                            vmin=minpsl, vmax=maxpsl, cmap='Blues_r')
        else:
            cax = ax.imshow(np.zeros([10,10]), extent=[0,
                                        ncols * grid_size,
                                        0,
                                        nrows * grid_size],
                                interpolation='none',
                                vmin=minpsl, vmax=maxpsl, cmap='Blues_r')
        fig.colorbar(cax, fraction=0.04, pad=0.10)

        def plot(time):
            h5datapsl2d = h5.ph_depth.values[1:-1, 1:-1, time]
            h5datapsl2d[h5datapsl2d == -1.0] = np.nan
            if use_elevation:
                h5datapsl2d = elevations - h5datapsl2d
            cax.set_data(h5datapsl2d)



            plt.title("Water Table depth - meters below ground. Time = %7.0f hours" % psltimes[time],
                      # fontsize=14,
                      # fontweight='bold'
                      )
            plt.close()
            return cax,

        # def init():
        #     # print(lines)
        #     for i in range(len(lines)):
        #         lines[i].set_data([], [])
        #     return lines

        anim = animation.FuncAnimation(fig, plot,
                                       # init_func=init,
                                       frames=ntimes, interval=200, blit=True)
        return HTML(anim.to_html5_video())

    else:
        plot(timestep)

def area3d(h5_file, hdf_group, grid=None, out_dir=None, interactive=True, azi=0):
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

    def get_grid():
        with open(grid) as f:
            lines = [f.readline() for _ in range(4)]

        geo = {'ncols':lines[0].split()[1],
               'nrows':lines[1].split()[1],
               'xll':lines[2].split()[1],
               'yll':lines[3].split()[1]}

        return geo

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



        # repeated to produce a plot for each direction (azi)
        # print '3d plot'
        # starting direction
        # azi = 0
        # while azi < 360:
        def plot(azi):
            fig = plt.figure(figsize=[12.0, 5.0], dpi=300)


            # ax = plt.subplot(1, 1, 1, projection='3d')
            ax = Axes3D(fig)
            ax.set_xlabel('Distance(m)')
            ax.set_ylabel('Distance(m)')
            ax.set_zlabel('Elevation(m)')
            X = np.arange(0, (ncols - 1) * GridSize, GridSize)
            Y = np.arange(0, (nrows - 1) * GridSize, GridSize)
            if grid is not None:
                g = get_grid()
                X += int(g['xll'])
                Y += int(g['yll'])
                ax.set_xlabel('OSGB X Coordinate (m)')
                ax.set_ylabel('OSGB Y Coordinate (m)')
            X, Y = np.meshgrid(X, Y)
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