# DCIMG_opener.py
### Introduction
Here I wrote this Jython script file to directly read Hamamatsu dcimg files with Fiji ImageJ based on a previous code.
<em><b>Update Feb. 26, 2025  We added support for the new dcimg format acquired by HCImage Ver. > 5.0.</b></em>

### Requirements
- ImageJ/Fiji

### Usage
For anyone who wants to process dcimg files (acquired by Hamamatsu cameras), you can put the Jython file into **`[your ImageJ folder]//plugins//Scripts//`**, and then you can open the dcimg files as virtual stacks from the Plugins menu.
Note that, if you are using an old dcimg-api, you may need to change `crop_info = read_crop_info(fID, hdr, deprecated=False)` in line 100 to `crop_info = read_crop_info(fID, hdr, deprecated=True)`.

# dcimg.m
### Introduction
Here I wrote a Matlab class file to directly read Hamamatsu dcimg files.

<em><b>Update Jul. 16, 2024  We added support for the new dcimg format acquired by HCImage Ver. > 5.0.</b></em>

### Requirements
- Matlab R2006+

### Usage
- To get information from .dcimg file
```matlab
dcim = dcimg(scrname);
dc_hdr = dcim.dc_file_header;
dc_sess_hdr = dcim.dc_sess_header; % The main file info is in this struct
```
`scrname` The filename of the dcimg file.\
`dcim` The read dcimg structure including all the info of the file.
- To get portion/all of the content of the .dcimg file
```matlab
dcim = dcimg(scrname,scrind);
im = dcim.data;
```
`scrname` The filename of the dcimg file.\
`scrind` The indices of the portion slices you want to read. E.g., 1:10, \[1,2,3,4\], etc.\
`dcim` The read dcimg structure including all the info of the file.\
`im` The image data you read. This is in the 'data' field of the dcimg struct.

# dcimg2tiff.py
### Introduction
This package also includes a Python program to transform Hamamatsu dcimg files to multipage tif files.\
<em>\[NOTE\] To avoid large file errors, this program limits the total pixel number of the file within 2^31.</em>

<em>\[NOTE\]To support the new dcimg format acquired by HCImage Ver. > 5.0, go to `dcimg.py` after the installation, navigate to the function `_parse_header` and change the line `i = self._header_size + 712` to `i = self._header_size + 760`. </em>

### Requirements
- Python 3.5+
- numpy (```pip install numpy```)
- tifffile (```pip install tifffile```)
- dcimg (```pip install dcimg```)
- rich (```pip install rich```)
### Usage
```python
dcimg2tiff(scrname,destfolder)
```

`scrname` The filename of the dcimg file.\
`destfolder` The destination folder to store tif files.

# Acknowledgement
Please acknowledge Xuanwen Hua's contribution if this package is used in your work. 
For any further questions, please feel free to DM me on Github. Thank you!\
\- Mar. 24th, 2022
PLEASE NOTE THAT I DO NOT USE WECHAT OR ANY CHINESE SOCIAL MEDIA.
