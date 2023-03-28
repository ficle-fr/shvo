import sys
import importlib
from PyQt5.QtCore import Qt, QSize, QRect, QEvent, QAbstractListModel, \
    pyqtSignal, QObject, QModelIndex, QDir, QPoint
from PyQt5.QtGui import QPainter, QColor, QFont, QPixmap, QBrush, QImage, \
    QPalette, QWheelEvent, QIcon
from PyQt5.QtWidgets import QPushButton, QWidget, QApplication, QMainWindow, \
    QScrollArea, QSizePolicy, QVBoxLayout, QHBoxLayout, QLabel, QFileDialog,\
    QToolBar, QAction, QActionGroup, QMdiArea, QMdiSubWindow, QTextEdit,\
    QListView, QStyleFactory, QDockWidget, QFrame, QSizeGrip

from qt_material import apply_stylesheet, export_theme

import numpy as np

import cv2

#import resources

from draw_engine import DrawEngine


class DrawWidget(QWidget):
    merged_img = np.empty((0, 0), dtype=np.uint8)
    zoom = 1

    def __init__(self, *args, **kwargs):
        QWidget.__init__(self, *args, **kwargs)

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)
        qp.drawPixmap(0, 0, self.np2qpixmap(self.merged_img))
        qp.end()

    def drawImg(self, img):
        self.merged_img = img
        self.resize(self.merged_img.shape[1], self.merged_img.shape[0])
        self.update()

    def plugEngine(self, engine):
        self.engine = engine
        self.engine.draw = self.drawImg

    def np2qpixmap(self, img_np):
        height, width = img_np.shape[:2]
        bytesPerLine = 3 * img_np.shape[1]
        image = QImage(img_np.data.tobytes(), width, height, bytesPerLine,
                       QImage.Format_BGR888)
        return QPixmap.fromImage(image.copy())


class ShvoScroll(QScrollArea):
    def wheelEvent(self, event):
        pass


class TitleBar(QFrame):
    def __init__(self, *args, **kwargs):
        super(TitleBar, self).__init__(*args, **kwargs)
        self.is_maximum = True
        self.setupUi()
        self.setupStyleSheet()

    def setupStyleSheet(self):
        self.r_frame.setProperty('class', 'without_border')
        # self.btn_mnmz.setProperty('class', 'minimize')
        self.btn_mxmz.setProperty('class', 'maximize')
        self.btn_mxmz.setProperty('state', self.is_maximum)
        self.btn_cls.setProperty('class', 'close')

    def setupUi(self):
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.setProperty('class', 'without_border')

        self.main_hl = QHBoxLayout(self)
        self.main_hl.setContentsMargins(0, 0, 0, 0)
        self.main_hl.setSpacing(0)
        self.l_frame = QFrame(self)
        self.l_frame.setProperty('class', 'without_border')

        self.l_hl = QHBoxLayout(self.l_frame)
        self.l_hl.setContentsMargins(0, 0, 0, 0)
        self.l_hl.setSpacing(0)
        self.label = QLabel(self.l_frame)
        self.l_hl.addWidget(
            self.label, 0, Qt.AlignHCenter | Qt.AlignTop)
        self.main_hl.addWidget(
            self.l_frame, 0, Qt.AlignLeft | Qt.AlignTop)

        self.r_frame = QFrame(self)
        self.r_hl = QHBoxLayout(self.r_frame)
        self.r_hl.setContentsMargins(0, 0, 0, 0)
        self.r_hl.setSpacing(0)
        self.btn_mxmz = QPushButton(self.r_frame)
        self.btn_mxmz.setFlat(True)
        self.r_hl.addWidget(self.btn_mxmz)
        self.btn_cls = QPushButton(self.r_frame)
        self.btn_cls.setFlat(True)
        self.r_hl.addWidget(self.btn_cls)

        self.main_hl.addWidget(
            self.r_frame, 0, Qt.AlignRight | Qt.AlignTop)

        self.btn_mxmz.clicked.connect(self.toggleMaxNorm)

    def toggleMaxNorm(self):
        self.is_maximum = not self.is_maximum
        self.btn_mxmz.setProperty('state', self.is_maximum)
        self.btn_mxmz.style().unpolish(self.btn_mxmz)
        self.btn_mxmz.style().polish(self.btn_mxmz)


