import numpy as np
import cv2

from .shvo_object import ShvoObject

class LineObject(ShvoObject):
  def __init__(self, parent):
    super().__init__(parent)

    self.type_name = "LINE"
    self.points = np.empty((0, 2), dtype = np.int) #x, y
    self.r = 5
    self.margin = np.stack([5, 5])
    self.not_completed = True#in future move to parrent class
    self.change_ind = 0

  def push(self, arg):
    if self.not_completed:
      if len(self.points) == 0:
        self.points = np.full((2, 2), arg)
        self.change_ind = 1
      else:
        self.points[self.change_ind] = arg
        self.not_completed = False#in future move to parrent class
    return self.points, self.not_completed

  def change(self, arg):
    self.points[self.change_ind] = arg
    return self.points

  def setArgs(self, **kargs):
    self.points = kargs["points"]

  def calcRasterChanges(self, zoom):
    self.sub_layers_w.clear()
    self.layers_starts.clear()
    self.layers_colors.clear()

    points = (self.points * zoom).astype(np.int)
    points_yx = points[:, -1::-1]
    
    mins = np.min(points_yx, axis = 0) - self.margin
    maxs = np.max(points_yx, axis = 0) + self.margin
    shape = maxs - mins
    layer = np.full(shape, 0, dtype = np.uint8)
    cv2.line(layer, tuple(points[0] - mins[-1::-1]), 
             tuple(points[1] - mins[-1::-1]), 255)
    where_coords = np.where(layer > 0)
    coords = \
      np.stack([where_coords[0], where_coords[1]])#.astype(np.int)
    self.layers_starts.append(mins)
    self.sub_layers_w.append(coords)
    self.layers_colors.append(np.array([255, 0, 0]))
    
    cir_mins = points_yx - np.stack([self.r, self.r])

    cirf_lay = np.full(np.stack([self.r, self.r]) * 2, 0, dtype = np.uint8)
    cv2.circle(cirf_lay, (self.r, self.r), self.r, 255, thickness = -1)
    where_cirf_coords = np.where(cirf_lay > 0)
    cirf_coords = \
      np.stack([where_cirf_coords[0], where_cirf_coords[1]])#.astype(np.int)

    self.layers_starts.append(cir_mins[0])
    self.layers_starts.append(cir_mins[1])
    self.sub_layers_w.append(cirf_coords)
    self.sub_layers_w.append(cirf_coords)
    self.layers_colors.append(np.array([255, 255, 255]))
    self.layers_colors.append(np.array([255, 255, 255]))

    cir_lay = np.full(np.stack([self.r, self.r]) * 2, 0, dtype = np.uint8)
    cv2.circle(cir_lay, (self.r, self.r), self.r, 255)
    where_cir_coords = np.where(cir_lay > 0)
    cir_coords = \
      np.stack([where_cir_coords[0], where_cir_coords[1]])#.astype(np.int)

    self.layers_starts.append(cir_mins[0])
    self.layers_starts.append(cir_mins[1])
    self.sub_layers_w.append(cir_coords)
    self.sub_layers_w.append(cir_coords)
    self.layers_colors.append(np.array([0, 0, 255]))
    self.layers_colors.append(np.array([0, 0, 255]))

  def changeEngine(self):
    pass

plugin_info = {"line": LineObject}
