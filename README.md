# libgds 1.0

Desctiption: Python library to handle GDS version 2 (GDS2 or GDSII) data.

## Files

### gds.py
core of the library. Read/Write GDS file. See doc for more info how to use it.

### gds2ascii <file.gds>
Translate the binary  <file.gds> in a human readable ASCII <file.gds.txt> file.
Note: (destination is not pwd, but the same as <file.gds>)

### plsmaker.py
let you create a position list file for Raith patterning software
