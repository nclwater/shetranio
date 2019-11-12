# SHETran I/O

## Installation

```
pip install shetranio
```

### Dependencies
  - h5py
  - pandas
  - beautifulsoup4
 
To easily install shetranio and dependencies into a new environment:

```
conda env create -f https://github.com/nclwater/shetranio/blob/master/environment.yml
conda activate shetranio
```

#### Optional dependencies

Some features also require gdal and netCDF4. It is recommended to install these using conda.

## Usage

```python
from shetranio import Model

model = Model('library_file.xml')
values = model.hdf.overland_flow.get_element(100)
times = model.hdf.overland_flow.times

```