class ImgWindow(QMdiSubWindow):
    def __init__(self, *args):
        super().__init__(*args)
        self.can_move = False
        self.setWindowFlags(Qt.FramelessWindowHint)
        # self.setWindowFlags(Qt.SubWindow);
        self.setWindowIcon(QIcon(":ico_load_img.svg"))

        main_w = QWidget(self)
        main_hl = QVBoxLayout(main_w)
        main_hl.setContentsMargins(0, 0, 0, 0)
        main_hl.setSpacing(0)

        scroll = ShvoScroll(main_w)
        scroll.setBackgroundRole(QPalette.Dark)
        self.draw_widget = DrawWidget()
        self.draw_widget.setMouseTracking(True)
        # self.draw_widget.installEventFilter(self)
        scroll.setWidget(self.draw_widget)

        self.tb = TitleBar()
        self.tb.installEventFilter(self)
        main_hl.addWidget(self.tb)
        main_hl.addWidget(scroll)
        self.setWidget(main_w)

        self.tb.btn_cls.clicked.connect(self.close)
        self.tb.btn_mxmz.clicked.connect(self.toggleWinSize)

        hl_sg = QHBoxLayout()
        sg = QSizeGrip(main_w)
        hl_sg.addWidget(sg, 0, Qt.AlignRight)

        main_hl.addLayout(hl_sg)

    def toggleWinSize(self):
        if self.tb.is_maximum:
            self.showMaximized()
        else:
            self.showNormal()

    def eventFilter(self, obj, event):
        if hasattr(self, "tb") and obj is self.tb:
            if event.type() == QEvent.MouseButtonPress and\
               event.button() == Qt.LeftButton:
                self.can_move = True
                self.move_anchor = event.globalPos()
            elif event.type() == QEvent.MouseButtonRelease:
                self.can_move = False
            elif event.type() == QEvent.MouseMove and self.can_move:
                pos = event.globalPos()
                diff_pos = pos - self.move_anchor
                self.move(self.pos() + diff_pos)
                self.move_anchor = pos
        return super(ImgWindow, self).eventFilter(obj, event)


