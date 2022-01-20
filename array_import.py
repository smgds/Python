import os
print("Current Working Directory " , os.getcwd())
os.chdir('C:\Users\amyn\Desktop')

from PIL import Image
from Images import imageToPixmapRGB
from numpy import array, dstack, transpose, uint8, zeros

# load file, identifying name, number of rows/columns
def loadArrayImage(fileName, sampleName, nRows, nCols=None):

  # sets default data columns to number of rows
  if not nCols:
    nCols = nRows
  
  # matrix with 3 colors, rows, columns. 
  dataMatrix = zeros((3, nRows, nCols), float)
  
  # image object
  img = Image.open(fileName)
  # numeric array
  pixmap = imageToPixmapRGB(img)
  
  # divide total image by #col and #rows
  height, width, depth = pixmap.shape
  
  # floating point grid sizes-precise values
  dx = width/float(nCols)
  dy = height/float(nRows)
  # integer grid sizes-fixed number of pixels
  xSize = 1 + (width-1)//nCols
  ySize = 1 + (height-1)//nRows

  # loop by row, calculate first and last pixel position
  for row in range(nRows):
    yStart = int(row*dy)
    yEnd   = yStart + ySize

    # loop by row, calculate range of pixels
    for col in range(nCols):
      xStart = int(col*dx)
      xEnd   = xStart + xSize

      # use row/colunm pixel location-data summed from width and height
      elementData = pixmap[yStart:yEnd,xStart:xEnd]
      dataMatrix[:,row, col] = elementData.sum(axis=(0,1))

  # microarray object which is passed back from function
  return Microarray(sampleName, dataMatrix)
 
# object holding data in microarray   
class Microarray(object):

  # sample name and NumPy array
  def __init__(self, name, data, rowData=None, colData=None):

   # make copy of array
    self.name = name 
    data = array(data)
    
    # size of array axes
    shape = data.shape
    
    # 3 axes=data channels, row, column
    if len(shape) == 3:
      self.nChannels, self.nRows, self.nCols = shape
    
    # 2 axes=1 channel, row, column -> forces to have 3 channels
    elif len(shape) == 2:
      self.nRows, self.nCols = shape
      self.nChannels = 1
      data = array([data])

    # exception for incorrect # of channels
    else:
      raise Exception('Array data must have either 2 or 3 axes.')  

    # new data tied to microarray object, copy of original
    self.data = data
    self.origData = array(data)
  
    # row/column labels added to object  
    self.rowData = rowData or range(self.nRows)
    self.colData = colData or range(self.nCols)

  def resetData(self):
  
    self.data = array(self.origData)
    self.nChannels = len(self.data)

  def writeData(self, fileName, separator=' '):
  
    fileObj = open(fileName, 'w')
    
    for i in range(self.nRows):
      rowName = str(self.rowData[i])
      
      for j in range(self.nCols):
        colName = str(self.colData[j])

        values = self.data[:,i,j]

        lineData = [rowName, colName]
        lineData += ['%.3f' % (v,) for v in values]
        
        line = separator.join(lineData)
        fileObj.write(line + '\n')

  def makeImage(self, squareSize=20, channels=None):
    
    minVal = self.data.min()
    maxVal = self.data.max() 
    dataRange = maxVal - minVal  

    adjData = (self.data - minVal) * 255 / dataRange
    adjData = array(adjData, uint8)
   
    if not channels:
      if self.nChannels == 1:
        channels = (0,0,0) # Greyscale
      else:
        channels = list(range(self.nChannels))[:3]

    pixmap = []
    for i in channels:
      if i is None:
        pixmap.append(zeros((self.nRows, self.nCols), uint8))
      else:
        pixmap.append(adjData[i])
        
    while len(pixmap) < 3:
      pixmap.append(zeros((self.nRows, self.nCols), uint8))
     
    pixmap = dstack(pixmap)
    img = Image.fromarray(pixmap, 'RGB')

    width = self.nCols * squareSize
    height = self.nRows * squareSize
    img = img.resize((width, height))
    
    return img

  def clipBaseline(self, threshold=None, channels=None, defaultProp=0.2):
    
    if not channels:
      channels = range(self.nChannels)
    
    channels = [tuple(channels)]
    
    maxVal = self.data[channels].max()
    if threshold is None:
      limit = maxVal * defaultProp
    else:
      limit = threshold
    
    boolArray = self.data[channels] < limit
    indices = boolArray.nonzero()
        
    self.data[indices] = limit

    self.data[channels] -= limit
    self.data[channels] *= maxVal / (maxVal-limit)

  # exporting array data
  def writeData(self, fileName, separator=' '):
  
    fileObj = open(fileName, 'w')
    
    # loops through array and converts identifiers as strings
    for i in range(self.nRows):
      rowName = str(self.rowData[i])
      
      for j in range(self.nCols):
        colName = str(self.colData[j])

        # get data
        values = self.data[:,i,j]

        # line of text: row, column, value
        lineData = [rowName, colName]
        lineData += ['%.3f' % (v,) for v in values]
        
        # joins strings
        line = separator.join(lineData)
        # write to file object
        fileObj.write(line + '\n') 
  
  # created picture  
  def makeImage(self, squareSize=20, channels=None):
    
    # extreme values and data range
    minVal = self.data.min()
    maxVal = self.data.max() 
    dataRange = maxVal - minVal  

    # subtract minVAl for 0(black), 255=brightest
    adjData = (self.data - minVal) * 255 / dataRange
    # converted to 8-bit
    adjData = array(adjData, uint8)
   
    # 1 channel:red,green,blue from data layer; else up to 3 layers
    if not channels:
      if self.nChannels == 1:
        channels = (0,0,0) # Greyscale
      else:
        channels = list(range(self.nChannels))[:3]

    # blank channels: append 0
    pixmap = []
    for i in channels:
      if i is None:
        pixmap.append(zeros((self.nRows, self.nCols), uint8))
      else:
        pixmap.append(adjData[i])
        
    # add zeros if channels<3
    while len(pixmap) < 3:
      pixmap.append(zeros((self.nRows, self.nCols), uint8))
     
    # 3 color layers stacked along depth axis; create image
    pixmap = dstack(pixmap)
    img = Image.fromarray(pixmap, 'RGB')

    # resize image to squares in each row/column
    width = self.nCols * squareSize
    height = self.nRows * squareSize
    img = img.resize((width, height))
    
    return img
  
  # load sample file    
  imgFile = 'RedGreenArray.png'
  rgArray = loadArrayImage(imgFile, 'TwoChannel', 18, 17)
  rgArray.writeData('RedGreenArrayData.txt')