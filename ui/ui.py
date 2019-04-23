import sys
from shetran.hdf import Hdf, Geometries
from shetran.dem import Dem
import argparse
from pyqtlet import L, MapWidget
import numpy as np
import os
import json
from PyQt5.QtWidgets import QRadioButton, QLabel, QComboBox, QProgressBar, QApplication, QMainWindow, QSizePolicy, QLineEdit, QPushButton, QFileDialog, QVBoxLayout, QWidget
from PyQt5.QtCore import pyqtSignal, pyqtSlot, QJsonValue, QThread


from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


parser = argparse.ArgumentParser()
parser.add_argument('-h5')
parser.add_argument('-dem')
args = parser.parse_args()

variables = dict(
        potential_evapotranspiration=dict(name='Potential Evapotranspiration'),
        transpiration=dict(name='Transpiration'),
        surface_evaporation=dict(name='Surface Evaporation'),
        evaporation_from_interception=dict(name='Evaporation from Interception'),
        drainage_from_interception=dict(name='Drainage from Interception'),
        canopy_storage=dict(name='Canopy Storage'),
        vertical_flows=dict(name='Vertical Flows'),
        snow_depth=dict(name='Snow Depth'),
        ph_depth=dict(name='Phreatic Depth'),
        overland_flow=dict(name='Overland Flow'),
        surface_depth=dict(name='Surface Depth'),
        surface_water_potential=dict(name='Surface Water Potential'),
        theta=dict(name='Theta'),
        total_sediment_depth=dict(name='Total Sediment Depth'),
        surface_erosion_rate=dict(name='Surface Erosion Rate'),
        sediment_discharge_rate=dict(name='Sediment Discharge Rate'),
        mass_balance_error=dict(name='Mass Balance Error'))


class Group(L.featureGroup):
    def __init__(self):
        super().__init__()

    def update_style(self, style):
        self.runJavaScript("{}.setStyle({})".format(self.jsName, json.dumps(style)))

    def remove_listeners(self):
        self.runJavaScript("{}.invoke('off')".format(self.jsName))


class Element(L.polygon):
    default_weight = 0.5

    @pyqtSlot(QJsonValue)
    def _signal(self):
        self.signal.emit(self)

    def __init__(self, latLngs, element_number, signal):
        super().__init__(latLngs, {'weight': self.default_weight})
        self.signal = signal
        self.number = element_number
        self.setProperty('element_number', element_number)
        self._connectEventToSignal('click', '_signal')

    def onclick(self):
        self._connectEventToSignal('click', '_signal')

    def onhover(self):
        self._connectEventToSignal('mouseover', '_signal')

    def update_style(self, style):
        self.runJavaScript("{}.setStyle({})".format(self.jsName, json.dumps(style)))


