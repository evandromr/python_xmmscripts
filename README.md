Py-XMM-scripts
============

Python scripts to automate the process of data reduction and generates scientific products from XMM-Newton data.

  - uses python's **`subprocess`** module to run sas tasks
  - uses python's **`os`** module to manipulate folder paths and files
  - uses python's **`glob`** module to find files by name, path and regular expressions
  - uses **`astropy.io.fits`** to read relevant data from file headers, and manipulate files if necessary
