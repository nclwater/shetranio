import os
import shutil
import subprocess
from datetime import *
from run import Run
import numpy as np
import gdal
import gear

import clipper
from library import make_lib_file

rainfall_source = 'GEAR'


def get_temp(pe_id_list, start_date, end_date, temp_time_series_file, max_or_min):
    # calculate start and end line numbers
    start_line_delta = datetime.strptime(start_date, "%Y-%m-%d") - datetime.strptime("01/01/1960", "%d/%m/%Y")
    lines_to_skip = start_line_delta.days
    lines_to_read_delta = datetime.strptime(end_date, "%Y-%m-%d") - datetime.strptime(start_date, "%Y-%m-%d")
    lines_to_read = lines_to_read_delta.days  # this doesn't count the end date... i think this is what SHETRAN wants
    # get time series for each id
    all_grid_squares_time_series_list = []
    for i in range(len(pe_id_list)):
        one_grid_square_time_series_list = [str(pe_id_list[i])]
        time_series_id = int(pe_id_list[i])
        # get numbers of the equivalent file
        if time_series_id == -9999:
            pass
        else:
            if time_series_id % 180 == 0:
                x_coord = 180
                y_coord = int(round(time_series_id / 180, 0))
            else:
                x_coord = time_series_id % 180
                y_coord = int(round(time_series_id / 180, 0)) + 1

            assert isinstance(max_or_min, str)
            temp_file = open("../UKCP09" + max_or_min + "TempTimeSeries/[" + str(x_coord) + "][" + str(
                y_coord) + "]" + max_or_min + "TempTimeSeries.txt", "r")

            for a in range(lines_to_skip):
                temp_file.readline()
            for b in range(lines_to_read):
                temp_val = temp_file.readline().rstrip()
                one_grid_square_time_series_list.append(temp_val)

            temp_file.close()
            all_grid_squares_time_series_list.append(one_grid_square_time_series_list)

    print("writing temp time series data to file")
    for c in range(len(all_grid_squares_time_series_list[0])):
        line_list = []
        for d in range(len(all_grid_squares_time_series_list)):
            line_list.append(str(all_grid_squares_time_series_list[d][c]))
        line = ",".join(line_list)
        if c == 0:
            temp_time_series_file.write(line + "," + start_date + " to " + end_date + "\n")
        else:
            temp_time_series_file.write(line + "\n")


