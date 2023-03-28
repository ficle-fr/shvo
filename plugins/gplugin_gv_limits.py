from draw_engine import DrawEngine
from shvo import DrawEngineDirector, PluginBase, ToDockBase
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import QPushButton, QWidget, QVBoxLayout
from PyQt5.QtCore import QObject
import matplotlib.pyplot as plt
import PyQt5
import matplotlib
matplotlib.use('Qt5Agg')


class MplCanvas(FigureCanvas):
    def __init__(self, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(5, 4))
        self.axes = self.fig.add_subplot(111)
        self.axes.grid()

        lim = self.axes.get_xlim()
        self.refreshVLines(self.axes.get_xlim())
        super(MplCanvas, self).__init__(self.fig)
        cid = self.fig.canvas.mpl_connect('button_press_event', self.onClick)

    def setObserver(self, observer=None):
        self.observer = observer

    def refreshVLines(self, limits=None):
        if limits is not None:
            self.x1 = limits[0]
            self.x2 = limits[1]
        self.line1 = self.axes.axvline(self.x1, ls='--', c='red')
        self.line2 = self.axes.axvline(self.x2, ls='--', c='red')

    def onClick(self, event):
        if abs(event.xdata - self.x1) < abs(event.xdata - self.x2):
            curr_line = self.line1
            self.x1 = event.xdata
            if self.observer is not None:
                self.observer.onXLeftChange(self.x1)
        else:
            curr_line = self.line2
            self.x2 = event.xdata
            if self.observer is not None:
                self.observer.onXRightChange(self.x2)

        curr_line.set_xdata(event.xdata)
        self.draw()

class ToDock(ToDockBase):
    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout()
        self.mpl = MplCanvas()
        lay.addWidget(self.mpl)
        self.setLayout(lay)

    def postAdd(self):
        color = self.mpl.palette().color(PyQt5.QtGui.QPalette.Background).\
            getRgbF()
        self.mpl.fig.set_facecolor(color)
        self.mpl.axes.set_facecolor(color)

class EngineCache:
    def __init__(self, e):
        self.engine = e

class Plugin(DrawEngineDirector, PluginBase):
    def __init__(self):
        self.to_dock = ToDock()
        self.to_dock.mpl.setObserver(self)
        self.caches = []
        self.title = "Intensity limits"

    def onEngineActivated(self, e):
        self.engine = e
        self.engine.addDirector(self)

        self.cache = next((c for c in self.caches if c.engine == e), None)
        if self.cache == None:
            self.cache = EngineCache(e)
            self.caches.append(self.cache)

        if self.engine.img_origin is not None:
            self._redraw()

    def onImageChange(self):
        self.x_left, self.x_right = np.iinfo(self.engine.img_origin.dtype).min, \
            np.iinfo(self.engine.img_origin.dtype).max
        self.counts, self.bins = np.histogram(self.engine.img_origin)
        self._redraw()

    @ property
    def counts(self):
        return self.cache.counts

    @ counts.setter
    def counts(self, arg):
        self.cache.counts = arg

    @ property
    def bins(self):
        return self.cache.bins

    @ bins.setter
    def bins(self, arg):
        self.cache.bins = arg

    @ property
    def x_left(self):
        return self.cache.x_left

    @ x_left.setter
    def x_left(self, arg):
        self.cache.x_left = arg

    @ property
    def x_right(self):
        return self.cache.x_right

    @ x_right.setter
    def x_right(self, arg):
        self.cache.x_right = arg

    def onXLeftChange(self, arg):
        self.x_left = arg
        self.doCommands()

    def onXRightChange(self, arg):
        self.x_right = arg
        self.doCommands()

    def _redraw(self):
        self.to_dock.mpl.axes.cla()
        self.to_dock.mpl.axes.stairs(self.counts, self.bins)
        self.to_dock.mpl.axes.grid()
        self.to_dock.mpl.refreshVLines((self.x_left, self.x_right))
        self.to_dock.mpl.draw()


    def doCommands(self):
        if self.command_line is not None:
            cmd = "app.draw(\"gv_limits\", \"gv\", min = {xl}, max = {xr})".\
                format(xl=int(self.x_left), xr=int(self.x_right))
            self.command_line.exec(cmd)
