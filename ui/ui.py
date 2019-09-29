import sys
from shetran.hdf import Geometries
from shetran.model import Model
import argparse
from pyqtlet import L, MapWidget
import numpy as np
import os
import json
from PyQt5.QtWidgets import QFrame, QSplitter, QRadioButton, QHBoxLayout, QLabel, QComboBox, QProgressBar, \
    QApplication, QMainWindow, QSizePolicy, QPushButton, QFileDialog, QVBoxLayout, QWidget, QSlider, QScrollArea
from PyQt5.QtCore import pyqtSignal, pyqtSlot, QJsonValue, QThread, Qt
import pandas as pd
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

    def __init__(self, shape, element_number, signal):
        super().__init__(shape, {'weight': self.default_weight, 'fillOpacity': 0.8})
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

        self.models = []
        self.args = args
        self.variables = None
        self.variable = None

        self.modelDropDown = QComboBox()
        self.modelDropDown.activated.connect(self.set_model)

        self.slider = QSlider(parent=self, orientation=Qt.Horizontal, )
        self.slider.valueChanged.connect(self.set_time)

        self.add_model()
        self.model = self.models[0]

        row1 = QHBoxLayout()
        row2 = QHBoxLayout()
        row3 = QHBoxLayout()
        row4 = QSplitter()

        self.mainWidget = QWidget(self)
        self.mainWidget.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        row1.addWidget(self.modelDropDown)

        self.plot_on_click = QRadioButton(text='Click')
        self.plot_on_hover = QRadioButton(text='Hover')

        self.plot_on_click.toggle()

        self.plot_on_click.toggled.connect(self.set_hover)
        self.plot_on_hover.toggled.connect(self.set_hover)

        self.plot_on_click.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        self.plot_on_hover.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)

        self.plot_on_click.setGeometry(510, 10, 100, 50)
        self.plot_on_hover.setGeometry(600, 10, 100, 50)

        self.variableDropDown = QComboBox()
        for variable in self.model.h5.spatial_variables:
            self.variableDropDown.addItem(variable.long_name)
        self.variableDropDown.activated.connect(self.set_variables)

        self.download_button = QPushButton(text='Download')
        self.download_button.clicked.connect(self.download_values)

        self.add_model_button = QPushButton(text='Add Model')
        self.add_model_button.clicked.connect(self.add_model)

        row2.addWidget(self.variableDropDown)
        row2.addWidget(self.add_model_button)
        row2.addWidget(self.download_button)
        row2.addWidget(self.plot_on_click)
        row2.addWidget(self.plot_on_hover)

        self.title = 'SHETran Results Viewer'

        self.element_number = None
        self.time = 0

        self.progress = QProgressBar(self)

        row2.addWidget(self.progress)
        row3.addWidget(self.slider)

        self.setWindowTitle(self.title)
        self.plotCanvas = PlotCanvas()
        row4.addWidget(self.plotCanvas)

        map_and_legend_layout = QVBoxLayout()

        self.mapCanvas = MapCanvas()
        self.legendCanvas = LegendCanvas()
        map_and_legend_layout.addWidget(self.mapCanvas)
        map_and_legend_layout.addWidget(self.legendCanvas)

        map_and_legend = QWidget()
        map_and_legend.setLayout(map_and_legend_layout)

        width = 500
        height = 400
        self.plotCanvas.setMinimumWidth(width)
        self.plotCanvas.setMinimumHeight(height)
        map_and_legend.setMinimumWidth(width)
        map_and_legend.setMinimumHeight(height)
        self.mainWidget.setMinimumHeight(600)
        self.mainWidget.setMinimumWidth(width*2)

        row4.addWidget(map_and_legend)
        row4.setCollapsible(0, False)
        row4.setCollapsible(1, False)

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
        self.set_variables(0)
        self.show()
        self.activateWindow()

    def add_model(self):
        if self.args.l is None:
            library_path = QFileDialog.getOpenFileName(
                self,
                'Choose a library file',
                "",
                "XML files (*.xml);;All Files (*)",
                options=QFileDialog.Options())[0]
        else:
            library_path = self.args.l
            self.args.l = None
        model = Model(library_path)
        self.models.append(model)
        self.modelDropDown.addItem('{} - {}'.format(len(self.models), model.library))
        if len(self.models) > 1:
            self.set_variables(self.variableDropDown.currentIndex())

    def set_variables(self, variable_index):
        self.variables = [model.h5.spatial_variables[variable_index] for model in self.models]
        self.variable = self.variables[self.models.index(self.model)]
        self.slider.setMaximum(len(self.variables[0].times) - 1)
        self.switch_elements()
        self.set_time(self.time)

    def update_data(self, element):
        self.element_number = element.number
        self.plotCanvas.update_data(element.number, self.variables)

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
        if self.variables[0].is_river:
            self.mapCanvas.show_rivers()
            self.element_number = self.mapCanvas.river_elements[0].number
        else:
            self.mapCanvas.show_land()
            self.element_number = self.mapCanvas.land_elements[0].number

        self.plotCanvas.update_data(self.element_number, self.variables)

    def on_load(self):
        self.progress.hide()
        self.plotCanvas.show()
        self.mapCanvas.show()

    def set_progress(self, progress):
        self.progress.setValue(progress)

    def download_values(self):
        if not self.element_number:
            return
        array = pd.DataFrame({'time': self.variables[0].times[:],
                              **{'value_{}'.format(i): var.get_element(self.element_number).round(3) for i, var in
                                 enumerate(self.variables)}})

        directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), '{} at {}.csv'.format(
            self.variables[0].long_name, self.element_number).replace('/', ' per '))

        dialog = QFileDialog.getSaveFileName(directory=directory, filter="CSV Files (*.csv)")
        if dialog[0] != '':
            with open(dialog[0], 'w') as f:
                f.write('{} at {}\n'.format(self.variables[0].long_name, self.element_number))
                array.to_csv(f, index=False)

    def set_time(self, time):
        self.time = time
        self.mapCanvas.set_time(self.time, self.variable)
        self.plotCanvas.set_time(self.variable.times[self.time], self.mapCanvas.norm)
        self.legendCanvas.set_time(self.mapCanvas.norm)

    def set_model(self, model_index):
        self.model = self.models[model_index]
        self.variable = self.variables[model_index]
        self.set_time(self.time)


