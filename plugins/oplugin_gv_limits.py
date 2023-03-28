import numpy as np
import cv2

from .shvo_object import ShvoObject


class GVLimits(ShvoObject):
    def __init__(self, parent):
        super().__init__(parent)

    def push(self, arg):
        pass

    def change(self, arg):
        pass

    def setArgs(self, **kargs):
        self.min = kargs["min"]
        self.max = kargs["max"]

    def calcRasterChanges(self, zoom):
        pass

    def changeEngine(self):
        img_tmp = self.parent.img_origin.reshape(
            np.r_[self.parent.shape2d, -1])[..., :3].flatten()
        img_tmp = np.where(img_tmp > self.max, self.max, img_tmp)
        img_tmp = np.where(img_tmp < self.min, self.min, img_tmp)
        show_img_min, show_img_max = 0, 255
        img_tmp = np.interp(img_tmp, np.arange(self.min, self.max + 1),
                            np.linspace(show_img_min, show_img_max,
                                        self.max - self.min + 1))
        img_tmp = img_tmp.astype(np.uint8)
        self.parent.img_3c = \
            np.broadcast_to(img_tmp.reshape(np.r_[self.parent.shape2d, -1]),
                            np.r_[self.parent.shape2d, 3])
        self.parent.canvas = cv2.resize(self.parent.img_3c,
                                        tuple(self.parent.cshape2d[-1::-1]))

plugin_info = {"gv_limits": GVLimits}