class App(QMainWindow):

    def __init__(self):
        super().__init__()

        for attribute, fileClass in [['h5', Hdf], ['dem', Dem]]:

            if getattr(args, attribute) is None:
                options = QFileDialog.Options()

                fileName, _ = QFileDialog.getOpenFileName(self, "QFileDialog.getOpenFileName()", "",
                                                          "All Files (*);;Python Files (*.py)", options=options)
                if fileName:
                    self.__setattr__(attribute, fileClass(fileName))

            else:
                print(args)
                self.__setattr__(attribute, fileClass(args.__getattribute__(attribute)))


        self.paths = QLabel(self)
        self.paths.setText(os.path.abspath(self.h5.path))

        self.plot_on_click = QRadioButton(self, text='Click')
        self.plot_on_hover = QRadioButton(self, text='Hover')

        self.plot_on_click.toggle()

        self.plot_on_click.toggled.connect(self.set_hover)
        self.plot_on_hover.toggled.connect(self.set_hover)

        self.plot_on_click.setGeometry(510, 10, 100, 50)
        self.plot_on_hover.setGeometry(600, 10, 100, 50)

        self.paths.setGeometry(10,60,1000,50)

        self.variables = [{'variable': key, **val} for key, val in variables.items() if self.h5.__getattribute__(key) is not None]

        self.variable = self.variables[0]

        self.variableDropDown = QComboBox(self)
        for variable in self.variables:
            self.variableDropDown.addItem(variable['name'])
        self.variableDropDown.activated.connect(self.set_variable)
        self.variableDropDown.setGeometry(10,10,500, 50)
        self.left = 0
        self.top = 0
        self.title = 'SHETran Results Viewer'
        self.width = 1000
        self.height = 600
        self.element_number = 1
        self.show()

        self.progress = QProgressBar(self)
        self.progress.setGeometry(100,100, 200, 500)
        self.progress.show()

        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.plotCanvas = PlotCanvas(*self.get_values(), element=self.element_number,
                                     variable=self.variable['variable'],
                                     parent=self, width=5, height=4)

        self.mapCanvas = MapCanvas(self)

        self.mapCanvas.progress.connect(self.set_progress)
        self.mapCanvas.clickedElement.connect(self.update_data)
        self.mapCanvas.loaded.connect(self.on_load)

        self.mapCanvas.add_data(self.h5, self.dem)

        self.pan = QPushButton(parent=self, text='Reset View')
        self.pan.setGeometry(700,10,100,50)
        self.pan.show()

        self.pan.clicked.connect(self.mapCanvas.pan_to)

        self.switch_elements()


    def set_variable(self, variable_index):
        self.variable = self.variables[variable_index]
        self.switch_elements()

    def update_data(self, element):
        self.element_number = element.number

        new_data, times = self.get_values()

        self.plotCanvas.line[0].set_data(times, new_data)
        self.plotCanvas.axes.relim()
        self.plotCanvas.axes.autoscale_view()
        self.plotCanvas.axes.set_title('{} {}'.format(self.element_number, self.variable['name']))
        self.plotCanvas.draw()

    def get_values(self):
        var = self.variable['variable']
        idx = self.h5.element_numbers.tolist().index(self.element_number)
        values = self.h5.__getattribute__(var).values
        times = self.h5.__getattribute__(var).times
        if var in ['overland_flow', 'surface_depth']:
            if idx < self.h5.overland_flow.values.shape[0]:
                if var == 'overland_flow':
                    return values[idx, :, :].max(axis=0), times
                else:
                    return values[idx, :], times
            else:
                return []
        elif var == 'surface_depth':
            if idx < self.h5.overland_flow.values.shape[0]:
                return values[idx, 0, :], times
            else:
                return [], []
        else:
            if self.element_number in self.h5.number.square:
                index = np.where(self.h5.number.square == self.element_number)
                return values[index[0][0], index[1][0]], times
            else:
                return [], []

    def set_hover(self):
        class Thread(QThread):
            def __init__(self, parent=None):
                QThread.__init__(self)
                self.setParent(parent)

            def __del__(self):
                self.wait()

            def run(self):
                if self.parent().plot_on_click.isChecked():
                    self.parent().mapCanvas.set_onclick()
                else:
                    self.parent().mapCanvas.set_onhover()

        Thread(self).start()

    def switch_elements(self):
        if self.variable['variable'] in ['overland_flow', 'surface_depth']:
            self.mapCanvas.show_land(self.h5)
        else:
            self.mapCanvas.show_rivers(self.h5)

    def on_load(self):
        self.progress.hide()
        self.plotCanvas.show()
        self.mapCanvas.show()

    def set_progress(self, progress):
        self.progress.setValue(progress)


class PlotCanvas(FigureCanvas):

    def __init__(self, data, times, element, variable, parent=None,  width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)

        FigureCanvas.__init__(self, fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                                   QSizePolicy.Expanding,
                                   QSizePolicy.Expanding)
        self.setGeometry(10,110,480,480)
        fig.tight_layout()

        ax = self.figure.add_subplot(111)
        self.line = ax.plot(times, data, 'r-')
        ax.set_title('{} {}'.format(element, variable))
        self.draw()


class MapCanvas(QWidget):
    clickedElement = pyqtSignal(object)
    loaded = pyqtSignal()
    progress = pyqtSignal(float)

    def __init__(self, parent=None):
        self.mapWidget = MapWidget()
        QWidget.__init__(self, self.mapWidget)
        self.setParent(parent)
        self.setGeometry(500,100,500,500)

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.mapWidget)
        self.setLayout(self.layout)

        self.map = L.map(self.mapWidget)
        self.map.setZoom(10)

        self.group = Group()
        self.group.addTo(self.map)

        self.clickedElement.connect(self.select_element)
        self.element = None
        self.elements = []

    def pan_to(self):

        def _pan_to(bounds):
            self.map.fitBounds([list(b.values()) for b in bounds.values()])

        self.group.getJsResponse('{}.getBounds()'.format(self.group.jsName), _pan_to)



    def add_data(self, h5, dem):

        L.tileLayer('http://{s}.tile.osm.org/{z}/{x}/{y}.png').addTo(self.map)

        geoms = Geometries(h5, dem)

        prog = 0
        for geom, number in zip(geoms, h5.element_numbers):
            coords = [list(reversed(coord)) for coord in geom['coordinates'][0]]
            self.elements.append(Element(coords, number, self.clickedElement))
            self.group.addLayer(self.elements[-1])
            prog += 100/len(geoms)
            self.progress.emit(prog)

        self.pan_to()

        self.loaded.emit()



    def set_onclick(self):
        self.group.remove_listeners()
        for element in self.elements:
            element.onclick()

    def set_onhover(self):
        self.group.remove_listeners()
        for element in self.elements:
            element.onhover()

    def select_element(self, element):
        if self.element is not None:
            self.element.update_style({'weight': self.element.default_weight})

        self.element = element
        element.update_style({'weight': 3})

    def show_land(self, h5):
        for element in self.elements:
            if element.number >= h5.overland_flow.values.shape[0]:
                self.group.removeLayer(element)
            else:
                self.group.addLayer(element)

    def show_rivers(self, h5):
        for element in self.elements:
            if element.number < h5.overland_flow.values.shape[0]:
                self.group.removeLayer(element)
            else:
                self.group.addLayer(element)



if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())
