from setuptools import setup

setup(
    name='shetranio',
    version='0.1.0',
    packages=['shetranio', 'shetranio.setup'],
    url='https://github.com/nclwater/shetranio',
    license='MIT',
    author='Fergus McClean',
    author_email='fergus.mcclean@ncl.ac.uk',
    description='A python package to complement the SHETran hydrological model.',
    install_requires=[
        'numpy',
        'h5py',
        'matplotlib',
        'pandas',
        'beautifulsoup4'
    ]
)
