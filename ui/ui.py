import sys
from shetran.hdf import Geometries
from shetran.model import Model
import argparse
from pyqtlet import L, MapWidget
import numpy as np
import os
import json
from PyQt5.QtWidgets import QFrame, QSplitter, QRadioButton, QHBoxLayout, QDesktopWidget, QLabel, QComboBox, QProgressBar, QApplication, QMainWindow, QSizePolicy, QPushButton, QFileDialog, QVBoxLayout, QWidget, QSlider
from PyQt5.QtCore import pyqtSignal, pyqtSlot, QJsonValue, QThread, Qt

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.colors import Normalize, to_hex
from matplotlib.cm import get_cmap
from matplotlib.pyplot import colorbar
from matplotlib.cm import ScalarMappable


parser = argparse.ArgumentParser()
parser.add_argument('-l')
args = parser.parse_args()


class Group(L.featureGroup):
    def __init__(self):
        super().__init__()

    def update_style(self, style):
        self.runJavaScript("{}.setStyle({})".format(self.jsName, json.dumps(style)))


class Element(L.polygon):
    default_weight = 0.1

    @pyqtSlot(QJsonValue)
    def _signal(self):
        self.signal.emit(self)

    def __init__(self, latLngs, element_number, signal):
        super().__init__(latLngs, {'weight': self.default_weight, 'fillOpacity': 0.8})
        self.signal = signal
        self.number = element_number
        self.setProperty('element_number', element_number)
        self._connectEventToSignal('click', '_signal')

    def onclick(self):
        self.runJavaScript("{}.off()".format(self.jsName))
        self._connectEventToSignal('click', '_signal')

    def onhover(self):
        self.runJavaScript("{}.off()".format(self.jsName))
        self._connectEventToSignal('mouseover', '_signal')

    def update_style(self, style):
        self.runJavaScript("{}.setStyle({})".format(self.jsName, json.dumps(style)))

colormap = 'RdYlGn'

class App(QMainWindow):

    def __init__(self):
        super().__init__()

        library_path = args.l
        if library_path is None:
            library_path, _ = QFileDialog.getOpenFileName(self,
                                                          'Choose a library file',
                                                          "",
                                                          "All Files (*);;XML files (*.xml)",
                                                          options=QFileDialog.Options())

        self.model = Model(library_path)

        row1 = QHBoxLayout()
        row2 = QHBoxLayout()
        row3 = QHBoxLayout()
        row4 = QSplitter()

        self.mainWidget = QWidget(self)
        self.mainWidget.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.mainWidget.setGeometry(0,0,1000,1000)
        self.paths = QLabel(text=os.path.abspath(self.model.h5.path))
        row1.addWidget(self.paths)

        self.plot_on_click = QRadioButton(text='Click')
        self.plot_on_hover = QRadioButton(text='Hover')

        self.plot_on_click.toggle()

        self.plot_on_click.toggled.connect(self.set_hover)
        self.plot_on_hover.toggled.connect(self.set_hover)

        self.plot_on_click.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        self.plot_on_hover.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)

        self.plot_on_click.setGeometry(510, 10, 100, 50)
        self.plot_on_hover.setGeometry(600, 10, 100, 50)

        self.variables = [var for var in self.model.h5.variables if var.is_spatial]

        self.variable = None

        self.variableDropDown = QComboBox()
        for variable in self.variables:
            self.variableDropDown.addItem(variable.long_name)
        self.variableDropDown.activated.connect(self.set_variable)

        self.download_button = QPushButton(text='Download')
        self.download_button.clicked.connect(self.download_values)

        row2.addWidget(self.variableDropDown)
        row2.addWidget(self.download_button)
        row2.addWidget(self.plot_on_click)
        row2.addWidget(self.plot_on_hover)

        self.left = 0
        self.top = 0
        self.title = 'SHETran Results Viewer'
        self.width = 1000
        self.height = 600
        self.element_number = None
        self.time = 0


        self.progress = QProgressBar(self)
        self.slider = QSlider(parent=self, orientation=Qt.Horizontal)
        self.slider.valueChanged.connect(self.set_time)

        row2.addWidget(self.progress)
        row3.addWidget(self.slider)

        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.plotCanvas = PlotCanvas(width=5, height=4)
        row4.addWidget(self.plotCanvas)

        self.mapCanvas = MapCanvas()
        row4.addWidget(self.mapCanvas)

        self.mapCanvas.progress.connect(self.set_progress)
        self.mapCanvas.clickedElement.connect(self.update_data)
        self.mapCanvas.loaded.connect(self.on_load)

        self.mapCanvas.add_data(self.model)

        self.pan = QPushButton(parent=self, text='Reset View')
        row1.addWidget(self.pan)
        self.pan.clicked.connect(self.mapCanvas.pan_to)

        rows = QVBoxLayout()
        for row in [row1, row2, row3]:
            w = QWidget()
            w.setLayout(row)
            w.setMaximumHeight(50)
            rows.addWidget(w)

        rows.addWidget(row4)

        self.mainWidget.setLayout(rows)
        self.setCentralWidget(self.mainWidget)

        centerPoint = QDesktopWidget().availableGeometry().center()
        geom = self.frameGeometry()
        geom.moveCenter(centerPoint)
        self.set_variable(0)
        self.set_time(self.time)
        self.move(geom.topLeft())
        self.show()
        self.activateWindow()

    def set_variable(self, variable_index):
        self.variable = self.variables[variable_index]
        self.slider.setMaximum(len(self.variable.times) - 1)
        self.switch_elements()
        self.set_time(self.time)

    def update_data(self, element):
        self.element_number = element.number
        self.plotCanvas.update_data(element.number, self.variable)


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
        if self.variable.is_river:
            self.mapCanvas.show_rivers()
        else:
            self.mapCanvas.show_land()

        self.element_number = None
        self.plotCanvas.clear_data()

    def on_load(self):
        self.progress.hide()
        self.plotCanvas.show()
        self.mapCanvas.show()

    def set_progress(self, progress):
        self.progress.setValue(progress)

    def download_values(self):
        if not self.element_number:
            return
        array = np.array([self.variable.times[:], self.variable.get_element(self.element_number)]).transpose()

        directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), '{} at {}.csv'.format(
            self.variable.long_name, self.element_number).replace('/', ' per '))

        dialog = QFileDialog.getSaveFileName(directory=directory, filter="CSV Files (*.csv)")
        if dialog[0] != '':
            np.savetxt(dialog[0], array, fmt='%.3f',
                       header='{} at {}\ntime,value'.format(self.variable.long_name, self.element_number),
                       delimiter=',', comments='')

    def set_time(self, time):
        self.time = time
        self.mapCanvas.set_time(self.time, self.variable)
        self.plotCanvas.set_time(self.variable.times[self.time], self.mapCanvas.norm)


