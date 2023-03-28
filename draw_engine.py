import numpy as np
import cv2

import importlib

shvo_types = {}

plugins_pkg = importlib.import_module("plugins")
object_plugin_names = \
  ["plugins." + name for name in plugins_pkg.object_plugins]
for name in plugins_pkg.object_plugins:
  plugin = importlib.import_module("plugins." + name)
  shvo_types.update(plugin.plugin_info)

class DrawEngine:
  img_origin = property(lambda self: self._io if hasattr(self, '_io') else None, 
                        lambda self, val: self.setImg(val))
  def __init__(self, arg):
    self.eid = arg
    self.zoom = 1.
    self.shvo_objects = {}#id: object
    self.free_id = 0

  def draw(self, img):
    pass
  def onImgOriginChanged(self):
    pass

  def getId(self):
    return self.free_id

  def idPP(self):
    self.free_id += 1

  def getZoom(self):
    return self.zoom

  def setImg(self, img):
    self._io = img

  def zoomAll(self, zoom):
    self.zoom = zoom
    self.new_shape2d = (self.shape2d * self.zoom).astype(np.int)
    for k in self.shvo_objects: 
      self.shvo_objects[k].calcRasterChanges(self.zoom) #calc model
    self.renderAllW()
    self.draw(self.img_w_all)

  def objectsFactory(self, obj_type):
    return shvo_types[obj_type](self)

  def addIfNotExist(self, obj_type, obj_id):
    shvo_object = \
      self.shvo_objects.setdefault(obj_id, self.objectsFactory(obj_type))

    if not isinstance(shvo_object, shvo_types[obj_type]):
      shvo_object = self.objectsFactory(obj_type)
      self.shvo_objects[obj_id] = shvo_object

  def push(self, obj_type, obj_id, val):
    self.addIfNotExist(obj_type, obj_id)
    return self.shvo_objects[obj_id].push(val)

  def change(self, obj_type, obj_id, val):
    self.addIfNotExist(obj_type, obj_id)
    return self.shvo_objects[obj_id].change(val)

  def drawObject(self, obj_type, obj_id, **kargs):
    self.addIfNotExist(obj_type, obj_id)
    self.shvo_objects[obj_id].setArgs(**kargs) #calc model
    self.shvo_objects[obj_id].changeEngine()
    self.shvo_objects[obj_id].calcRasterChanges(self.zoom) #calc model
    self.renderAllW()
    self.draw(self.img_w_all)

  def renderAllW(self):
    if hasattr(self, "canvas"):
      self.img_w_all = self.canvas.copy()
      for shvo_object in self.shvo_objects.values():
        for start, lay_w, color in zip(shvo_object.layers_starts, 
                                       shvo_object.sub_layers_w,
                                       shvo_object.layers_colors):
          where_draw = tuple(np.stack([lay_w[0], lay_w[1]]) + \
                             np.expand_dims(start, -1))
          self.img_w_all[where_draw] = color
