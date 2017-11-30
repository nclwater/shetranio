import matplotlib.pyplot as plt
import numpy as np
from ..hdf import Hdf
from ..dem import Dem
import os
from ipywidgets import interact, IntSlider, Layout, Dropdown, SelectionSlider


def points(h5_file, timeseries_locations, selected_layers, dem=None, out_dir=None, interactive=True, timestep=0, video=False):
    """Using HDF file produces soil moisture profile plots of particular points.
            Each figure shows all the points at a particular time.
            There is a separate figure for each time.
            If a DEM is specified, points are read as geo-referenced coordinates

                Args:
                    h5_file (str): Path to the input HDF5 file.
                    timeseries_locations (str): Points that you want time series inputs for.
                    selected_layers (int): Number of soil layers needing output for. Starting from the top.
                    dem (str): Path to an ASCII text file of the input DEM.
                    out_dir (str, optional): Folder to save an output PNG into. Defaults to None.
                    interactive (bool, optional): Whether to return an ipython slider with the plot. Defaults to True.
                    timestep (int, optional): The index of the timestep to create the plot at. Defaults to 0.

                Returns:
                     None

    """

    h5 = Hdf(h5_file)

    with open(timeseries_locations) as f:
        # skip over the headers
        f.readline()
        x = []
        y = []
        for line in f:
            x_val, y_val = line.rstrip().split(",")
            x.append(int(x_val))
            y.append(int(y_val))
        col = np.array(x)
        row = np.array(y)

    number_of_points = len(col)

    if dem is not None:
        dem = Dem(dem)
        for i, (x, y)  in enumerate(zip(col, row)):
            col[i], row[i] = dem.get_index(x, y)

    elevations = h5.surface_elevation.square[1:- 1, 1:- 1]

    elevation = np.zeros(shape=(number_of_points))
    for i in range(number_of_points):

        elevation[i] = elevations[int(row[i]), int(col[i])]

    moisture_times = h5.theta.times
    number_of_time_steps = h5.theta.times.shape[0]
    assert 0 <= timestep < number_of_time_steps, 'Timestep must be between 0 and %s' % (int(number_of_time_steps) - 1)

    # get the number of layers for which output is defined. This is specified in the visulisation plan file and might not be all the layers

    all_layers = h5.theta.values.shape[2]

    selected_layers = min(all_layers, selected_layers)

    assert selected_layers > 1, 'Need more than 1 layer to plot soil moisture'

    # get the time series inputs
    data = np.zeros(shape=(all_layers, number_of_time_steps, number_of_points))

    for i in range(number_of_points):
        point_data = h5.theta.values[row[i], col[i], :, :]
        point_data[point_data==-1] = np.nan
        data[:, :, i] = point_data

    actual_thickness = np.zeros(shape=(all_layers))

    for i in range(number_of_points):

        thickness = h5.vertical_thickness.square[row[i], col[i], :-1]

        for j in range(selected_layers):
            actual_thickness[j] = max(actual_thickness[j], thickness[j])

    # calculate depths from thicknesses
    depth = np.zeros(all_layers)

    depth[0] = actual_thickness[0] / 2.0
    for i in range(1, selected_layers):
        depth[i] = depth[i - 1] + actual_thickness[i] / 2.0 + actual_thickness[i - 1] / 2.0

    # get min and max theta
    min_theta = 99999.0
    max_theta = -99999.0
    min_theta = min(min_theta, np.nanmin(data[:, 1:number_of_time_steps, :]))
    max_theta = max(max_theta, np.nanmax(data[:, 1:number_of_time_steps, :]))

    def plot(time):
        label = np.empty(number_of_points, dtype=object)
        plt.figure(figsize=[12.0, 5.0], dpi=300)
        plt.subplots_adjust(bottom=0.1, right=0.75)
        ax = plt.subplot(1, 1, 1)
        ax.set_ylabel('Depth(m)')
        ax.set_xlabel('Soil moisture content')

        for i in range(number_of_points):
            if elevation[i] != -1:
                if dem is not None:
                    label[i] = str(int(dem.x_coordinates[int(col[i])])) + ',' + str(int(dem.y_coordinates[int(row[i])])) + \
                            ' Elev:%.2f m' % elevation[i]
                else:
                    label[i] = 'Col=' + str(int(col[i])) + ' Row=' + str(
                        int(row[i])) + ' Elev= %7.2f m' % elevation[i]
                ax.plot(data[0:selected_layers - 1, time, i], depth[0:selected_layers - 1],
                        label=label[i])

        axes = plt.gca()
        axes.set_xlim([min_theta, max_theta])
        plt.gca().invert_yaxis()
        ax.legend(
            bbox_to_anchor=(0.5, -0.2),
            loc=9,
            ncol=2,
        )
        plt.title("Profile. Time = %7.0f hours" % moisture_times[time])
        if out_dir:
            if not os.path.exists(out_dir):
                os.mkdir(out_dir)
            plt.savefig(out_dir + '/' + 'profile' + str(time) + '.png')
        plt.show()

    if interactive and not video:
        interact(plot, time=SelectionSlider(
            options = [("%7.0f hours" % moisture_times[i],i) for i in range(number_of_time_steps)],
            continuous_update=False,
            description=' ',
            readout_format='',
            layout=Layout(width='100%')))

    elif video:
        from matplotlib import animation, rc
        from IPython.display import HTML

        rc('animation', html='html5')
        fig = plt.figure(figsize=[12.0, 5.0])
        plt.subplots_adjust(bottom=0.1, right=0.75)
        ax = plt.subplot(1, 1, 1)
        ax.set_ylabel('Depth(m)')
        ax.set_xlabel('Soil moisture content')
        axes = plt.gca()
        axes.set_xlim([min_theta, max_theta])
        axes.set_ylim([min(depth), max(depth)])
        plt.gca().invert_yaxis()

        lines=  []
        for i in range(number_of_points):
            if dem is not None:
                label = str(int(dem.x_coordinates[int(col[i])])) + ',' + str(
                    int(dem.y_coordinates[int(row[i])])) + \
                        ' Elev:%.2f m' % elevation[i]
            else:
                label = 'Col=' + str(int(col[i])) + ' Row=' + str(
                    int(row[i])) + ' Elev= %7.2f m' % elevation[i]
            lines.append(axes.plot([], [], label=label)[0])
            plt.legend(
            )
        print(lines)

        def plot(time):
            plt.title("Profile. Time = %7.0f hours" % moisture_times[time])
            
            for i in range(number_of_points):
                if elevation[i] != -1:
                    lines[i].set_data(data[0:selected_layers - 1, time, i], depth[0:selected_layers - 1])
            plt.close()
            return lines


        def init():
            # print(lines)
            for i in range(len(lines)):
                lines[i].set_data([], [])
            return lines


        anim = animation.FuncAnimation(fig, plot, init_func=init,
                                       frames=number_of_time_steps, interval=200, blit=True)

        return HTML(anim.to_html5_video())


    else:
        plot(timestep)




