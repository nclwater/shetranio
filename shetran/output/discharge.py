from datetime import datetime, timedelta
import numpy as np
import matplotlib.pyplot as plt
import os

def _read(in_file):
    table = open(in_file, "r")
    table.readline()
    obs = []
    sim = []
    days = []
    for line in table:
        lineList = line.rstrip().split(",")
        dayVal = lineList[0]
        obsVal = lineList[1]
        simVal = lineList[2]

        obs.append(float(obsVal))

        sim.append(float(simVal))

        days.append(datetime.strptime(dayVal, '%d/%m/%Y'))

    table.close()
    return obs, sim, days


def plot_time_series(in_file, out_dir=None):
    """Creates a plot of observed verses simulated discharge

    Args:
        in_file (str): Path to the input CSV file.
        out_dir (str): Folder to save the output PNG into.

    Returns:
        None

    """

    obs, sim, days = _read(in_file)

    plt.figure(dpi=300, figsize=[12.0, 5.0])
    plt.subplots_adjust(bottom=0.2)
    plt.plot_date(x=days, y=obs, fmt="b-")
    plt.plot_date(x=days, y=sim, fmt="r-", alpha=0.75)
    plt.gca().set_ylim(bottom=0)
    plt.title("Observed vs simulated flows")
    plt.ylabel("Flow (m" + r'$^3$' + "/s)")
    plt.grid(True)
    plt.xticks(rotation=70)

    groups = ("Observed", "Simulated")
    line1 = plt.Line2D(range(10), range(10), color="b")
    line2 = plt.Line2D(range(10), range(10), color="r")
    plt.legend((line1, line2), groups, numpoints=1, loc=1, prop={'size': 8})
    if out_dir:
        if not os.path.exists(out_dir):
            os.mkdir(out_dir)
        plt.savefig(os.path.join(out_dir, os.path.basename(in_file)[:-4]) + "_hydrograph.png")

    plt.show()


def get_nse(in_file):
    """Calculates the Nash Sutcliffe Efficiency of observed vs simulated discharge.

        Args:
            in_file (str): Path to the input CSV file.

        Returns:
            float: Value of NSE

        """
    obs, sim, days = _read(in_file)

    diffList = []
    obsDiffList = []
    meanObs = np.mean(obs)
    for a in range(len(obs)):
        diffList.append((obs[a] - sim[a]) ** 2)
        obsDiffList.append((obs[a] - meanObs) ** 2)

    return 1 - (sum(diffList) / sum(obsDiffList))


def get_percentiles(in_file, out_dir=None):
    """Calculates percentiles of observed vs simulated discharge at 0, 1, 5-100 in steps of 5 and 99.

            Args:
                in_file (str): Path to the input CSV file.
                out_dir (str,optional): Path to output CSV file.

            Returns:
                tuple: First element is a list of percentiles, second is the observed percentiles
                    and third is the simulated percentiles

    """
    percentiles_list = range(5, 100, 5)
    percentiles_list.append(99)
    percentiles_list.insert(0, 1)

    obs, sim, days = _read(in_file)

    obs_percentiles = [np.percentile(obs, percentile) for percentile in percentiles_list]
    sim_percentiles = [np.percentile(sim, percentile) for percentile in percentiles_list]

    if out_dir:

        percentiles_file = open(os.path.join(out_dir, os.path.basename(in_file)[:-4]) + "_percentiles.csv", "w")
        percentiles_file.write("Percentile,Observed,Simulated\n")
        for x in range(len(percentiles_list)):
            percentiles_file.write(
                str(percentiles_list[x]) + "," + str(obs_percentiles[x]) + "," + str(sim_percentiles[x]) + "\n")
        percentiles_file.close()

    return percentiles_list, obs_percentiles, sim_percentiles


def plot_exceedance(in_file, out_dir=None):
    """Saves an exceedance curve plot to a PNG file

        Args:
            in_file (str): Path to the input CSV file.
            out_dir (str): Folder to save the output PNG into.

        Returns:
            None

        """
    percentiles_list, obs_percentiles, sim_percentiles = get_percentiles(in_file)

    percentiles_list.reverse()

    plt.figure(figsize=[12.0, 5.0], dpi=300)
    plt.plot(percentiles_list, obs_percentiles, c="b", ls="-")
    plt.plot(percentiles_list, sim_percentiles, c="r", ls="-", alpha=0.75)
    plt.title("Flow duration curve of observed vs simulated flows")
    plt.ylabel("Flow (m" + r'$^3$' + "/s)")
    plt.xlabel("% Of the time indicated discharge was equalled or exceeded")
    plt.grid(True)

    groups = ("Observed", "Simulated")
    line1 = plt.Line2D(range(10), range(10), color="b")
    line2 = plt.Line2D(range(10), range(10), color="r")
    plt.legend((line1, line2), groups, numpoints=1, loc=1, prop={'size': 8})

    if out_dir:
        if not os.path.exists(out_dir):
            os.mkdir(out_dir)
        plt.savefig(os.path.join(out_dir, os.path.basename(in_file)[:-4]) + "_Flow_Duration_Curve.png")

    plt.show()


def plot_water_balance(in_file, out_dir=None):
    """Saves a water balance plot to a PNG file

        Args:
            in_file (str): Path to the input CSV file.
            out_dir (str): Folder to save the output PNG into.

        Returns:
            None

        """

    with open(in_file) as run_file:

        lines = run_file.readlines()

        obs = [[] for _ in range(12)]
        sim = [[] for _ in range(12)]

        day, month, year = [int(s) for s in lines[1].split(',')[0].split('/')]
        d = datetime(year, month, day)

        for line in lines[1:]:

            obs[d.month-1].append(float(line.rstrip().split(",")[1]))
            sim[d.month-1].append(float(line.rstrip().split(",")[2]))

            d += timedelta(days=1)

    obs = [np.mean(month) for month in obs]
    sim = [np.mean(month) for month in sim]

    months = range(1,13)

    plt.figure(dpi=300, figsize=[12.0, 5.0])
    plt.plot(months, obs, c="b", ls="-")
    plt.plot(months, sim, c="r", ls="-", alpha=0.75)
    plt.title("Monthlys Average Flows")
    plt.ylabel("Flow (m" + r'$^3$' + "/s)")
    plt.xlabel("Month")
    plt.grid(True)
    groups = ("Observed", "Simulated")
    line1 = plt.Line2D(range(10), range(10), color="b")
    line2 = plt.Line2D(range(10), range(10), color="r")
    plt.legend((line1, line2), groups, numpoints=1, loc=1, prop={'size': 8})

    if out_dir:
        if not os.path.exists(out_dir):
            os.mkdir(out_dir)
        plt.savefig(os.path.join(out_dir, os.path.basename(in_file)[:-4]) + "_Monthly_Water_Balance.png")
    plt.show()

