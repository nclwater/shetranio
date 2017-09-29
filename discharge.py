from datetime import datetime, timedelta
import numpy as np
import matplotlib.pyplot as plt
import os


def timeSeriesPlotter(in_file, out_dir):
    """Saves a plot of observed verses simulated discharge to a PNG file

    Args:
        in_file (str): Path to the input CSV file.
        out_dir (str): Folder to save the output PNG into.

    Returns:
        float: Nash-Sutcliffe Efficiency.

    """

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

    diffList = []
    obsDiffList = []
    meanObs = np.mean(obs)
    for a in range(len(obs)):
        diffList.append((obs[a] - sim[a]) ** 2)
        obsDiffList.append((obs[a] - meanObs) ** 2)

    NSE = 1 - (sum(diffList) / sum(obsDiffList))

    # plot the graph!
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
    plt.savefig(os.path.join(out_dir, os.path.basename(in_file)[:-4]) + "_hydrograph.png")
    plt.clf()

    table.close()

    return NSE


def exceedanceCurve(in_file, out_dir):
    """Saves an exceedance curve plot to a PNG file

        Args:
            in_file (str): Path to the input CSV file.
            out_dir (str): Folder to save the output PNG into.

        Returns:
            None

        """

    percentilesList = range(5, 100, 5)
    percentilesList.append(99)
    percentilesList.insert(0, 1)

    table = open(in_file, "r")
    table.readline()
    obs = []
    sim = []

    for line in table:
        lineList = line.rstrip().split(",")
        try:
            obs.append(float(lineList[1]))
        except:
            pass
        try:
            sim.append(float(lineList[2]))
        except:
            pass

    table.close()

    obsPercentiles = []
    simPercentiles = []
    for perc in percentilesList:
        obsPercentiles.append(np.percentile(obs, perc))
        simPercentiles.append(np.percentile(sim, perc))

    percentilesFile = open(os.path.join(out_dir,os.path.basename(in_file)[:-4]) + "_percentiles.csv", "w")
    percentilesFile.write("Percentile,Observed,Simulated\n")
    for x in range(len(percentilesList)):
        percentilesFile.write(
            str(percentilesList[x]) + "," + str(obsPercentiles[x]) + "," + str(simPercentiles[x]) + "\n")
    percentilesFile.close()

    qList = percentilesList
    qList.reverse()
    plt.plot(qList, obsPercentiles, c="b", ls="-")
    plt.plot(qList, simPercentiles, c="r", ls="-", alpha=0.75)
    plt.title("Flow duration curve of observed vs simulated flows")
    plt.ylabel("Flow (m" + r'$^3$' + "/s)")
    plt.xlabel("% Of the time indicated discharge was equalled or exceeded")
    plt.grid(True)
    groups = ("Observed", "Simulated")
    line1 = plt.Line2D(range(10), range(10), color="b")
    line2 = plt.Line2D(range(10), range(10), color="r")
    plt.legend((line1, line2), groups, numpoints=1, loc=1, prop={'size': 8})
    plt.savefig(os.path.join(out_dir, os.path.basename(in_file)[:-4]) + "_Flow_Duration_Curve.png")
    plt.clf()


def doWaterBalance(in_file, obsOrSim):
    """Calculates the water balance of either the observed or simulated values

    Args:
            in_file (str): Path to the input CSV file.
            obsOrSim (str): Either 'o' (observed) or 's' (simulated).

        Returns:
            A list of monthly means Jan-Dec

    """

    if obsOrSim == "o":
        x = 1
    elif obsOrSim == "s":
        x = 2

    runFile = open(in_file)
    runFile.readline()

    runJanValsList = []
    runFebValsList = []
    runMarValsList = []
    runAprValsList = []
    runMayValsList = []
    runJunValsList = []
    runJulValsList = []
    runAugValsList = []
    runSepValsList = []
    runOctValsList = []
    runNovValsList = []
    runDecValsList = []

    d = datetime(1990, 1, 1)

    for line in runFile:
        if d.month == 1:
            runJanValsList.append(float(line.rstrip().split(",")[x]))
        if d.month == 2:
            runFebValsList.append(float(line.rstrip().split(",")[x]))
        if d.month == 3:
            runMarValsList.append(float(line.rstrip().split(",")[x]))
        if d.month == 4:
            runAprValsList.append(float(line.rstrip().split(",")[x]))
        if d.month == 5:
            runMayValsList.append(float(line.rstrip().split(",")[x]))
        if d.month == 6:
            runJunValsList.append(float(line.rstrip().split(",")[x]))
        if d.month == 7:
            runJulValsList.append(float(line.rstrip().split(",")[x]))
        if d.month == 8:
            runAugValsList.append(float(line.rstrip().split(",")[x]))
        if d.month == 9:
            runSepValsList.append(float(line.rstrip().split(",")[x]))
        if d.month == 10:
            runOctValsList.append(float(line.rstrip().split(",")[x]))
        if d.month == 11:
            runNovValsList.append(float(line.rstrip().split(",")[x]))
        if d.month == 12:
            runDecValsList.append(float(line.rstrip().split(",")[x]))

        d = d + timedelta(days=1)

    runFile.close()

    dataList = [np.mean(runJanValsList), np.mean(runFebValsList)
        , np.mean(runMarValsList)
        , np.mean(runAprValsList)
        , np.mean(runMayValsList)
        , np.mean(runJunValsList)
        , np.mean(runJulValsList)
        , np.mean(runAugValsList)
        , np.mean(runSepValsList)
        , np.mean(runOctValsList)
        , np.mean(runNovValsList)
        , np.mean(runDecValsList)]

    return dataList


def wbGraph(in_file, out_dir):
    """Saves a water balance plot to a PNG file

        Args:
            in_file (str): Path to the input CSV file.
            out_dir (str): Folder to save the output PNG into.

        Returns:
            None

        """

    obs = doWaterBalance(in_file, "o")
    sim = doWaterBalance(in_file, "s")

    months = [i + 1 for i in range(12)]

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
    plt.savefig(os.path.join(out_dir, os.path.basename(in_file)[:-4]) + "_Monthly_Water_Balance.png")
    plt.clf()
