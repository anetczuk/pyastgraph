## <a name="main_help"></a> python3 -m astgraph --help
```
usage: __main__.py [-h] [-f FILES [FILES ...]] [-d DIR]
                   [--filterdown N [N ...]] [--filterup N [N ...]]
                   [--showdefs] --outsvgfile OUTSVGFILE
                   [--outdotfile OUTDOTFILE] [--outhtmlfile OUTHTMLFILE]
                   [--outseqdiag OUTSEQDIAG] [--outseqsvg OUTSEQSVG] [-ddd]

Thread graph generator

optional arguments:
  -h, --help            show this help message and exit
  -f FILES [FILES ...], --files FILES [FILES ...]
                        Files to analyze
  -d DIR, --dir DIR     Path to directory to search .py files
  --filterdown N [N ...]
                        Space separated list of regex strings applied on found
                        items to be included in diagram (otherwise items will
                        be excluded)
  --filterup N [N ...]  Space separated list of regex strings applied on found
                        items to be included in diagram (otherwise items will
                        be excluded)
  --showdefs            Show defs relation on use graph (fixes dot 'init_rank'
                        error)
  --outsvgfile OUTSVGFILE
                        Path to output SVG file
  --outdotfile OUTDOTFILE
                        Path to output DOT file
  --outhtmlfile OUTHTMLFILE
                        Path to output HTML file
  --outseqdiag OUTSEQDIAG
                        Path to output PlantUml sequence diagram
  --outseqsvg OUTSEQSVG
                        Path to output PlantUml sequence diagram as SVG
  -ddd, --dumpdebugdata
                        Dump various debug data like intermediate structures
                        and graphs
```
