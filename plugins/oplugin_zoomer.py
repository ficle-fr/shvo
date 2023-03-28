import numpy as np
import cv2

from .shvo_object import ShvoObject

class Zoomer(ShvoObject):
  def __init__(self, parent):
    super().__init__(parent)

  def push(self, arg):
    pass

  def change(self, arg):
    pass

  def setArgs(self, **kargs):
    self.done = False
    self.zoom = kargs["zoom"]

  def calcRasterChanges(self, zoom):
    pass

  def changeEngine(self):
    self.parent.zoom = self.zoom
    self.parent.cshape2d = (self.parent.shape2d * self.zoom).astype(np.int)

    self.parent.canvas = cv2.resize(self.parent.img_3c, 
                                    tuple(self.parent.cshape2d[-1::-1]))
    for shvo_object in self.parent.shvo_objects.values(): 
      shvo_object.calcRasterChanges(self.zoom) #calc model

plugin_info = {"zoomer": Zoomer}
