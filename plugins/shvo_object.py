class ShvoObject:
  def __init__(self, parent):
    type_name = "UNKNOWN"
    self.parent = parent
    self.sub_layers_w = []
    self.layers_starts = []
    self.layers_colors = []
  def push(self, arg, ):
    raise NotImplementedError()
  def calcRasterChanges(self, args, zoom):
    raise NotImplementedError()
  def setArgs(self, **kargs):
    raise NotImplementedError()
  def changeEngine(self):
    raise NotImplementedError()
