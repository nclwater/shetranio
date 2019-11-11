# SHETran I/O

## Installation

```
pip install shetranio
```

## Usage

```python
from shetranio import Model

model = Model('library_file.xml')
values = model.hdf.overland_flow.get_element(100)
times = model.hdf.overland_flow.times

```
