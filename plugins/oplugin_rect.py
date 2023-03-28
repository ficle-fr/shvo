import numpy as np
import cv2

from .shvo_object import ShvoObject
    
class RectObject(ShvoObject):
  def __init__(self, parent):
    super().__init__(parent)

    self.type_name = "RECT"
    self.points = np.empty((0, 2), dtype = np.int) #x, y
    self.r = 5
    self.margin = np.stack([5, 5])
    self.completed = False#in future move to parrent class

  def push(self, arg):
    if len(self.points) == 0:
      self.points = np.full((2, 2), arg)
    else:
      self.points[1] = arg
      self.completed = True
    return self.points, self.completed

  def setArgs(self, **kargs):
    self.points = kargs["points"]

  def calcRasterChanges(self, zoom):
    self.sub_layers_w.clear()
    self.layers_starts.clear()
    self.layers_colors.clear()

    points = (self.points * zoom).astype(np.int)
    mins = np.min(points, axis = 0)
    maxs = np.max(points, axis = 0)

    corners = np.stack([mins, maxs])
    hor_edges = np.stack(np.meshgrid(corners[:, 0], corners[:, 1]), axis = -1)
    ver_edges = np.stack(np.meshgrid(corners[:, 1], 
                                     corners[:, 0])[::-1], axis = -1)

    hor_mins = hor_edges[:, 0] - self.margin
    ver_mins = ver_edges[:, 0] - self.margin

    hor_len = hor_edges[0, 1, 0] - hor_edges[0, 0, 0]
    ver_len = ver_edges[0, 1, 1] - ver_edges[0, 0, 1]
    hor_lay = np.full([0, hor_len] + 2 * self.margin, 0, dtype = np.uint8)
    ver_lay = np.full([ver_len, 0] + 2 * self.margin, 0, dtype = np.uint8)

    cv2.line(hor_lay, tuple(self.margin), 
             tuple([hor_len, 0] + self.margin), 255)
    where_hor = np.where(hor_lay > 0)
    coords_hor = \
      np.stack([where_hor[0], where_hor[1]])#.astype(np.int)

    cv2.line(ver_lay, tuple(self.margin), 
             tuple([0, ver_len] + self.margin), 255)
    where_ver = np.where(ver_lay > 0)
    coords_ver = \
      np.stack([where_ver[0], where_ver[1]])#.astype(np.int)
    self.layers_starts.append(hor_mins[0][-1::-1])
    self.layers_starts.append(hor_mins[1][-1::-1])
    self.sub_layers_w.append(coords_hor)
    self.sub_layers_w.append(coords_hor)
    self.layers_colors.append(np.array([255, 0, 0]))
    self.layers_colors.append(np.array([255, 0, 0]))

    self.layers_starts.append(ver_mins[0][-1::-1])
    self.layers_starts.append(ver_mins[1][-1::-1])
    self.sub_layers_w.append(coords_ver)
    self.sub_layers_w.append(coords_ver)
    self.layers_colors.append(np.array([255, 0, 0]))
    self.layers_colors.append(np.array([255, 0, 0]))

  def changeEngine(self):
    pass

plugin_info = {"rect": RectObject}
