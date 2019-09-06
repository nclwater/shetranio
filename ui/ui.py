import sys
from shetran.hdf import Hdf, Geometries
from shetran.dem import Dem
import argparse
from pyqtlet import L, MapWidget
import numpy as np
import os
import json
from PyQt5.QtWidgets import QRadioButton, QHBoxLayout, QDesktopWidget, QLabel, QComboBox, QProgressBar, QApplication, QMainWindow, QSizePolicy, QPushButton, QFileDialog, QVBoxLayout, QWidget
from PyQt5.QtCore import pyqtSignal, pyqtSlot, QJsonValue, QThread

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


parser = argparse.ArgumentParser()
parser.add_argument('-h5')
parser.add_argument('-dem')
args = parser.parse_args()


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
                names = {'h5': 'Select a SHETRAN output file',
                         'dem': 'Select a DEM for the same catchment'}
                fileName, _ = QFileDialog.getOpenFileName(self, names[attribute], "",
                                                          "All Files (*);;HDF5 files (*.h5)", options=options)
                if fileName:
                    self.__setattr__(attribute, fileClass(fileName))

            else:
                print(args)
                self.__setattr__(attribute, fileClass(args.__getattribute__(attribute)))

        row1 = QHBoxLayout()
        row2 = QHBoxLayout()
        row3 = QHBoxLayout()

        self.mainWidget = QWidget(self)
        self.mainWidget.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.mainWidget.setGeometry(0,0,1000,1000)
        self.paths = QLabel(text=os.path.abspath(self.h5.path))
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

        self.variables = [var for var in self.h5.variables if var.is_spatial]

        self.variable = self.variables[0]

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
        self.element_number = 1


        self.progress = QProgressBar(self)

        row2.addWidget(self.progress)

        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.plotCanvas = PlotCanvas(width=5, height=4)
        row3.addWidget(self.plotCanvas)

        self.mapCanvas = MapCanvas()
        row3.addWidget(self.mapCanvas)

        self.mapCanvas.progress.connect(self.set_progress)
        self.mapCanvas.clickedElement.connect(self.update_data)
        self.mapCanvas.loaded.connect(self.on_load)

        self.mapCanvas.add_data(self.h5, self.dem)

        self.pan = QPushButton(parent=self, text='Reset View')
        row1.addWidget(self.pan)
        self.pan.clicked.connect(self.mapCanvas.pan_to)

        self.switch_elements()
        rows = QVBoxLayout()
        for row in [row1, row2, row3]:
            w = QWidget()
            w.setLayout(row)
            rows.addWidget(w)

        self.mainWidget.setLayout(rows)
        self.setCentralWidget(self.mainWidget)

        centerPoint = QDesktopWidget().availableGeometry().center()
        geom = self.frameGeometry()
        geom.moveCenter(centerPoint)
        self.move(geom.topLeft())
        self.show()
        self.activateWindow()

    def set_variable(self, variable_index):
        self.variable = self.variables[variable_index]
        self.switch_elements()

    def update_data(self, element):
        self.element_number = element.number
        self.plotCanvas.line[0].set_data(self.variable.times, self.variable.get_values(self.element_number))
        self.plotCanvas.axes.relim()
        self.plotCanvas.axes.autoscale_view()
        self.plotCanvas.axes.set_title('Element {}'.format(self.element_number))
        self.plotCanvas.axes.set_ylabel(self.variable.long_name)
        self.plotCanvas.fig.tight_layout()
        self.plotCanvas.draw()


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
            self.mapCanvas.show_rivers(self.h5)
        else:
            self.mapCanvas.show_land(self.h5)

    def on_load(self):
        self.progress.hide()
        self.plotCanvas.show()
        self.mapCanvas.show()

    def set_progress(self, progress):
        self.progress.setValue(progress)

    def download_values(self):
        array = np.array(self.get_values()).transpose()
        dialog = QFileDialog.getSaveFileName(directory=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                                    '{} at {}.csv'.format(self.variable.long_name,
                                                                                      self.element_number)),
                                             filter="CSV Files (*.csv)")
        if dialog[0] != '':
            np.savetxt(dialog[0], array, fmt='%.3f',
                       header='{} at {}\ntime,value'.format(self.variable.long_name, self.element_number),
                       delimiter=',', comments='')


class PlotCanvas(FigureCanvas):

    def __init__(self, parent=None,  width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
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

        ax = self.figure.add_subplot(111)
        self.line = ax.plot([], [], 'r-')
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
            if element.number <= h5.overland_flow.values.shape[0]:
                self.group.removeLayer(element)
            else:
                self.group.addLayer(element)

    def show_rivers(self, h5):
        for element in self.elements:
            if element.number > h5.overland_flow.values.shape[0]:
                self.group.removeLayer(element)
            else:
                self.group.addLayer(element)



if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())