def setup(run: Run):

    directory = "outputs/{}".format(run.gauge_id)
    print("Creating directory...")
    if not os.path.exists(directory):
        os.makedirs(directory)

    if run.upload is not None:
        clipper.create_mask(run)
    else:
        shutil.copy2(run.inputs.mask, run.outputs.mask)

    mask_file = open(run.outputs.mask, "r")

    n_cols_line = mask_file.readline()
    n_cols_list = n_cols_line.rstrip().split()
    n_cols = float(n_cols_list[1])

    n_rows_line = mask_file.readline()
    n_rows_list = n_rows_line.rstrip().split()
    n_rows = float(n_rows_list[1])

    bx_line = mask_file.readline()
    bx_list = bx_line.rstrip().split()
    x_lower_left_corner = float(bx_list[1])

    by_line = mask_file.readline()
    by_list = by_line.rstrip().split()
    y_lower_left_corner = float(by_list[1])

    mask_file.close()

    def extract(in_file, out_file):
        ds = gdal.Open(in_file)

        start_line_number = ds.RasterYSize - y_lower_left_corner / run.resolution_in_metres - n_rows
        start_index_number = x_lower_left_corner / run.resolution_in_metres

        gdal.Translate(out_file, ds, srcWin=[
                start_index_number,
                start_line_number,
                n_cols,
                n_rows],
                       format='AAIGrid')
        del ds
        ds = gdal.Open(out_file)
        unique_values = np.unique(ds.ReadAsArray())
        del ds
        return unique_values

    extract(run.inputs.dem, run.outputs.dem)
    extract(run.inputs.min_dem, run.outputs.min_dem)
    extract(run.inputs.soil, run.outputs.soil)
    extract(run.inputs.veg, run.outputs.veg)
    extract(run.inputs.lakes, run.outputs.lakes)

    pe_output = extract(run.inputs.pe, run.outputs.pe)

    if rainfall_source == 'GEAR':
        gear.extract(run)
    else:
        rain_output = extract(run.inputs.rain, run.outputs.rain)

        unique_rain_ids_list = list(np.sort(rain_output[rain_output != -9999]).astype(str))

        # calculate start and end line numbers
        start_line_delta = datetime.strptime(run.start_date, "%Y-%m-%d") - datetime.strptime("01/01/1958", "%d/%m/%Y")
        lines_to_skip = start_line_delta.days
        lines_to_read_delta = datetime.strptime(run.end_date, "%Y-%m-%d") - datetime.strptime(run.start_date, "%Y-%m-%d")
        lines_to_read = lines_to_read_delta.days  # this doesn't count the end date... i think this is what SHETRAN wants
        # get time series for each id
        all_grid_squares_time_series_list = []
        print(unique_rain_ids_list)
        for i in range(len(unique_rain_ids_list)):
            one_grid_square_time_series_list = [str(unique_rain_ids_list[i])]
            time_series_id = int(unique_rain_ids_list[i])
            # get numbers of the equivalent file
            if time_series_id % 180 == 0:
                x_coord = 180
                y_coord = time_series_id / 180
            else:
                x_coord = time_series_id % 180
                y_coord = int((time_series_id / 180) + 1)

            rain_file = open(
                "../Inputs/UKCP09RainfallTimeSeries/[" + str(x_coord) + "][" + str(y_coord) + "]RainfallTimeSeries.txt",
                "r")

            for a in range(lines_to_skip):
                rain_file.readline()
            for b in range(lines_to_read):
                rain_val = rain_file.readline().rstrip()
                one_grid_square_time_series_list.append(rain_val)

            rain_file.close()
            all_grid_squares_time_series_list.append(one_grid_square_time_series_list)

        print("writing Rain time series data to file")
        with open(run.outputs.rain_timeseries, 'w') as f:
            for c in range(len(all_grid_squares_time_series_list[0])):
                line_list = []
                for d in range(len(all_grid_squares_time_series_list)):
                    line_list.append(str(all_grid_squares_time_series_list[d][c]))
                line = ",".join(line_list)
                if c == 0:
                    f.write(line + "," + run.start_date + " to " + run.end_date + "\n")
                else:
                    f.write(line + "\n")

    unique_p_e_ids_list = np.sort(pe_output[pe_output != -9999]).astype(str)

    new_p_e_time_series = open(run.outputs.pe_timeseries, 'w')

    # calculate start and end line numbers
    start_line_delta = datetime.strptime(run.start_date, "%Y-%m-%d") - datetime.strptime("01/01/1960", "%d/%m/%Y")
    lines_to_skip = start_line_delta.days
    lines_to_read_delta = datetime.strptime(run.end_date, "%Y-%m-%d") - datetime.strptime(run.start_date, "%Y-%m-%d")
    lines_to_read = lines_to_read_delta.days  # this doesn't count the end date... i think this is what SHETRAN wants
    # get time series for each id
    all_grid_squares_time_series_list = []
    for i in range(len(unique_p_e_ids_list)):
        one_grid_square_time_series_list = [str(unique_p_e_ids_list[i])]
        time_series_id = int(unique_p_e_ids_list[i])
        # get numbers of the equivalent file
        if time_series_id % 180 == 0:
            x_coord = 180
            y_coord = time_series_id / 180
        else:
            x_coord = time_series_id % 180
            y_coord = int((time_series_id / 180) + 1)

        pe_file = open(
            "../UKCP09PEBetterTimeSeries/[" + str(x_coord) + "][" + str(y_coord) + "]PEBetterTimeSeries.txt",
            "r")

        for a in range(lines_to_skip):
            pe_file.readline()
        for b in range(lines_to_read):
            pe_val = pe_file.readline().rstrip()
            one_grid_square_time_series_list.append(pe_val)

        pe_file.close()
        all_grid_squares_time_series_list.append(one_grid_square_time_series_list)

        # write to file
    print("writing PE time series data to file")
    for c in range(len(all_grid_squares_time_series_list[0])):
        line_list = []
        for d in range(len(all_grid_squares_time_series_list)):
            line_list.append(str(all_grid_squares_time_series_list[d][c]))
        line = ",".join(line_list)
        if c == 0:
            new_p_e_time_series.write(line + "," + run.start_date + " to " + run.end_date + "\n")
        else:
            new_p_e_time_series.write(line + "\n")

    new_p_e_time_series.close()

    get_temp(unique_p_e_ids_list, run.start_date, run.end_date,
             open(run.outputs.max_temp_timeseries, 'w'),
             "Max")
    get_temp(unique_p_e_ids_list, run.start_date, run.end_date,
             open(run.outputs.min_temp_timeseries, "w"),
             "Min")
    # write time series data to file

    # write library file

    make_lib_file(run)

    # copy SHETRAN files over

    print("Copying SHETRAN files over")
    if not os.path.exists(directory + "/program"):
        shutil.copytree("../program", directory + "/program")
    if not os.path.exists(directory+"/prepare-liz2.2.4a.exe"):
        shutil.copy("../prepare-liz2.2.4a.exe", directory + "/")
    if not os.path.exists(directory+"/rdf.csv"):
        shutil.copy("../rdf.csv", directory + "/")

    # time.sleep(10)

    # run SHETRAN prepare
    # catch = raw_input(enter catch again)

    # directory = os.getcwd()
    # dirList = directory.split("\\")
    # directory2 = "\\".join(dirList)
    # print(catch)
    # print(os.getcwd())
    #
    # new_directory = directory2 + "\\outputs\\" + catch
    # if not os.path.exists(new_directory):
    #     os.mkdir(new_directory)
    # os.chdir(new_directory)
    # print(os.getcwd())
    # libFile = catch + "LibraryFile.xml"
    # subprocess.call(["prepare-liz2.2.4a.exe", libFile])