class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):

        self.is_zoom = False
        self.curr_id = 0
        self.curr_cmd = ""
        self.in_cmd = False

        super(MainWindow, self).__init__(*args, **kwargs)
        self.setWindowIcon(QIcon("icon:/actions/ico_load_img.svg"))

        act_zoom = QAction(QIcon("icon:/actions/ico_zoom.svg"), "Zoom", self)
        act_load = QAction(
            QIcon("icon:/actions/ico_load_img.svg"), "Load image", self)
        act_line = QAction(
            QIcon("icon:/actions/ico_draw_line.svg"), "Line", self)
        act_rect = QAction(
            QIcon("icon:/actions/ico_draw_rect.svg"), "Recp", self)
        act_shvol = QAction(
            QIcon("icon:/actions/ico_shvol.svg"), "Load shvo", self)

        act_zoom.setCheckable(True)

        act_line.setCheckable(True)
        act_rect.setCheckable(True)
        drawing_group = QActionGroup(self)
        drawing_group.addAction(act_line)
        drawing_group.addAction(act_rect)
        drawing_group.setExclusionPolicy(
            QActionGroup.ExclusionPolicy.ExclusiveOptional)

        act_load.triggered.connect(self.openImg)
        # act_view.triggered.connect(self.addView)
        act_zoom.toggled.connect(self.activateZomm)
        act_line.toggled.connect(self.activateLine)
        act_rect.toggled.connect(self.activateRect)
        act_shvol.triggered.connect(self.loadShvo)

        commands_bar = QToolBar("Commands", self)
        self.addToolBar(commands_bar)
        commands_bar.addAction(act_load)
        commands_bar.addAction(act_zoom)
        commands_bar.addAction(act_line)
        commands_bar.addAction(act_rect)
        commands_bar.addAction(act_shvol)

        self.mdi = QMdiArea()
        # self.mdi.setSt

        def changeDrawEngineByWin(win):
            # print("Change draw engine!!!")
            if hasattr(win, 'draw_widget') and \
               hasattr(win.draw_widget, 'engine'):
                self.command_line.exec("app.activateEngine({eid})".
                                       format(eid=win.draw_widget.engine.eid))
        self.mdi.subWindowActivated.connect(changeDrawEngineByWin)
        self.setCentralWidget(self.mdi)

    def setCommandLine(self, arg):
        self.command_line = arg

    def addView(self):
        sub = ImgWindow()
        sub.setAttribute(Qt.WA_DeleteOnClose)
        sub.draw_widget.installEventFilter(self)
        self.mdi.addSubWindow(sub)
        sub.showMaximized()
        return sub

    def onDrawEngineChanged(self, engine):
        win = next((sub for sub in self.mdi.subWindowList()
                    if hasattr(sub.draw_widget, 'engine') and
                    sub.draw_widget.engine is engine), None)
        if win == None:
            win = self.addView()
            win.draw_widget.plugEngine(engine)

        self.mdi.setActiveSubWindow(win)

    def openImg(self):
        fname = QFileDialog.getOpenFileName(caption="Open image",
                                            filter="*.tif")[0]
        if fname:
            self.command_line.exec(
                "img = app.openImg(\"{f}\")\n".format(f=fname) +
                "eid = app.nextUniqueId()\n" +
                "app.activateEngine(eid)\n" +
                "app.draw(\"draw_img\", \"img\", img = img)#app.setImg(img)")

    def loadShvo(self):
        fname = QFileDialog.getOpenFileName(caption="Load shvo",
                                            filter="*.npz")[0]
        prof_data = np.load(fname)
        if "start_point" in prof_data and "border_points" in prof_data:
            cmd = ("obj_id = app.getId()\n" +
                   "app.draw(\"poly_rads\", obj_id, start_point = {sp}," +
                   "border_points = {bp})\n").\
                format(sp=np.array2string(prof_data["start_point"],
                                          separator=","),
                       bp=np.array2string(prof_data["border_points"],
                                          separator=","))
            self.command_line.exec(cmd)

    def activateZomm(self, is_zoom):
        self.is_zoom = is_zoom

    def activateLine(self, is_line):
        self.curr_cmd = "line" if is_line else ""

    def activateRect(self, is_rect):
        self.curr_cmd = "rect" if is_rect else ""

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Wheel and self.is_zoom:
            zoom_coeff = 1.2 if event.angleDelta().y() > 0 else 1. / 1.2
            cmd = "app.draw(\"zoomer\", \"zoomer\", zoom = app.getZoom() * {coeff})".\
                format(coeff=zoom_coeff)

            self.command_line.exec(cmd)
        if event.type() == QEvent.MouseButtonPress:  # and self.is_zoom:
            if self.curr_cmd == "line" or self.curr_cmd == "rect":
                click_pos = (np.array([event.pos().x(), event.pos().y()]) /
                             obj.zoom)
                cmd = "obj_id = app.getId()\n" +\
                      "zoom = app.getZoom()\n" +\
                      "coords = [{p1} / zoom, {p2} / zoom]\n".\
                    format(p1=click_pos[0], p2=click_pos[1]) +\
                      "args, in_cmd = app.push(\"line\", obj_id, coords)\n" +\
                      "aux[\"in_cmd\"] = in_cmd\n" +\
                      "app.draw(\"line\", obj_id, points = args)\n" +\
                      "if not in_cmd:\n" +\
                      "  app.incrementId()"
                self.command_line.exec(cmd)
                return True
        if event.type() == QEvent.MouseMove:  # and self.is_zoom:
            if (self.curr_cmd == "line" or self.curr_cmd == "rect"):
                click_pos = (np.array([event.pos().x(), event.pos().y()]) /
                             obj.zoom)
                cmd = "if \"in_cmd\" in aux and aux[\"in_cmd\"]:\n" +\
                      "  obj_id = app.getId()\n" +\
                      "  zoom = app.getZoom()\n" +\
                      "  coords = [{p1} / zoom, {p2} / zoom]\n".\
                    format(p1=click_pos[0], p2=click_pos[1]) +\
                      "  args = app.change(\"line\", obj_id, coords)\n" +\
                      "  app.draw(\"line\", obj_id, points = args)\n"
                self.command_line.exec(cmd)
                return True
        return super(MainWindow, self).eventFilter(obj, event)


def apply_theme(app, name):
    th_path = "themes/" + name
    print("Path:", th_path)
    QDir.addSearchPath('icon', th_path)
    with open(th_path + '.qss', 'r') as file:
        print(file)
        app.setStyleSheet(file.read())


