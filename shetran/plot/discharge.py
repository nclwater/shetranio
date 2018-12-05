from datetime import datetime, timedelta
import numpy as np
import matplotlib.pyplot as plt
import os

def _read_obs(in_file):
    table = open(in_file, "r")
    table.readline()
    values = []
    days = []
    for line in table:
        l = line.strip().split(",")
        values.append(float(l[1]))
        days.append(l[0])
    try:
        days = [datetime.strptime(day, '%d/%m/%Y') for day in days]
    except ValueError:
        days = [datetime.strptime(day, '%m/%d/%Y') for day in days]

    table.close()
    return values, days

def _read_sim(in_file):
    table = open(in_file, "r")
    table.readline()
    values = []
    for line in table:
        values.append(float(line.strip()))

    table.close()
    return values


def hydrograph(sim, obs=None, out_dir=None, start_date=None, time_step=None):
    """Creates a plot of observed verses simulated discharge

    Args:
        in_file (str): Path to the input CSV file.
        out_dir (str): Folder to save the output PNG into.

    Returns:
        None

    """

    if obs is None and (start_date is None or time_step is None):
        raise Exception('If there is no observed series, you must provide a start date and time step')

    sim_values = _read_sim(sim)
    if obs is not None:
        obs_values, days = _read_obs(obs)
        assert len(obs_values) == len(sim_values)
    else:
        days = []
        for i in range(len(sim_values)):
            days.append(start_date+timedelta(hours=time_step)*i)


    plt.figure(figsize=[12.0, 5.0])
    plt.subplots_adjust(bottom=0.2)

    plt.plot_date(days, y=sim_values, fmt="r-", alpha=0.75)

    if obs is not None:
        plt.plot_date(x=days, y=obs_values, fmt="b-")
        plt.title("Observed vs simulated flows")
        groups = ("Observed", "Simulated")
        line1 = plt.Line2D(range(10), range(10), color="b")
        line2 = plt.Line2D(range(10), range(10), color="r")
        plt.legend((line1, line2), groups, numpoints=1, loc=1, prop={'size': 8})
    else:
        plt.title("Simulated flows")

    plt.gca().set_ylim(bottom=0)

    plt.ylabel("Flow (m" + r'$^3$' + "/s)")
    plt.grid(True)
    plt.xticks(rotation=70)

    if out_dir:
        if not os.path.exists(out_dir):
            os.mkdir(out_dir)
        plt.savefig(os.path.join(out_dir, os.path.basename(sim)[:-4]) + "_hydrograph.png")

        with open(os.path.join(out_dir, os.path.basename(sim)[:-4]) + "_hydrograph.csv", 'w') as f:
            if obs is not None:
                f.write('date,obs,sim\n')
            else:
                f.write('date,sim\n')
            for i in range(len(days)):
                if obs is not None:
                    f.write('{},{:.2f},{:.2f}\n'.format(days[i], obs_values[i], sim_values[i]))
                else:
                    f.write('{},{:.2f}\n'.format(days[i], sim_values[i]))

    plt.show()


def get_nse(sim, obs):
    """Calculates the Nash Sutcliffe Efficiency of observed vs simulated discharge.

        Args:
            in_file (str): Path to the input CSV file.

        Returns:
            float: Value of NSE

        """
    sim_values = _read_sim(sim)
    obs_values, days = _read_obs(obs)

    if len(sim_values) != len(obs_values):
        raise Exception('Observed and Simulated records must be the same length')

    diffList = []
    obsDiffList = []
    meanObs = np.mean(obs_values)
    for a in range(len(obs_values)):
        diffList.append((obs_values[a] - sim_values[a]) ** 2)
        obsDiffList.append((obs_values[a] - meanObs) ** 2)

    return float(round(1 - (sum(diffList) / sum(obsDiffList)), 3))


def percentiles(sim, obs=None, out_dir=None):
    """Calculates percentiles of observed vs simulated discharge at 0, 1, 5-100 in steps of 5 and 99.

            Args:
                in_file (str): Path to the input CSV file.
                out_dir (str,optional): Path to output CSV file.

            Returns:
                tuple: First element is a list of percentiles, second is the observed percentiles
                    and third is the simulated percentiles

    """
    percentiles_list = list(range(5, 100, 5))
    percentiles_list.append(99)
    percentiles_list.insert(0, 1)

    sim_values = _read_sim(sim)
    sim_percentiles = [np.percentile(sim_values, percentile) for percentile in percentiles_list]

    if obs is not None:
        obs_values, days = _read_obs(obs)
        assert len(sim_values) == len(obs_values), 'Observed and simulated series must be the same length'
        obs_percentiles = [np.percentile(obs_values, percentile) for percentile in percentiles_list]


    if out_dir:

        percentiles_file = open(os.path.join(out_dir, os.path.basename(sim)[:-4]) + "_percentiles.csv", "w")
        if obs is not None:
            percentiles_file.write("Percentile,Observed,Simulated\n")
            for x in range(len(percentiles_list)):
                percentiles_file.write(
                    str(percentiles_list[x]) + "," + str(obs_percentiles[x]) + "," + str(sim_percentiles[x]) + "\n")
            percentiles_file.close()
        else:
            percentiles_file.write("Percentile,Simulated\n")
            for x in range(len(percentiles_list)):
                percentiles_file.write(
                    str(percentiles_list[x]) + "," + str(sim_percentiles[x]) + "\n")
            percentiles_file.close()
    if obs is not None:
        return percentiles_list, obs_percentiles, sim_percentiles
    else:
        return percentiles_list, sim_percentiles