def run_shetran(catch):
    os.chdir("outputs\\" + catch + "\\program")
    run_file = "outputs\\" + catch + "\\rundata_" + catch + ".txt"
    subprocess.call(["sv4.4.2asnow.exe", "-f", run_file])


def get_observed_flows(run):
    # obs_file = open("E:/SHETRANforUK/Inputs/NRFAdata/ "+ str(gauge)  + "FlowData.csv", "r")
    start2 = run.start_date.replace("-", ".")
    end2 = run.end_date.replace("-", ".")

    new_file = open(run.outputs.observed_flow, "w")

    obs_path = "../Inputs/NRFAdata/" + str(run.gauge_id) + "FlowData.csv"
    if os.path.exists(obs_path):
        obs_file = open(obs_path, "r")
    else:
        print('There is no flow data available for gauge {gauge_id}'.format(gauge_id=run.gauge_id))
        return

    for x in range(14):
        obs_file.readline()

    obs_start_list = obs_file.readline().rstrip().split(",")
    obs_start_string = obs_start_list[2]
    obs_start = datetime.strptime(obs_start_string, "%Y-%m-%d")
    print(obs_start)

    obs_end_list = obs_file.readline().rstrip().split(",")
    obs_end_string = obs_end_list[2]
    obs_end = datetime.strptime(obs_end_string, "%Y-%m-%d")
    print(obs_end)

    start_date = datetime.strptime(run.start_date, "%Y-%m-%d")
    end_date = datetime.strptime(run.end_date, "%Y-%m-%d")
    print(start_date)
    print(end_date)

    new_file.write("date,flow\n")

    if (obs_start - start_date).days > 0:
        print(
            "I'm sorry, I don't have observed flows for the period you're modelling. I only have data for " +
            obs_start_string + " to " + obs_end_string)
    elif (end_date - obs_end).days > 0:
        print(
            "I'm sorry, I don't have observed flows for the period you're modelling. I only have data for " +
            obs_start_string + " to " + obs_end_string)
    else:
        days_to_skip = (start_date - obs_start).days
        print("days to skip = " + str(days_to_skip))

        for x in range(days_to_skip):
            obs_file.readline()

        days_to_read = (end_date - start_date).days
        print("days to read = " + str(days_to_read))
        for x in range(days_to_read):
            line_list = obs_file.readline().rstrip().split(",")
            new_list = line_list[:2]
            new_line = ",".join(new_list)
            new_file.write(new_line + "\n")

    new_file.close()


def setup_catchment(run):
    setup(run)
    directory = "outputs/" + str(run.gauge_id)
    if run.upload is None:
        get_observed_flows(run)
    import zipfile
    print('writing zip file')
    zf = zipfile.ZipFile('output.zip', 'w', zipfile.ZIP_DEFLATED)
    print(os.path.exists('outputs/' + str(run.gauge_id)))
    for root, dirs, files in os.walk('outputs/' + str(run.gauge_id)):
        for file in files:
            print(file)
            zf.write(os.path.join(root, file))

    zf.close()