class LegendCanvas(FigureCanvas):
    def __init__(self):

        self.fig = Figure(figsize=(7, 1))
        self.fig.subplots_adjust(bottom=0.5)

        self.fig.set_constrained_layout_pads(h_pad=100)
        FigureCanvas.__init__(self, self.fig)
        self.setFixedHeight(50)
        self.axes = self.fig.add_subplot(111)
        self.sm = ScalarMappable(cmap=colormap, norm=Normalize(vmin=0, vmax=1))
        self.sm.set_array(np.array([]))
        self.colorbar = colorbar(self.sm, cax=self.axes,
                                 pad=1,
                                 orientation='horizontal')
        self.fig.patch.set_visible(False)
        self.setStyleSheet("background-color:transparent;")

    def set_time(self, norm):
        self.sm.set_norm(norm)
        self.draw()


class PlotCanvas(FigureCanvas):

    def __init__(self, parent=None):

        self.fig = Figure()
        self.axes = self.fig.add_subplot(111)
        self.fig.subplots_adjust(bottom=0.2, top=0.9)
        self.sm = ScalarMappable(cmap=colormap, norm=Normalize(vmin=0, vmax=1))
        self.sm.set_array(np.array([]))
        self.fig.patch.set_visible(False)

        FigureCanvas.__init__(self, self.fig)
        self.setStyleSheet("background-color:transparent;")
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                                   QSizePolicy.Expanding,
                                   QSizePolicy.Expanding)

        self.lines = []
        self.time = None

    def update_data(self, element_number, variables):

        for line in self.lines:
            self.axes.lines.remove(line)
        self.lines = []

        for i, var in enumerate(variables):

            pd.Series(var.get_element(element_number),
                      index=var.times).plot(color='C{}'.format(i), ax=self.axes, label=i+1)

            self.lines.append(self.axes.lines[-1])

        self.set_backgroud()

        self.axes.relim()
        self.axes.autoscale_view()

        self.axes.set_title('Element {}'.format(element_number))
        self.axes.set_ylabel(variables[0].long_name)
        self.axes.set_xlabel('Time')
        if len(variables) > 1:
            self.axes.legend()
        self.draw()

    def set_backgroud(self):
        self.axes.patch.set_visible(False)

    def set_time(self, time, norm):
        if self.time in self.axes.lines:
            self.axes.lines.remove(self.time)
        self.time = self.axes.axvline(time, color='black', linewidth=0.8)
        self.set_backgroud()
        self.sm.set_norm(norm)
        self.draw()


class MapCanvas(QFrame):
    clickedElement = pyqtSignal(object)
    loaded = pyqtSignal()
    progress = pyqtSignal(float)

    def __init__(self, parent=None):
        self.mapWidget = MapWidget()
        QWidget.__init__(self, self.mapWidget)
        self.setParent(parent)

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
        self.visible_elements = None
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
        self.select_element(self.land_elements[0])

    def show_rivers(self):
        for element in self.land_elements:
            self.group.removeLayer(element)
        for element in self.river_elements:
            self.group.addLayer(element)
        self.visible_elements = self.river_elements
        self.select_element(self.river_elements[0])

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
