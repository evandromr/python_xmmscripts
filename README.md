Python XMM_scripts
============

Python scripts to automate the process of data reduction and generates scientific products from [XMM-Newton](http://xmm.esac.esa.int/) data.

  - uses python's **`subprocess`** module to run sas tasks
  - uses python's **`os`** module to manipulate folder paths and files
  - uses python's **`glob`** module to find files by name, path and regular expressions
  - uses **`astropy`** module to read relevant data from file headers, and manipulate files if necessary
    - can substitute by the deprecated **`pyfits`**

### Warning:
  Need to initialize [HEASOFT](http://heasarc.nasa.gov/lheasoft/) and [SAS](http://xmm.esac.esa.int/sas/current/documentation/sas_concise.shtml) environment apropriately beforehand
