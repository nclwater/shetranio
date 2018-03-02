import matplotlib.pyplot as plt
import numpy as np
from ..hdf import Hdf
from ..dem import Dem
import os
from ipywidgets import interact, IntSlider, Layout, Dropdown, SelectionSlider


def points(h5_file, timeseries_locations, selected_layers, dem=None, out_dir=None, interactive=True, timestep=1, video=False):
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
        col = x
        row = y

    number_of_points = len(col)
    col_index = np.array(col)
    row_index = np.array(row)

    if dem is not None:
        dem = Dem(dem)
        for i, (x, y)  in enumerate(zip(col_index, row_index)):
            col_index[i], row_index[i] = dem.get_index(x, y)

    elevations = h5.surface_elevation.square[1:- 1, 1:- 1]

    elevation = np.zeros(shape=(number_of_points))
    for i in range(number_of_points):

        elevation[i] = elevations[int(row_index[i]), int(col_index[i])]

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
        point_data = h5.theta.values[row_index[i], col_index[i], :, :]
        point_data[point_data==-1] = np.nan
        data[:, :, i] = point_data

    actual_thickness = np.zeros(shape=(all_layers))

    for i in range(number_of_points):

        thickness = h5.vertical_thickness.square[row_index[i], col_index[i], :-1]

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
        plt.figure(figsize=[12.0, 5.0])
        plt.subplots_adjust(bottom=0.1, right=0.75)
        ax = plt.subplot(1, 1, 1)
        ax.set_ylabel('Depth(m)')
        ax.set_xlabel('Soil moisture content')

        for i in range(number_of_points):
            if elevation[i] != -1:
                if dem is not None:
                    label[i] = str(int(dem.x_coordinates[int(col_index[i])])) + ',' + str(int(dem.y_coordinates[int(row_index[i])])) + \
                            ' Elev:%.2f m' % elevation[i]
                else:
                    label[i] = 'Col=' + str(int(col_index[i])) + ' Row=' + str(
                        int(row_index[i])) + ' Elev= %7.2f m' % elevation[i]
                ax.plot(data[0:selected_layers - 1, time, i], depth[0:selected_layers - 1],
                        label=label[i])
            else:
                print('Row {} Col {} not within domain'.format(row[i], col[i]))

        ax.set_xlim([min_theta, max_theta])
        plt.gca().invert_yaxis()
        ax.legend()
        plt.title("Profile. Time = %7.0f hours" % moisture_times[time])
        if out_dir:
            if not os.path.exists(out_dir):
                os.mkdir(out_dir)
            plt.savefig(os.path.join(out_dir ,'points-profile-time-{}.png'.format(time)))

            with open(os.path.join(out_dir ,'points-profile-time-{}.csv'.format(time)), 'w') as f:
                headers = []
                point_moisture = []

                for idx in range(number_of_points):
                    if elevation[idx] != -1:
                        headers.append('point_{}_moisture'.format(idx))
                        point_moisture.append(data[0:selected_layers - 1, time, idx])

                point_depths = depth[0:selected_layers - 1]

                f.write(','.join(['depth'] + headers) + '\n')
                for idx in range(len(point_depths)):
                    f.write(str(point_depths[idx]))
                    for point in point_moisture:
                        f.write(',' + str(point[idx]))
                    f.write('\n')

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
        title = plt.title("Profile. Time = 0 hours")

        lines=  []
        for i in range(number_of_points):
            if dem is not None:
                label = str(int(dem.x_coordinates[int(col_index[i])])) + ',' + str(
                    int(dem.y_coordinates[int(row_index[i])])) + \
                        ' Elev:%.2f m' % elevation[i]
            else:
                label = 'Col=' + str(int(col_index[i])) + ' Row=' + str(
                    int(row_index[i])) + ' Elev= %7.2f m' % elevation[i]
            lines.append(axes.plot([], [], label=label)[0])
            plt.legend(
            )
        print(lines)

        def plot(time):
            title.set_text("Profile. Time = %7.0f hours" % moisture_times[time])
            
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




