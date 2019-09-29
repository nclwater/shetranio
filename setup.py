from setuptools import setup

setup(
    name='shetran',
    version='0.1',
    packages=['shetran', 'shetran.plot'],
    url='https://github.com/fmcclean/shetran',
    license='MIT',
    author='Fergus McClean',
    author_email='f.mcclean2@ncl.ac.uk',
    description='A python package to complement the SHETRAN hydrological model.', install_requires=['numpy',
                                                                                                    'matplotlib',
                                                                                                    'pandas', 'PyQt5',
                                                                                                    'pyqtlet']
)
