#
# Copyright (c) 2015-2016 Javier G. Orlandi <javierorlandi@javierorlandi.com>
# - Universitat de Barcelona, 2015-2016
# - University of Calgary, 2016
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# Based on the Python module for reading Hamamatsu DCIMG files from Stuart Littlefair
# https://github.com/StuartLittlefair/dcimg
#

# Hamamatsu DCIMG ImageJ VirtualStack Opener
# ------------------------------------------
# This script quickly opens as a VirtualStack the typical DCIMG files generated with 
# HCIMage and Hamamatsu Orca cameras (tested on Orca Flash 4.0 and HCImage Live 4.3).
#

from ij import IJ
from ij.io import FileInfo
from ij import VirtualStack, ImagePlus
from ij.plugin import FileInfoVirtualStack
from ij.gui import MessageDialog
from ij.plugin.frame import PlugInFrame
from ij.gui import GenericDialog
from java.awt.Dialog import ModalityType
from ij.gui import HTMLDialog
#from org.python.core.util.StringUtil import toBytes
#from org.python.core.util.StringUtil import fromBytes
import struct
import os

class CorrectedVirtualStack(FileInfoVirtualStack):
  def __init__(self, fileinfo, header, sess_hdr, crop_info):
    
    self.nImages = fileinfo.nImages
    self.header = header
    self.sess_hdr = sess_hdr
    self.crop_info = crop_info
    self.filePath = fileinfo.filePath
    self.bytes_per_img = header['bytes_per_img']
    # Gap between images (in bytes) is 32, as defined in your FileInfo.
    self.gap = 32  
    self.binning = header['binning']
    # Compute the target line using MATLAB’s formula:
    # target_line = floor((1024 - dc_y0 + 1) / dc_binning)
    # In Python (0-indexed) we use:
    self.target_line = (1023 - crop_info['y0']) // self.binning

    FileInfoVirtualStack.__init__(self, fileinfo)
    # IJ.log("target line #: " + str(self.target_line))

  def getProcessor(self, slice):
    # IJ.log("Processor got for slice #: " + str(slice))
    ip = super(CorrectedVirtualStack, self).getProcessor(slice)
    # Compute data_offset dynamically:
    data_offset = self.header['header_size'] + self.sess_hdr['offset_to_data']
    # For each frame, the correction data is located at:
    # correction_offset = data_offset + (slice-1) * (bytes_per_img + gap) + (bytes_per_img + 12)
    correction_offset = data_offset + (slice - 1) * (self.bytes_per_img + self.gap) + (self.bytes_per_img + 12)
    with open(self.filePath, 'rb') as f:
      f.seek(correction_offset)
      corr_bytes = f.read(8)  # 4 pixels x 2 bytes each
    correction = struct.unpack('<4H', corr_bytes)
    # Replace the first 4 pixels in the target line with the correction values.
    for col in range(4):
      ip.set(col, self.target_line, correction[col])
      # IJ.log("Correction: " + str(correction[col]))
    return ip

def main():
  imp = IJ.getFilePath("Select DCIMG file")
  if not imp: return
  root, ext = os.path.splitext(imp)
  if ext.lower() != '.dcimg':
    cFrame = PlugInFrame('ERR DLG')
    MessageDialog(cFrame, 'ERROR', 'Expected extension .dcimg')
    return

  #Lets start
  fID = open(imp, 'rb')
  hdr_bytes = read_header_bytes(fID)
  hdr = parse_header_bytes(fID, hdr_bytes)
  sess_hdr = parse_sess_header(fID, hdr)
  crop_info = read_crop_info(fID, hdr, deprecated=False)

  data_offset = hdr['header_size'] + sess_hdr['offset_to_data']
  
  metadataStr = beginMetadata()
  for key, value in hdr.iteritems():
    metadataStr += addMetadataEntry(key, str(value))
  
  metadataStr += endMetadata()
  metadataDlg = HTMLDialog("DCIMG metadata", metadataStr, 0)
  size = metadataDlg.getSize()
  if size.width < 300:
    size.width = 300
  if size.height < 500:
    size.height = 500
  metadataDlg.setSize(size)

  finfo = FileInfo()
  finfo.fileName = imp
  # finfo.isdcimg = True
  finfo.width = hdr['xsize']
  finfo.height = hdr['ysize']
  finfo.nImages = hdr['nframes']
  finfo.offset = data_offset #int(1096+(12+2)*8)
  finfo.fileType = hdr['bitdepth']/8 #Ugh
  finfo.intelByteOrder = 1
  finfo.gapBetweenImages = 32
  finfo.fileFormat = 1
  finfo.samplesPerPixel = 1
  finfo.displayRanges = None
  finfo.lutSize = 0
  finfo.whiteIsZero = 0
  vs = VirtualStack()
  finfo.virtualStack = vs
  # FileInfoVirtualStack(finfo)
  # CorrectedVirtualStack(finfo.width, finfo.height, finfo.nImages,imp, hdr, sess_hdr, crop_info)
  CorrectedVirtualStack(finfo, hdr, sess_hdr, crop_info)
  # finfo.virtualStack = vs
  # FileInfoVirtualStack(finfo)
  print(finfo)
  # IJ.log("Data offset computed as: " + str(data_offset))