def main3():
    app = QApplication(sys.argv)

    # apply_theme(app, 'dark')
    apply_theme(app, 'canonical')

    # QDir.addSearchPath('icon', 'theme')
    # QDir.addSearchPath('iconssssssss', 'themessss')
    # QDir.addSearchPath('icon', 'themes/dark')
    # with open('themes/dark.qss', 'r') as file:
    #    app.setStyleSheet(file.read())
    # with open('shvo_theme.qss', 'r') as file:
    #    app.setStyleSheet(file.read())
    win = MainWindow()
    win.setWindowTitle("Shvo")
    win.showMaximized()
    cl = CommandLine()
    data = AppDataQtWrapp()  # Send signals to win and gui plugins
    cl.setApp(data)  # Command line controls data
    win.setCommandLine(cl)  # Win can send commands to command line

    data.engine_activated.connect(win.onDrawEngineChanged)

    plugins_pkg = importlib.import_module("plugins")
    gui_plugin_names = ["plugins." + name for name in plugins_pkg.gui_plugins]
    for name in gui_plugin_names:
        plugin = importlib.import_module(name)
        plugin_var = plugin.Plugin()
        plugin_var.setCommandLine(cl)
        dock = QDockWidget()
        win.addDockWidget(Qt.RightDockWidgetArea, dock)
        dock.setWidget(plugin_var.to_dock)
        plugin_var.to_dock.postAdd()
        if hasattr(plugin_var, "title"):
            dock.setWindowTitle(plugin_var.title)
        data.engine_activated.connect(plugin_var.onEngineActivated)

    sys.exit(app.exec_())


class AppData:
    def __init__(self, DEClass=DrawEngine):
        super(AppData, self).__init__()
        self.engines = {}
        self.last_id = -1  # about engine
        self.current_id = -1  # about engine ; future del self.current_engine
        self.DEClass = DEClass

    def openImg(self, fname):
        img = cv2.imread(fname, cv2.IMREAD_UNCHANGED)
        return cv2.imread(fname, cv2.IMREAD_UNCHANGED)

    def nextUniqueId(self):
        self.last_id += 1
        while self.last_id in self.engines.keys():
            self.last_id += 1
        return self.last_id

    def setImg(self, img):
        self.current_engine.setImg(img)

    def activateEngine(self, engine_id):
        self.current_id = engine_id
        self.current_engine = \
            self.engines.setdefault(engine_id, self.DEClass(engine_id))

    def push(self, cmd, obj_id, point):
        return self.current_engine.push(cmd, obj_id, point)

    def change(self, cmd, obj_id, point):
        return self.current_engine.change(cmd, obj_id, point)

    def draw(self, cmd, obj_id, **kargs):
        # self.current_engine.drawObject(cmd, obj_id, points = args)
        self.current_engine.drawObject(cmd, obj_id, **kargs)

    def incrementId(self):
        self.current_engine.idPP()

    def getId(self):
        return self.current_engine.getId()

    def getZoom(self):
        return self.current_engine.getZoom()


class DrawEngineDirector:
    def onImageChange(self):
        pass

    def onEngineActivated(self, e):
        pass


class PluginBase:
    def setCommandLine(self, arg):
        self.command_line = arg


class DrawEngineInPlugin(DrawEngine):
    def __init__(self, arg):
        super(DrawEngineInPlugin, self).__init__(arg)
        self.directors = []

    def setImg(self, img):
        super(DrawEngineInPlugin, self).setImg(img)
        for director in self.directors:
            director.onImageChange()

    def addDirector(self, arg):
        if arg not in self.directors:
            self.directors.append(arg)


class AppDataQtWrapp(AppData, QObject):
    engine_activated = pyqtSignal(DrawEngineInPlugin)

    def __init__(self):
        super(AppDataQtWrapp, self).__init__(DrawEngineInPlugin)

    def activateEngine(self, engine_id):
        super(AppDataQtWrapp, self).activateEngine(engine_id)
        self.engine_activated.emit(self.current_engine)


class CommandLine:
    def setApp(self, app):
        self.to_exec = {"app": app, "aux": {}}

    def exec(self, code):
        exec(code, {}, self.to_exec)


class ToDockBase(QWidget):
    def __init__(self, parent=None):
        super(ToDockBase, self).__init__(parent)

    def postAdd(self):
        pass


if __name__ == '__main__':
    main3()
