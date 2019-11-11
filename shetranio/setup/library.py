# preparing the library file to go into SHETRAN e.g. H:\PhD\PythonLessons\gettingItIntoSHETRAN\s1.xml
# please ensure that there are no backslashes in the file paths as theres are escape characters in python. Use forward slashes instead!
import os


def make_lib_file(run):

    print("Making library file")
    lib_file_path = os.path.join(run.directory, "LibraryFile.xml")
    project_file = "{}ProjectFile".format(run.gauge_id)
    dem_file = os.path.basename(run.outputs.dem)
    min_dem_file = os.path.basename(run.outputs.min_dem)
    mask_files = os.path.basename(run.outputs.mask)
    pe_file = os.path.basename(run.outputs.pe)
    ppt_file = os.path.basename(run.outputs.rain)
    veg_file = os.path.basename(run.outputs.veg)
    soil_file = os.path.basename(run.outputs.soil)
    # if run.resolution == '500m':
    lake_file = os.path.basename(run.outputs.lakes)
    # else:
    #     lake_file = False
    ppt_time_series = os.path.basename(run.outputs.rain_timeseries)
    pe_time_series = os.path.basename(run.outputs.pe_timeseries)
    max_temp_time_series = os.path.basename(run.outputs.max_temp_timeseries)
    min_temp_time_series = os.path.basename(run.outputs.min_temp_timeseries)
    simulated_discharge_file = os.path.basename(run.outputs.simulated_discharge)

    library_file = open(lib_file_path, "w")

    # input files
    with open("code_key_uk_soil_four_layers.txt", "r") as f:
        code_key_uk_soil_four_layers = f.readlines()

    # Variables
    overland_flow_roughness_coefficient = 1  # 0.1-10
    initial_conditions = 0
    precipitation_time_step = 24
    pe_time_step = 24
    if run.start_date[8] == 0:
        start_day = run.start_date[9:]
    else:
        start_day = run.start_date[8:]

    if run.start_date[5] == 0:
        start_month = run.start_date[6:-3]
    else:
        start_month = run.start_date[5:-3]
    start_year = run.start_date[:-6]

    if run.end_date[8] == 0:
        end_day = run.end_date[9:]
    else:
        end_day = run.end_date[8:]

    if run.end_date[5] == 0:
        end_month = run.end_date[6:-3]
    else:
        end_month = run.end_date[5:-3]
    end_year = run.end_date[:-6]

    river_grid_squares_accumulated = 2  # min 2 - 200
    drop_from_grid_to_channel_depth = 2  # 2-20
    minimum_drop_between_channels = 0.5  # 0.1- 10 only 10 in steep catchment
    rock_depth = 5  # (1-20)
    snowmelt_degree_day_factor = 0.0002
    # ae/pe 0.1-1

    # soil parameters
    hg1 = ['HighlyProductiveAquifer, ', '0.3, 0.2, 0.1, 0.01, 5']
    hg2 = ['ModeratelyProductiveAquifer, ', '0.3, 0.2, 0.01, 0.01, 5']
    hg3 = ['LowProductivityAquifer, ', '0.3, 0.2, 0.001, 0.01, 5']
    hg4 = ['NoGroundwater, ', '0.3, 0.2, 0.0001, 0.01, 5']

    rock_depth_for_h_p_aquifer = 20

    dr1 = 1
    dr2 = 0.3  # no value"
    dr3 = 0.6
    dr4 = 0.4
    dr5 = 1.2

    text_dep_chg0 = 0.3  # "No information"
    text_dep_chg1 = 0.3
    text_dep_chg2 = 0.5
    text_dep_chg3 = 0.7
    text_dep_chg4 = 1
    text_dep_chg5 = 1.3  # check with steve. I think this should just represent the botom of the column
    text_dep_chg6 = 0.4
    text_dep_chg7 = 0.9

    # EUcode, soil layer, soil type, saturated water content, Residual Water Content, Saturated Conductivity (m/day), vanGenuchten- alpha (cm-1), vanGenuchten-n
    text_srf_dom0 = ['1, Peat, ', '0.766, 0.010, 8, 0.0130, 1.2039']  # "1, NoInformation"
    text_srf_dom9 = ['1, Peat, ', '0.766, 0.010, 8, 0.0130, 1.2039']
    text_srf_dom1 = ['1, Coarse(18%:clayAnd:65%sand), ', '0.403, 0.025, 60.000, 0.0383, 1.3774']
    text_srf_dom2 = ['1, Medium(18%:clay:35%And:15%sandOr18%:clayAnd15%:sand:65%), ',
                   '0.439, 0.010, 12.061, 0.0314, 1.1804']
    text_srf_dom3 = ['1, MediumFine(:35%clayand:15%sand), ', '0.430, 0.010, 2.272, 0.0083, 1.2539']
    text_srf_dom4 = ['1, Fine(35%:clay:60%), ', '0.520, 0.010, 24.800, 0.0367, 1.1012']
    text_srf_dom5 = ['1, VeryFine(clay:60%), ', '0.614, 0.010, 15.000, 0.0265, 1.1033']

    # EUcode, soil layer, soil type, saturated water content, Residual Water Content, Saturated Conductivity (m/day), vanGenuchten- alpha (cm-1), vanGenuchten-n
    text_sub_dom0 = ['2, Peat, ', '0.766, 0.010, 8, 0.0130, 1.2039']  # "2, NoInformation"
    text_sub_dom9 = ['2, Peat, ', '0.766, 0.010, 8, 0.0130, 1.2039']
    text_sub_dom1 = ['2, Coarse(18%:clayAnd:65%sand), ', '0.366, 0.025, 70.000, 0.0430, 1.5206']
    text_sub_dom2 = ['2, Medium(18%:clay:35%And::15%sandOr18%:clayAnd15%:sand:65%), ',
                   '0.329, 0.010, 10.755, 0.0249, 1.1689']
    text_sub_dom3 = ['2, MediumFine(:35%clayand:15%sand), ', '0.412, 0.010, 4.000, 0.0082, 1.2179']
    text_sub_dom4 = ['2, Fine(35%:clay:60%), ', '0.481, 0.010, 8.500, 0.0198, 1.0861']
    text_sub_dom5 = ['2, VeryFine(clay:60%), ', '0.538, 0.010, 8.235, 0.0168, 1.0730']

    # write file
    library_file.write("<?xml version=""1.0""?><ShetranInput>\n")
    library_file.write("<ProjectFile>" + project_file + "</ProjectFile>\n")
    library_file.write("<CatchmentName>{}</CatchmentName>\n".format(run.gauge_id))
    library_file.write("<DEMMeanFileName>" + dem_file + "</DEMMeanFileName>\n")
    library_file.write("<DEMminFileName>" + min_dem_file + "</DEMMinFileName>\n")
    library_file.write("<MaskFileName>" + mask_files + "</MaskFileName>\n")
    library_file.write("<VegMap>" + veg_file + "</VegMap>\n")
    library_file.write("<SoilMap>" + soil_file + "</SoilMap>\n")
    # if lake_file:
    library_file.write("<LakeMap>" + lake_file + "</LakeMap>\n")
    library_file.write("<PrecipMap>" + ppt_file + "</PrecipMap>\n")
    library_file.write("<PeMap>" + pe_file + "</PeMap>\n")
    library_file.write(
        "<VegetationDetails><VegetationDetail>Veg Type #, Vegetation Type, Canopy storage capacity (mm), Leaf area index, Maximum rooting depth(m), AE/PE at field capacity</VegetationDetail>\n")

    # veg key:
    # <VegetationDetail>1, Grass, 1.5, 6, 1, 0.6</VegetationDetail>\n

    library_file.write("<VegetationDetail>1, Arable, 1.0, 0.8, 0.8, 0.6</VegetationDetail>\n")
    library_file.write("<VegetationDetail>2, BareGround, 0, 0, 0.1, 0.4</VegetationDetail>\n")
    library_file.write("<VegetationDetail>3, Grass, 1.5, 1, 1.0, 0.6</VegetationDetail>\n")
    library_file.write("<VegetationDetail>4, DeciduousForest, 5, 1, 1.6, 1.0</VegetationDetail>\n")
    library_file.write("<VegetationDetail>5, EvergreenForest, 5, 1, 2.0, 1.0</VegetationDetail>\n")
    library_file.write("<VegetationDetail>6, Shrub, 1.5, 1, 1.0, 0.4</VegetationDetail>\n")
    library_file.write("<VegetationDetail>7, Urban, 0.3, 0.3, 0.5, 0.4</VegetationDetail>\n")
    library_file.write("</VegetationDetails>\n")

    library_file.write(
        "<SoilDetails><SoilDetail>Soil Category, Soil Layer, Soil Type, Depth at base of layer (m), Saturated Water Content, Residual Water Content, Saturated Conductivity (m/day), vanGenuchten- alpha (cm-1), vanGenuchten-n</SoilDetail>\n")
    # loop over soil column types- format:
    # <SoilDetail>1, 1, SiltLoam(10%Sand:10%Clay), 1, 0.452, 0.093, 0.163, 5.15E-03, 1.681</SoilDetail>\n

    for line in code_key_uk_soil_four_layers:
        lineList = line.rstrip().split(" ")
        # print lineList
        # get she_code
        she_code = lineList[1].rstrip()
        # data or no data?
        if she_code == "-9999":
            print("")
        else:
            # getting the first element of the line i.e. the long colon code
            code_list = lineList[0].rstrip().split(":")
            # print code_list
            hg = code_list[0]
            dr = code_list[1]
            text_dep_chg = code_list[2]
            text_srf_dom = code_list[3]
            text_sub_dom = code_list[4]

            if float(eval("dr" + str(dr))) <= float(eval("text_dep_chg" + str(text_dep_chg))):  # 1 layer plus rock layer
                if float(dr) == 1:
                    second_bit = dr1
                elif float(dr) == 2:
                    second_bit = dr2
                elif float(dr) == 3:
                    second_bit = dr3
                elif float(dr) == 4:
                    second_bit = dr4
                elif float(dr) == 5:
                    second_bit = dr5
                else:
                    print("piddle on aisle dr")

                if float(text_srf_dom) == 0:
                    first_bit = text_srf_dom0[0]
                    third_bit = text_srf_dom0[1]
                elif float(text_srf_dom) == 9:
                    first_bit = text_srf_dom9[0]
                    third_bit = text_srf_dom9[1]
                elif float(text_srf_dom) == 1:
                    first_bit = text_srf_dom1[0]
                    third_bit = text_srf_dom1[1]
                elif float(text_srf_dom) == 2:
                    first_bit = text_srf_dom2[0]
                    third_bit = text_srf_dom2[1]
                elif float(text_srf_dom) == 3:
                    first_bit = text_srf_dom3[0]
                    third_bit = text_srf_dom3[1]
                elif float(text_srf_dom) == 4:
                    first_bit = text_srf_dom4[0]
                    third_bit = text_srf_dom4[1]
                elif float(text_srf_dom) == 5:
                    first_bit = text_srf_dom5[0]
                    third_bit = text_srf_dom5[1]
                else:
                    print("piddle on aisle text_srf_dom")
                # Added in that if it is a highly productive aquifer, the depth of it is 20m not 5m
                if float(hg) == 1:
                    first_bit2 = hg1[0]
                    third_bit2 = hg1[1]
                    rock_depth = 20
                elif float(hg) == 2:
                    first_bit2 = hg2[0]
                    third_bit2 = hg2[1]
                elif float(hg) == 3:
                    first_bit2 = hg3[0]
                    third_bit2 = hg3[1]
                elif float(hg) == 4:
                    first_bit2 = hg4[0]
                    third_bit2 = hg4[1]
                else:
                    print('piddle on aisle hg')
                # 1 layer topsoil
                library_file.write(
                    "<SoilDetail>" + she_code + ", " + first_bit + str(second_bit) + ", " + third_bit + "</SoilDetail>\n")
                # 2 layer rock
                library_file.write("<SoilDetail>" + she_code + ", 2, " + first_bit2 + str(
                    second_bit + rock_depth) + ", " + third_bit2 + "</SoilDetail>\n")
            else:
                # 3 layers	including rock
                # 1st layer
                if float(text_srf_dom) == 0:
                    first_bit = text_srf_dom0[0]
                    third_bit = text_srf_dom0[1]
                elif float(text_srf_dom) == 9:
                    first_bit = text_srf_dom9[0]
                    third_bit = text_srf_dom9[1]
                elif float(text_srf_dom) == 1:
                    first_bit = text_srf_dom1[0]
                    third_bit = text_srf_dom1[1]
                elif float(text_srf_dom) == 2:
                    first_bit = text_srf_dom2[0]
                    third_bit = text_srf_dom2[1]
                elif float(text_srf_dom) == 3:
                    first_bit = text_srf_dom3[0]
                    third_bit = text_srf_dom3[1]
                elif float(text_srf_dom) == 4:
                    first_bit = text_srf_dom4[0]
                    third_bit = text_srf_dom4[1]
                elif float(text_srf_dom) == 5:
                    first_bit = text_srf_dom5[0]
                    third_bit = text_srf_dom5[1]
                else:
                    print("piddle on aisle text_srf_dom")

                if float(text_dep_chg) == 0:
                    second_bit = text_dep_chg0
                elif float(text_dep_chg) == 1:
                    second_bit = text_dep_chg1
                elif float(text_dep_chg) == 2:
                    second_bit = text_dep_chg2
                elif float(text_dep_chg) == 3:
                    second_bit = text_dep_chg3
                elif float(text_dep_chg) == 4:
                    second_bit = text_dep_chg4
                elif float(text_dep_chg) == 5:
                    second_bit = text_dep_chg5
                elif float(text_dep_chg) == 6:
                    second_bit = text_dep_chg6
                elif float(text_dep_chg) == 7:
                    second_bit = text_dep_chg7
                else:
                    print("piddle on aisle text_dep_chg")

                # 2nd layer

                if float(text_sub_dom) == 0:
                    first_bit2 = text_sub_dom0[0]
                    third_bit2 = text_sub_dom0[1]
                elif float(text_sub_dom) == 9:
                    first_bit2 = text_sub_dom9[0]
                    third_bit2 = text_sub_dom9[1]
                elif float(text_sub_dom) == 1:
                    first_bit2 = text_sub_dom1[0]
                    third_bit2 = text_sub_dom1[1]
                elif float(text_sub_dom) == 2:
                    first_bit2 = text_sub_dom2[0]
                    third_bit2 = text_sub_dom2[1]
                elif float(text_sub_dom) == 3:
                    first_bit2 = text_sub_dom3[0]
                    third_bit2 = text_sub_dom3[1]
                elif float(text_sub_dom) == 4:
                    first_bit2 = text_sub_dom4[0]
                    third_bit2 = text_sub_dom4[1]
                elif float(text_sub_dom) == 5:
                    first_bit2 = text_sub_dom5[0]
                    third_bit2 = text_sub_dom5[1]
                else:
                    print("piddle on aisle text_srf_dom")

                if float(dr) == 1:
                    second_bit2 = dr1
                elif float(dr) == 2:
                    second_bit2 = dr2
                elif float(dr) == 3:
                    second_bit2 = dr3
                elif float(dr) == 4:
                    second_bit2 = dr4
                elif float(dr) == 5:
                    second_bit2 = dr5
                else:
                    print("piddle on aisle dr")

                # rock layer. Added in that if it is a highly productive aquifer, the depth of it is 20m not 5m
                if float(hg) == 1:
                    first_bit3 = hg1[0]
                    third_bit3 = hg1[1]
                    rock_depth = rock_depth_for_h_p_aquifer
                elif float(hg) == 2:
                    first_bit3 = hg2[0]
                    third_bit3 = hg2[1]
                elif float(hg) == 3:
                    first_bit3 = hg3[0]
                    third_bit3 = hg3[1]
                elif float(hg) == 4:
                    first_bit3 = hg4[0]
                    third_bit3 = hg4[1]

                library_file.write(
                    "<SoilDetail>" + she_code + ", " + first_bit + str(second_bit) + ", " + third_bit + "</SoilDetail>\n")
                library_file.write("<SoilDetail>" + she_code + ", " + first_bit2 + str(
                    second_bit2) + ", " + third_bit2 + "</SoilDetail>\n")
                library_file.write("<SoilDetail>" + she_code + ", 3, " + first_bit3 + str(
                    second_bit2 + rock_depth) + ", " + third_bit3 + "</SoilDetail>\n")

    library_file.write("</SoilDetails><OverlandFlowRoughnessCoefficient>" + str(
        overland_flow_roughness_coefficient) + "</OverlandFlowRoughnessCoefficient>\n")
    library_file.write("<InitialConditions>" + str(initial_conditions) + "</InitialConditions>\n")
    library_file.write("<PrecipitationTimeSeriesData>" + ppt_time_series + "</PrecipitationTimeSeriesData>\n")
    library_file.write("<PrecipitationTimeStep>" + str(precipitation_time_step) + "</PrecipitationTimeStep>\n")
    library_file.write("<EvaporationTimeSeriesData>" + pe_time_series + "</EvaporationTimeSeriesData>\n")
    library_file.write("<EvaporationTimeStep>" + str(pe_time_step) + "</EvaporationTimeStep>\n")
    library_file.write("<MaxTempTimeSeriesData>" + max_temp_time_series + "</MaxTempTimeSeriesData>\n")
    library_file.write("<MinTempTimeSeriesData>" + min_temp_time_series + "</MinTempTimeSeriesData>\n")
    library_file.write("<StartDay>" + str(start_day) + "</StartDay>\n")
    library_file.write("<StartMonth>" + str(start_month) + "</StartMonth>\n")
    library_file.write("<StartYear>" + str(start_year) + "</StartYear>\n")
    library_file.write("<EndDay>" + str(end_day) + "</EndDay>\n")
    library_file.write("<EndMonth>" + str(end_month) + "</EndMonth>\n")
    library_file.write("<EndYear>" + str(end_year) + "</EndYear>\n")
    library_file.write(
        "<RiverGridSquaresAccumulated>" + str(river_grid_squares_accumulated) + "</RiverGridSquaresAccumulated>\n")
    library_file.write(
        "<DropFromGridToChannelDepth>" + str(drop_from_grid_to_channel_depth) + "</DropFromGridToChannelDepth>\n")
    library_file.write(
        "<MinimumDropBetweenChannels>" + str(minimum_drop_between_channels) + "</MinimumDropBetweenChannels>\n")
    library_file.write("<SnowmeltDegreeDayFactor>" + str(snowmelt_degree_day_factor) + "</SnowmeltDegreeDayFactor>\n")
    library_file.write("<SimulatedDischargeFile>" + simulated_discharge_file + "</SimulatedDischargeFile>\n")
    library_file.write("<PreviousDischargeFile />\n")
    library_file.write("<MeasuredDischargeFile />\n")
    library_file.write("</ShetranInput>\n")

    print("library file created")
    library_file.close()