def addMetadataEntry(name, val):
  return "<tr><td style='padding:0 25px 0 0px;'><b>" + name + "</b></td><td>" + val + "</td></tr>"
  
def beginMetadata():
  return "<table border=0 cellspacing=0>"
  
def endMetadata():
  return "</table>"

def decode_float(self,whole_bytes,frac_bytes):
  whole  = from_bytes(whole_bytes,byteorder='little')
  frac   = from_bytes(frac_bytes,byteorder='little')
  if frac == 0:
    return whole
  else:
    return whole + frac * 10**-(floor(log10(frac))+1)

def read_header_bytes(self):
  self.seek(0)
  # initial metadata block is 232 bytes
  return self.read(712)
    
def parse_header_bytes(self,hdr_bytes):
  header = {}

  header['footer_loc'] = from_bytes(hdr_bytes[120:124],byteorder='little')
  header['nframes'] = struct.unpack('<I', hdr_bytes[36:40])[0]
  header['header_size'] = struct.unpack('<I', hdr_bytes[40:44])[0]
  # Example: extract bitdepth (assuming stored at 176–179) and other fields:
  header['bitdepth'] = 8 * struct.unpack('<I', hdr_bytes[176:180])[0]
  header['filesize'] = struct.unpack('<Q', hdr_bytes[48:56])[0]  # uint64 from index 48
  header['xsize'] = struct.unpack('<I', hdr_bytes[184:188])[0]
  header['ysize'] = struct.unpack('<I', hdr_bytes[188:192])[0]
  header['bytes_per_row'] = struct.unpack('<I', hdr_bytes[192:196])[0]
  header['bytes_per_img'] = struct.unpack('<I', hdr_bytes[196:200])[0]
  header['binning'] = int(header['bytes_per_row'] / header['xsize'] / (header['bitdepth'] / 8))
  return header

def parse_sess_header(f, header):
  """
  Reads the session header from the file.
  The sess_header is 100 bytes long and is located at header['header_size'].
  """
  f.seek(header['header_size'])
  sess_hdr_bytes = f.read(100)
  sess_header = {}
  sess_header['session_size'] = struct.unpack('<Q', sess_hdr_bytes[0:8])[0]
  # Skip 13 uint32 (52 bytes) then read nframes at offset 60–63:
  sess_header['nframes'] = struct.unpack('<I', sess_hdr_bytes[60:64])[0]
  sess_header['byte_depth'] = struct.unpack('<I', sess_hdr_bytes[64:68])[0]
  # Skip 4 bytes (offset 68–71)
  sess_header['xsize'] = struct.unpack('<I', sess_hdr_bytes[72:76])[0]
  sess_header['ysize'] = struct.unpack('<I', sess_hdr_bytes[76:80])[0]
  sess_header['bytes_per_row'] = struct.unpack('<I', sess_hdr_bytes[80:84])[0]
  sess_header['bytes_per_img'] = struct.unpack('<I', sess_hdr_bytes[84:88])[0]
  # Skip 2 uint32 (8 bytes, offset 88–95)
  sess_header['offset_to_data'] = struct.unpack('<I', sess_hdr_bytes[96:100])[0]
  return sess_header

def read_crop_info(f, header, deprecated=False):
  """
  Reads the crop info structure.
  For non-deprecated files, this is at header['header_size'] + 760.
  For deprecated files, it is at header['header_size'] + 712.
  The structure contains 4 uint16 values: x0, xsize, y0, ysize.
  """
  offset = header['header_size'] + (712 if deprecated else 760)
  f.seek(offset)
  crop_bytes = f.read(8)
  crop_info = {}
  crop_info['x0'], crop_info['xsize'], crop_info['y0'], crop_info['ysize'] = struct.unpack('<4H', crop_bytes)
  return crop_info

# There is probably an easier way to do that
def from_bytes (data, byteorder = 'little'):
  if byteorder!='little':
    data = reversed(data)
  num = 0
  for offset, byte in enumerate(data):
    #nb = toBytes(byte)
    nb = struct.unpack('B', byte[0])[0]
    #num += nb[0] << (offset * 8)
    num += nb << (offset * 8)
  return num

def sizeof_fmt(num, suffix='B'):
  for unit in ['','K','M','G','T','P','E','Z']:
    if abs(num) < 1024.0:
      return "%3.1f%s%s" % (num, unit, suffix)
    num /= 1024.0
  return "%.1f%s%s" % (num, 'Yi', suffix)
    
if __name__ == '__main__':
  main()
