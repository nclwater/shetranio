import subprocess
import os
from datetime import datetime
import netCDF4 as nc


def download_ceh_gear(username, password, output_directory=None, start=1890, end=2016):
    base_url = "https://catalogue.ceh.ac.uk/datastore/eidchub/33604ea0-c238-4488-813d-0ad9ab7c51ca/GB/daily/"

    for year in range(start, end):

        filename = "CEH_GEAR_daily_GB_{}.nc".format(year)

        url = base_url + filename

        if output_directory is not None:
            output_file = os.path.join(output_directory, filename)
        else:
            output_file = filename

        subprocess.call(["curl", "--user", "{}:{}".format(username, password),  url, "-o", output_file])


def extract(data_path: str,
            mask_path: str,
            start_date: datetime,
            end_date: datetime,
            grid_path: str,
            ts_path: str) -> None:
    mask = open(mask_path, "r")

    ncols = float(mask.readline().rstrip().split()[1])
    nrows = float(mask.readline().rstrip().split()[1])
    xllc = float(mask.readline().rstrip().split()[1])
    yllc = float(mask.readline().rstrip().split()[1])
    cell_size = float(mask.readline().rstrip().split()[1])
    no_data = mask.readline().rstrip().split()[1]

    new_mask_list = []

    index_list = []
    j = 0
    ticker = 1
    for line in mask:
        line_list = line.rstrip().split()
        new_mask_line_list = []
        for i in range(len(line_list)):
            if line_list[i] == no_data:
                new_mask_line_list.append(no_data)
            else:
                new_mask_line_list.append(str(ticker))
                ticker += 1

                mask_x = (i * cell_size) + xllc + (cell_size / 2)
                mask_y = (nrows - j) * cell_size + yllc - (cell_size / 2)

                ceh_gear_resolution = 1000  # metres

                # 1251 must be the top of the gear data?
                y_idx, x_idx = 1251 - 1 - int(mask_y / ceh_gear_resolution), int(mask_x / ceh_gear_resolution)

                index_list.append((y_idx, x_idx))

        new_mask_list.append(new_mask_line_list)

        j += 1

    start_year = start_date.year
    end_year = end_date.year
    start_index = start_date.timetuple().tm_yday - 1
    end_index = end_date.timetuple().tm_yday

    grid = [[] for i in range(len(index_list))]

    for year in range(start_year, end_year + 1, 1):
        f = nc.Dataset(data_path)

        for grid_square in range(len(index_list)):
            if index_list[grid_square] in index_list[:grid_square]:
                # check if cell has already been read from netCDF
                first_cell_series = grid[index_list.index(index_list[grid_square])]
                grid[grid_square].extend(first_cell_series[len(grid[grid_square]):])
                continue

            j, i = index_list[grid_square]

            if year == start_year:
                if year == end_year:
                    ts = f.variables['rainfall_amount'][start_index:end_index, j, i]
                else:
                    ts = f.variables['rainfall_amount'][start_index:, j, i]

            elif year == end_year:
                ts = f.variables['rainfall_amount'][:end_index, j, i]

            else:
                ts = f.variables['rainfall_amount'][:, j, i]

            grid[grid_square].extend(ts)

        f.close()

    new_mask = open(grid_path, "w")

    new_mask.write("ncols\t" + str(ncols) + "\n")
    new_mask.write("nrows\t" + str(nrows) + "\n")
    new_mask.write("xllcorner\t" + str(xllc) + "\n")
    new_mask.write("yllcorner\t" + str(yllc) + "\n")
    new_mask.write("cellsize\t" + str(cell_size) + "\n")
    new_mask.write("NODATA_value\t" + str(no_data) + "\n")

    for new_line_list in new_mask_list:
        new_line = " ".join(new_line_list)
        new_mask.write(new_line + "\n")

    new_mask.close()

    new_ts = open(ts_path, "w")

    new_ts.write(",".join([str(a + 1) for a in range(len(grid))]) + "\n")

    for d in range(len(grid[0])):
        new_ts_line_list = []
        for b in range(len(grid)):
            new_ts_line_list.append(str(grid[b][d]))

        new_ts.write(",".join(new_ts_line_list) + "\n")

    new_ts.close()

