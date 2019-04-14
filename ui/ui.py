import sys
from shetran.hdf import Hdf, Geometries
from shetran.dem import Dem
import argparse
from pyqtlet import L, MapWidget

from PyQt5.QtWidgets import QApplication, QMainWindow, QSizePolicy, QLineEdit, QPushButton, QFileDialog, QVBoxLayout, QWidget
from PyQt5.QtCore import pyqtSignal, pyqtSlot, QJsonValue

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


parser = argparse.ArgumentParser()
parser.add_argument('-h5')
parser.add_argument('-dem')
args = parser.parse_args()


class App(QMainWindow):

    def __init__(self):
        super().__init__()

        for attribute, fileClass in [['h5', Hdf], ['dem', Dem]]:

            if not hasattr(args, attribute):
                options = QFileDialog.Options()

                fileName, _ = QFileDialog.getOpenFileName(self, "QFileDialog.getOpenFileName()", "",
                                                          "All Files (*);;Python Files (*.py)", options=options)
                if fileName:
                    self.__setattr__(attribute, fileClass(fileName))

            else:
                self.__setattr__(attribute, fileClass(args.__getattribute__(attribute)))

        self.left = 0
        self.top = 0
        self.title = 'SHETran Results Viewer'
        self.width = 1000
        self.height = 500

        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.plotCanvas = PlotCanvas(self, width=5, height=4)

        self.mapCanvas = MapCanvas(self)

        self.mapCanvas.clickedElement.connect(self.update_data)

        self.show()

    def update_data(self, element):

        idx = self.h5.unique_numbers.tolist().index(element)

        if idx > self.h5.overland_flow.values.shape[0]:
            return

        self.plotCanvas.element = element

        new_data = self.h5.overland_flow.values[idx, 0, :]

        self.plotCanvas.line[0].set_data(range(len(new_data)), new_data)
        self.plotCanvas.axes.relim()
        self.plotCanvas.axes.autoscale_view()
        self.plotCanvas.axes.set_title('{} Overland Flow'.format(self.plotCanvas.element))
        self.plotCanvas.draw()


class PlotCanvas(FigureCanvas):

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        self.element = 0

        FigureCanvas.__init__(self, fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                                   QSizePolicy.Expanding,
                                   QSizePolicy.Expanding)
        self.setGeometry(10,10,480,480)
        fig.tight_layout()

        data = self.parent().h5.overland_flow.values[self.element, 0, :]
        ax = self.figure.add_subplot(111)
        self.line = ax.plot(data, 'r-')
        ax.set_title('{} Overland Flow'.format(self.element))
        self.draw()


class MapCanvas(QWidget):
    clickedElement = pyqtSignal(int)

    def __init__(self, parent=None):
        self.mapWidget = MapWidget()
        QWidget.__init__(self, self.mapWidget)
        self.setParent(parent)
        self.setGeometry(500,0,500,500)

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.mapWidget)
        self.setLayout(self.layout)

        self.map = L.map(self.mapWidget)
        self.map.setView([12.97, 77.59], 10)

        L.tileLayer('http://{s}.tile.osm.org/{z}/{x}/{y}.png').addTo(self.map)

        geoms = Geometries(self.parent().h5, self.parent().dem)

        class Element(L.polygon):

            @pyqtSlot(QJsonValue)
            def _signal(self, event):
                self.mapWidget.parent().clickedElement.emit(self.property('name'))

            def __init__(self, latLngs, element_number):
                super().__init__(latLngs)
                self.setProperty('name', element_number)
                self._connectEventToSignal('click', '_signal')

        group = L.featureGroup()
        group.addTo(self.map)

        for geom, number in zip(geoms, self.parent().h5.unique_numbers):
            coords = [list(reversed(coord)) for coord in geom['coordinates'][0]]
            group.addLayer(Element(coords, number))

        def pan_to(bounds):
            ne = bounds['_northEast']

            sw = bounds['_southWest']
            latlng = [sw['lat']+(ne['lat']-sw['lat'])/2, sw['lng']+(ne['lng']-sw['lng'])/2]
            self.map.panTo(latlng)

        group.getJsResponse('{}.getBounds()'.format(group.jsName), pan_to)


        self.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())
