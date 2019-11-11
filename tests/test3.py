from shetranio import hdf

h = hdf.Hdf('sample_data/output_Wansbeck_at_Mitford_shegraph.h5')

h.to_geom('sample_data/Wansbeck_at_Mitford_Dem.txt')

h = hdf.Hdf('sample_data/output_Kilham_shegraph.h5')

h.to_geom('sample_data/Kilham_dem200.txt')
