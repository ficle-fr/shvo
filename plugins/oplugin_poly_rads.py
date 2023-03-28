import numpy as np
import cv2

from .shvo_object import ShvoObject
    
class PolyRadsObject(ShvoObject):
  def __init__(self, parent):
    super().__init__(parent)

    self.points = np.empty((0, 2), dtype = np.int) #x, y
    self.r = 5
    self.margin = np.stack([5, 5])

  def push(self, arg):
    if len(self.points) == 0:
      self.points = np.full((2, 2), arg)
    else:
      self.points[1] = arg
    return self.points

  def setArgs(self, **kargs):
    self.start_point = np.asarray(kargs["start_point"])
    
    self.border_points = np.asarray(kargs["border_points"])

  def calcRasterChanges(self, zoom):
    self.sub_layers_w.clear()
    self.layers_starts.clear()
    self.layers_colors.clear()

    start_point = (self.start_point * zoom).astype(np.int)
    border_points = (self.border_points * zoom).astype(np.int)
    
    rads = np.stack([np.full_like(border_points, start_point), border_points],
                    axis = -2)
    rmins = np.min(rads, axis = -2) - self.margin
    rmaxs = np.max(rads, axis = -2) + self.margin
    local_rads = rads - np.expand_dims(rmins, -2)
    for rmin, rmax, r, rnumb in zip(rmins, rmaxs, local_rads, 
                                    np.arange(len(local_rads))):

      lay = np.full((rmax - rmin)[-1::-1], 0, dtype = np.uint8)
      cv2.line(lay, tuple(r[0]), tuple(r[1]), 255)
      where_coords = np.where(lay > 0)
      coords = \
        np.stack([where_coords[0], where_coords[1]])#.astype(np.int)

      tsize, _ = \
        cv2.getTextSize(str(rnumb), cv2.FONT_HERSHEY_PLAIN, 0.8, 1)
      tlay = \
        np.full((tsize[1], tsize[0]) + 2 * self.margin, 0, dtype = np.uint8)
      cv2.putText(tlay, str(rnumb), 
                  (self.margin[0], tlay.shape[0] - self.margin[1]),
                  cv2.FONT_HERSHEY_PLAIN, 0.8, 255, 1)

      dydx = (r[1] - r[0])[-1::-1]
      angle = np.arctan2(dydx[0], dydx[1])
      angle += np.pi / 4
      angle = np.where(angle < 0, 2 * np.pi + angle, angle)
      if 0 <= angle < np.pi / 2:
        tmin = r[1][-1::-1] + np.array([-tlay.shape[0] / 2, 0])
      elif np.pi / 2 <= angle < np.pi:
        tmin = r[1][-1::-1] + np.array([0, -tlay.shape[1] / 2])
      elif np.pi <= angle < 3 * np.pi / 2:
        tmin = r[1][-1::-1] + np.array([-tlay.shape[0] / 2, -tlay.shape[1]])
      else: #3 * np.pi / 4 <= angle < 2 * np.pi:
        tmin = r[1][-1::-1] + np.array([-tlay.shape[0], -tlay.shape[1] / 2])
      
      tmin = rmin[-1::-1] + tmin.astype(np.int)

      where_tcoords= np.where(tlay > 0)
      tcoords = \
        np.stack([where_tcoords[0], where_tcoords[1]])#.astype(np.int)

      self.layers_starts.append(rmin[-1::-1])
      self.sub_layers_w.append(coords)
      self.layers_colors.append(np.array([255, 0, 0]))

      self.layers_starts.append(tmin)
      self.sub_layers_w.append(tcoords)
      self.layers_colors.append(np.array([0, 100, 0]))

  def changeEngine(self):
    pass

plugin_info = {"poly_rads": PolyRadsObject}