def exceedance(sim, obs=None, out_dir=None):
    """Saves an exceedance curve plot to a PNG file

        Args:
            in_file (str): Path to the input CSV file.
            out_dir (str): Folder to save the output PNG into.

        Returns:
            None

        """
    plt.figure(figsize=[12.0, 5.0])

    if obs is not None:
        percentiles_list, obs_percentiles, sim_percentiles = percentiles(sim, obs, out_dir=out_dir)
        plt.title("Flow duration curve of observed vs simulated flows")
    else:
        percentiles_list, sim_percentiles = percentiles(sim, out_dir=out_dir)
        plt.title("Flow duration curve of simulated flows")

    percentiles_list.reverse()

    plt.plot(percentiles_list, sim_percentiles, c="r", ls="-", alpha=0.75)
    if obs is not None:
        plt.plot(percentiles_list, obs_percentiles, c="b", ls="-")
        groups = ("Observed", "Simulated")
        line1 = plt.Line2D(range(10), range(10), color="b")
        line2 = plt.Line2D(range(10), range(10), color="r")
        plt.legend((line1, line2), groups, numpoints=1, loc=1, prop={'size': 8})


    plt.ylabel("Flow (m" + r'$^3$' + "/s)")
    plt.xlabel("% Of the time indicated discharge was equalled or exceeded")
    plt.grid(True)

    if out_dir:
        if not os.path.exists(out_dir):
            os.mkdir(out_dir)
        plt.savefig(os.path.join(out_dir, os.path.basename(sim)[:-4]) + "_Flow_Duration_Curve.png")

    plt.show()


def water_balance(sim, obs=None, out_dir=None, start_date=None, time_step=None):
    """Saves a water balance plot to a PNG file

        Args:
            in_file (str): Path to the input CSV file.
            out_dir (str): Folder to save the output PNG into.

        Returns:
            None

        """
    if obs is None and (start_date is None or time_step is None):
        raise Exception('If there is no observed series, you must provide a start date and time step')

    sim_values = _read_sim(sim)
    if obs is not None:
        obs_values, days = _read_obs(obs)
        assert len(obs_values) == len(sim_values), 'The lengths of the observed and simulated records must be the same'
    else:
        days = []
        for i in range(len(sim_values)):
            days.append(start_date+timedelta(hours=time_step)*i)

    if obs is not None:
        obs_months = [[] for _ in range(12)]
    sim_months = [[] for _ in range(12)]

    for idx in range(len(days)):
        if obs is not None:
            obs_months[days[idx].month-1].append(obs_values[idx])
        sim_months[days[idx].month-1].append(sim_values[idx])
    if obs is not None:
        obs_months = [np.mean(month) for month in obs_months]
    sim_months = [np.mean(month) for month in sim_months]

    months = range(1,13)

    plt.figure(figsize=[12.0, 5.0])
    if obs is not None:
        plt.plot(months, obs_months, c="b", ls="-")
        groups = ("Observed", "Simulated")
        line1 = plt.Line2D(range(10), range(10), color="b")
        line2 = plt.Line2D(range(10), range(10), color="r")
        plt.legend((line1, line2), groups, numpoints=1, loc=1, prop={'size': 8})
    plt.plot(months, sim_months, c="r", ls="-", alpha=0.75)
    plt.title("Monthly Average Flows")
    plt.ylabel("Flow (m" + r'$^3$' + "/s)")
    plt.xlabel("Month")
    plt.grid(True)

    if out_dir:
        if not os.path.exists(out_dir):
            os.mkdir(out_dir)
        plt.savefig(os.path.join(out_dir, os.path.basename(sim)[:-4]) + "_Monthly_Water_Balance.png")

        with open(os.path.join(out_dir, os.path.basename(sim)[:-4]) + "_Monthly_Water_Balance.csv", 'w') as f:
            if obs is not None:
                f.write('month,obs,sim\n')
                for i in range(len(months)):
                    f.write('{},{:.2f},{:.2f}\n'.format(months[i], obs_months[i], sim_months[i]))
            else:
                f.write('month,sim\n')
                for i in range(len(months)):
                    f.write('{},{:.2f},{:.2f}\n'.format(months[i], sim_months[i]))

    plt.show()

