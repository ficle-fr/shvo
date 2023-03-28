from draw_engine import DrawEngine
from shvo import DrawEngineDirector, PluginBase, ToDockBase
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QPushButton, QWidget, QVBoxLayout
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtCore import QObject
import matplotlib.pyplot as plt
import PyQt5
import matplotlib
matplotlib.use('Qt5Agg')

class MplCanvas(FigureCanvas):
    def __init__(self, width=5, height=4, dpi=100):
        self.fig, self.axes = \
            plt.subplots(32, 2, figsize=(width, height), layout="constrained")
        super(MplCanvas, self).__init__(self.fig)

class ToDock(ToDockBase):
    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout()
        self.mpl = MplCanvas(30, 60)

        self.mpl.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                               QtWidgets.QSizePolicy.Fixed)

        scroll = QtWidgets.QScrollArea()
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.mpl)

        lay.addWidget(scroll)
        btn = QPushButton("Load...")
        btn.setFlat(True)
        btn.clicked.connect(self.openProfs)
        lay.addWidget(btn)
        self.setLayout(lay)

    def postAdd(self):
        color = self.mpl.palette().color(PyQt5.QtGui.QPalette.Background).\
            getRgbF()
        self.mpl.fig.set_facecolor(color)
        for a in self.mpl.axes.flatten():
            a.set_facecolor(color)

    def openProfs(self):
        fname = QtWidgets.QFileDialog.getOpenFileName(caption="Open profile",
                                                      filter="*.npz")[0]
        if fname:
            prof_data = np.load(fname)
            mk_inds = prof_data["moving_kink_inds"]
            for prof, mk, brd, ax, prof_n in \
                zip(prof_data["profiles"], prof_data["moving_kink"],
                    prof_data["borders"], self.mpl.axes.flatten(),
                    range(len(prof_data["profiles"]))):
                ax.clear()
                ax.plot(prof, c="black")
                ax.plot(mk_inds, mk, c="green", ls="--", lw=1)
                ax.axvline(brd, c="red")
                ax.text(0, 1, 'profile:' + str(prof_n), transform=ax.transAxes)
                ax.annotate(str(brd), xy=(brd, 0.7), xycoords='data',
                            xytext=(30, 15), textcoords='offset points',
                            arrowprops=dict(arrowstyle="->"))

            self.mpl.fig.canvas.draw()
            self.mpl.fig.canvas.flush_events()

class Plugin(DrawEngineDirector, PluginBase):
    def __init__(self):
        self.to_dock = ToDock()
        self.title = "PolyRads profiles"