def times(h5_file, timeseries_locations, selected_number_of_layers, dem=None, out_dir=None, interactive=True, point=0):
    """Using HDF file produces soil moisture profile plots of particular points.
                Each figure shows a single points with all times.
                There is a separate figure for each point.

                    Args:
                        h5_file (str): Path to the input HDF5 file.
                        hdf_group (str): Name of HDF file output group.
                        timeseries_locations (str): Points that you want time series inputs for.
                        selected_number_of_layers (int): Number of soil layers needing output for. Starting from the top.
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
        for point_index, (x, y)  in enumerate(zip(col, row)):
            col[point_index], row[point_index] = dem.get_index(x, y)

    number_of_points = len(col)

    # dem is row number(from top), column number

    # Shetran adds extra column and row around grid. Only need dem in normal grid
    elevations = h5.surface_elevation.square[1:-1, 1:-1]

    # elevations correspond to the row number and column number in hdf file
    elevation = np.zeros(shape=number_of_points)
    for point_index in range(number_of_points):

        elevation[point_index] = elevations[int(row[point_index]), int(col[point_index])]


    # get times of output
    moisture_times = h5.theta.times
    number_of_time_steps = moisture_times.shape[0]

    number_of_hdf_layers = h5.theta.values.shape[2]

    # get the number of layers for which output is defined. This is specified in the visulisation plan file and might not be all the layers
    selected_number_of_layers = min(number_of_hdf_layers, selected_number_of_layers)
    assert selected_number_of_layers > 1, 'Need more than 1 layer to plot soil moisture'

    # get the time series inputs
    soil_moisture = np.zeros(shape=(number_of_hdf_layers, number_of_time_steps, number_of_points))

    for point_index in range(number_of_points):
        points_data = h5.theta.values[row[point_index], col[point_index], :, :]
        points_data[points_data==-1]=np.nan
        soil_moisture[:, :, point_index] = points_data

    # get the cell sizes of the layers. consider all the cells so that one is within the catchment
    layer_thicknesses = np.zeros(shape=number_of_hdf_layers)

    for point_index in range(number_of_points):
        thickness = h5.vertical_thickness.square[row[point_index], col[point_index], :]
        for j in range(number_of_hdf_layers):
            layer_thicknesses[j] = max(layer_thicknesses[j], thickness[j])

    # calculate depths from thicknesses
    depth = np.zeros(number_of_hdf_layers)
    depth[0] = layer_thicknesses[0] / 2.0
    for layer_index in range(1, number_of_hdf_layers):
        depth[layer_index] = depth[layer_index - 1] + layer_thicknesses[layer_index] / 2.0 + layer_thicknesses[layer_index - 1] / 2.0

    min_theta = 99999.0
    max_theta = -99999.0
    min_theta = min(min_theta, np.nanmin(soil_moisture[:, 1:number_of_time_steps, :]))
    max_theta = max(max_theta, np.nanmax(soil_moisture[:, 1:number_of_time_steps, :]))

    def plot(point):

        if elevation[point] != -1:
            plt.figure(figsize=[12.0, 5.0])
            plt.subplots_adjust(bottom=0.1, right=0.75)
            ax = plt.subplot(1, 1, 1)
            ax.set_ylabel('Depth(m)')
            ax.set_xlabel('Soil moisture content')

            for time_step in range(1, number_of_time_steps):
                label = 'Time=' + str(int(moisture_times[time_step])) + ' hours'
                ax.plot(soil_moisture[0:selected_number_of_layers - 1, time_step, point], depth[0:selected_number_of_layers - 1],
                        label=label)

            axes = plt.gca()
            axes.set_xlim([min_theta, max_theta])
            plt.gca().invert_yaxis()
            ax.legend()
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
                plt.savefig(os.path.join(out_dir, 'times-profile-point-{}.png'.format(point)))


                with open(os.path.join(out_dir, 'times-profile-point-{}.csv'.format(point)), 'w') as f:
                    headers = []
                    time_moisture = []


                    for time_step in range(1, number_of_time_steps):
                        headers.append(str(int(moisture_times[time_step])) + '_hours')
                        time_moisture.append(soil_moisture[0:selected_number_of_layers - 1, time_step, point])

                    point_depths = depth[0:selected_number_of_layers - 1]

                    f.write(','.join(['depth'] + headers) + '\n')
                    for idx in range(len(point_depths)):
                        f.write(str(point_depths[idx]))
                        for time in time_moisture:
                            f.write(',' + str(time[idx]))
                        f.write('\n')

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