def times(h5_file, timeseries_locations, selected_layers, dem=None, out_dir=None, interactive=True, point=0):
    """Using HDF file produces soil moisture profile plots of particular points.
                Each figure shows a single points with all times.
                There is a separate figure for each point.

                    Args:
                        h5_file (str): Path to the input HDF5 file.
                        hdf_group (str): Name of HDF file output group.
                        timeseries_locations (str): Points that you want time series inputs for.
                        selected_layers (int): Number of soil layers needing output for. Starting from the top.
                        out_dir (str, optional): Folder to save an output PNG into. Defaults to None.
                        interactive (bool, optional): Whether to return an ipython slider with the plot. Defaults to True.
                        point (int, optional): The index of the point to create the plot at. Defaults to 0.

                    Returns:
                        None

                """

    h5 = Hdf(h5_file)

    with open(timeseries_locations) as f:
        f.readline()
        x = []
        y = []
        for line in f:
            x_val, y_val = line.rstrip().split(",")
            x.append(int(x_val))
            y.append(int(y_val))

    col = np.array(x)
    row = np.array(y)

    if dem is not None:
        dem = Dem(dem)
        for i, (x, y)  in enumerate(zip(col, row)):
            col[i], row[i] = dem.get_index(x, y)

    number_of_points = len(col)

    # dem is row number(from top), column number

    # Shetran adds extra column and row around grid. Only need dem in normal grid
    elevations = h5.surface_elevation.square[1:-1, 1:-1]

    # elevations correspond to the row number and column number in hdf file
    elevation = np.zeros(shape=(number_of_points))
    for i in range(number_of_points):

        elevation[i] = elevations[int(row[i]), int(col[i])]


    # get times of output. ntimes is the final time
    moisture_times = h5.theta.times
    number_of_time_steps = moisture_times.shape[0]

    all_layers = h5.theta.values.shape[2]

    # get the number of layers for which output is defined. This is specified in the visulisation plan file and might not be all the layers
    selected_layers = min(all_layers, selected_layers)

    # get the time series inputs
    data = np.zeros(shape=(all_layers, number_of_time_steps, number_of_points))

    for i in range(number_of_points):
        points_data = h5.theta.values[row[i], col[i], :, :]
        points_data[points_data==-1]=np.nan
        data[:, :, i] = points_data

    # get the cell sizes of the layers. consider all the cells so that one is within the catchment

    actThickness = np.zeros(shape=(all_layers))

    for i in range(number_of_points):
        thickness = h5.vertical_thickness.square[row[i], col[i], :-1]
        for j in range(all_layers):
            actThickness[j] = max(actThickness[j], thickness[j])

    # calculate depths from thicknesses
    depth = np.zeros(all_layers)
    depth[0] = actThickness[0] / 2.0
    for i in range(all_layers):
        depth[i] = depth[i - 1] + actThickness[i] / 2.0 + actThickness[i - 1] / 2.0

    min_theta = 99999.0
    max_theta = -99999.0
    min_theta = min(min_theta, np.nanmin(data[:, 1:number_of_time_steps, :]))
    max_theta = max(max_theta, np.nanmax(data[:, 1:number_of_time_steps, :]))

    def plot(point):

        if elevation[point] != -1:
            plt.figure(figsize=[12.0, 5.0], dpi=300)
            plt.subplots_adjust(bottom=0.1, right=0.75)
            ax = plt.subplot(1, 1, 1)
            ax.set_ylabel('Depth(m)')
            ax.set_xlabel('Soil moisture content')

            for time_step in range(1, number_of_time_steps):
                label = 'Time=' + str(int(moisture_times[time_step])) + ' hours'
                ax.plot(data[0:selected_layers - 1, time_step, point], depth[0:selected_layers - 1],
                        label=label)

            axes = plt.gca()
            axes.set_xlim([min_theta, max_theta])
            plt.gca().invert_yaxis()
            ax.legend(
                bbox_to_anchor=(0.5, -0.2),
                loc=9,
                ncol=3,
            )
            if dem is not None:
                plt.title(
                    "Profile. " + str(int(dem.x_coordinates[col[point]])) + ',' + str(int(dem.y_coordinates[row[point]])) + ' Elev= %7.2f m' %
                    elevation[point])
            else:
                plt.title(
                    "Profile. " + 'Col=' + str(int(col[point])) + ' Row=' + str(int(row[point])) + ' Elev= %7.2f m' %
                    elevation[point])

            if out_dir:
                if not os.path.exists(out_dir):
                    os.mkdir(out_dir)
                plt.savefig(out_dir + '/' + 'profile' + str(point) + '.png')
            plt.show()
        else:
            print("Point. " + str(int(dem.x_coordinates[col[point]])) + ',' + str(int(dem.y_coordinates[row[point]]))
                  +' is not in the DEM')

    if interactive:
        interact(plot,point=Dropdown(
            options = dict([(str(int(dem.x_coordinates[col[i]])) +',' + str(int(dem.y_coordinates[row[i]])), i)
                            for i in range(number_of_points)]),
            description='location:',
            continuous_update=False,
            readout_format='',
        ))
    else:
        plot(point)