class PlotCanvas(FigureCanvas):

    def __init__(self, parent=None,  width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        self.sm = ScalarMappable(cmap=colormap, norm=Normalize(vmin=0, vmax=1))
        self.sm.set_array(np.array([]))
        self.colorbar = colorbar(self.sm, ax=self.axes, aspect=40, fraction=0.2, pad=0.1)
        self.fig.patch.set_visible(False)
        self.axes.patch.set_visible(False)

        FigureCanvas.__init__(self, self.fig)
        self.setStyleSheet("background-color:transparent;")
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                                   QSizePolicy.Expanding,
                                   QSizePolicy.Expanding)
        self.setGeometry(10,110,480,480)
        self.fig.tight_layout()

        self.line = self.axes.plot([], [], 'r-')
        self.time = self.axes.axvline()
        self.draw()

    def update_data(self, element_number, variable):
        self.line[0].set_data(variable.times, variable.get_element(element_number))
        self.axes.relim()
        self.axes.autoscale_view()
        self.axes.set_title('Element {}'.format(element_number))
        self.axes.set_ylabel(variable.long_name)
        self.axes.set_xlabel('Time ({})'.format(variable.time_units))
        self.fig.tight_layout()
        self.draw()

    def set_time(self, time, norm):
        self.time.set_xdata([time, time])
        self.sm.set_norm(norm)
        self.draw()

    def clear_data(self):
        self.line[0].set_data([], [])
        self.axes.set_title('')
        self.axes.set_ylabel('')
        self.axes.set_xlabel('')
        self.draw()



class MapCanvas(QFrame):
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
        self.setLineWidth(10)
        self.setFrameShape(QFrame.StyledPanel)

        self.clickedElement.connect(self.select_element)
        self.element = None
        self.elements = []
        self.river_elements = []
        self.land_elements = []
        self.norm = None

    def pan_to(self):

        def _pan_to(bounds):
            self.map.fitBounds([list(b.values()) for b in bounds.values()])

        self.group.getJsResponse('{}.getBounds()'.format(self.group.jsName), _pan_to)



    def add_data(self, model):

        L.tileLayer('http://{s}.tile.osm.org/{z}/{x}/{y}.png').addTo(self.map)

        geoms = Geometries(model.h5, model.dem, srs=model.srid)

        prog = 0
        for geom, number in zip(geoms, model.h5.element_numbers):
            coords = [list(reversed(coord)) for coord in geom['coordinates'][0]]
            element = Element(coords, number, self.clickedElement)
            self.elements.append(element)
            if number in model.h5.land_elements:
                self.land_elements.append(element)
            else:
                self.river_elements.append(element)
            self.group.addLayer(element)
            prog += 100/len(geoms)
            self.progress.emit(prog)

        self.pan_to()

        self.loaded.emit()



    def set_onclick(self):
        for element in self.elements:
            element.onclick()

    def set_onhover(self):
        for element in self.elements:
            element.onhover()

    def select_element(self, element):
        if self.element is not None:
            self.element.update_style({'weight': self.element.default_weight})

        self.element = element
        element.update_style({'weight': 3})

    def show_land(self):
        for element in self.river_elements:
            self.group.removeLayer(element)
        for element in self.land_elements:
            self.group.addLayer(element)
        self.visible_elements = self.land_elements

    def show_rivers(self):
        for element in self.land_elements:
            self.group.removeLayer(element)
        for element in self.river_elements:
            self.group.addLayer(element)
        self.visible_elements = self.river_elements

    def set_time(self, time, variable):
        values = variable.get_time(time)
        cm = get_cmap(colormap)
        if np.all(values == 0):
            self.norm = Normalize(vmin=0, vmax=1)
        else:
            self.norm = Normalize(vmin=min(values), vmax=max(values))
        values = cm(self.norm(values))
        for element, value in zip(self.visible_elements, values):
            element.update_style({'fillColor': to_hex(value)})




if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())
