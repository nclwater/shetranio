from shetran.plot import discharge, evap, overland, soil, table, water
from datetime import datetime as dt
import os

data_path = os.path.join(os.path.dirname(__file__), 'sample_data')
output_path = os.path.join(os.path.dirname(__file__), 'outputs')
discharge_file = os.path.join(data_path, 'WansbeckResults.csv')
h5_file = os.path.join(data_path, 'output_Wansbeck_at_Mitford_shegraph.h5')
points_file = os.path.join(data_path, 'points.txt')
flow_points_file = os.path.join(data_path, 'points_flow.txt')
dem_file = os.path.join(data_path, 'Wansbeck_at_Mitford_Dem.txt')
flow_links_file = os.path.join(data_path, 'flow_link_numbers.txt')
start_date = dt(2012, 1, 1)

discharge.exceedance(discharge_file, output_path)
discharge.hydrograph(discharge_file, output_path)
discharge.water_balance(discharge_file, output_path)

evap.components(h5_file,
                points_file,
                start_date=start_date,
                out_dir=output_path,
                dem=dem_file,
                interactive=False)

overland.numbers(h5_file,
                 flow_links_file,
                 start_date=start_date,
                 out_dir=output_path)

overland.xy(h5_file,
            timeseries_locations=flow_points_file,
            start_date=start_date,
            dem_file=dem_file,
            out_dir=output_path)


soil.times(os.path.join(data_path, '76008.h5'),
           timeseries_locations=points_file,
           selected_layers=3,
           dem=dem_file,
           out_dir=output_path,
           interactive=False,
           point=1)

soil.points(os.path.join(data_path, '76008.h5'),
            timeseries_locations=points_file,
            selected_layers=3,
            dem=dem_file,
            out_dir=output_path,
            interactive=False,
            timestep=3,
            video=False
            )

table.points(h5_file,
             timeseries_locations=points_file,
             start_date=start_date,
             out_dir=output_path,
             dem=dem_file)

table.area(h5_file,
           dem=dem_file,
           out_dir=output_path,
           interactive=False,
           timestep=5,
           time_interval=1,
           video=False,
           use_elevation=False)

table.area3d(h5_file,
             dem=dem_file,
             out_dir=output_path,
             interactive=False,
             azi=150)

water.balance(h5_file,
              timeseries_locations=points_file,
              start_date=start_date,
              out_dir=output_path,
              dem=dem_file,
              interactive=False)
