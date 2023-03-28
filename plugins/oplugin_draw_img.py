import numpy as np
import cv2

from .shvo_object import ShvoObject

class DrawImg(ShvoObject):
    def __init__(self, parent):
        super().__init__(parent)

    def push(self, arg):
        pass

    def change(self, arg):
        pass

    def setArgs(self, **kargs):
        self.img = kargs["img"]

    def calcRasterChanges(self, zoom):
        pass

    def changeEngine(self):
        # It is assumed that there will be 1 or 3 channels
        # It is assumed that there will be 8 or 16 bits depth
        self.parent.img_origin = self.img
        self.parent.shape2d = np.array(self.img.shape)[:2]
        self.parent.cshape2d = self.parent.shape2d

        img_tmp = self.parent.img_origin.reshape(
            np.r_[self.parent.shape2d, -1])[..., :3].flatten()
        show_img_min, show_img_max = 0, 255
        img_min, img_max = np.iinfo(img_tmp.dtype).min, \
                           np.iinfo(img_tmp.dtype).max
        img_tmp = np.interp(img_tmp, np.arange(img_min, img_max + 1),
                            np.linspace(show_img_min, show_img_max,
                                        img_max - img_min + 1))
        img_tmp = img_tmp.astype(np.uint8)
        self.parent.img_3c = \
            np.broadcast_to(img_tmp.reshape(np.r_[self.parent.shape2d, -1]),
                            np.r_[self.parent.shape2d, 3])
        self.parent.canvas = self.parent.img_3c.copy()


plugin_info = {"draw_img": DrawImg}
