## NAME
Pscad - Terminal based OpenSCAD file editor

## SYNOPSIS
`pscad.py [-h] [-o OUT_FILE] IN_FILE`

## DESCRIPTION
Pscad will open and parse `IN_FILE`. The file will not automatically be written to.

* `-h, --help` - show usage information and exit
* `-o, --outfile OUT_FILE` - When this file is given Pscad will write the current state of the opened document on every change. This can be used to have OpenSCAD monitor the file and render automatically.

## COMMANDS
### CONTROL
* `z` - Undo last action.
* `Z` - Redo last undo.
* `q` - Quit Pscad.
* `Q` - Quit Pscad even if document is not (auto) written.
* `w` - Write to IN_FILE.
* `esc` - Reset edits and close dialogs

### NAVIGATION
`up/down, home/end, page up/down`

### TREE MANIPULATION
* `y` - Yank single node. Copy to clipboard.
* `Y` - Yank node and its children. Copy to clipboard.
* `x` - Delete node from tree. Its children will be transferred to its parent.
* `X` - Delete node and children from tree.
* `p` - Paste clipboad contents after selected node as sibbling.
* `P` - Paste clipboad contents before selected node as sibbling.
* `g` - Gobble up next sibling and make it last child.
* `G` - Degobble last child make it a sibling.
* `a` - Insert new node as first child.
* `A` - Inser new node as next sibling.
* `Tab` - Push the node in sibling's child list.
* `STab` - Pop node from parents child list and become a sibling.
* `enter` - Start editing a node.

### MODIFIERS
* `*` - Toggle *disable*
* `!` - Toggle *show only*
* `#` - Toggle *highlight*
* `%` - Toggle *transparent*
* `/` - Toggle comment

### SHORTCUTS
* `d` - New child node difference()
* `D` - New parent node differnce()
* `u` - New child node union()
* `U` - New parent node union()
* `i` - New child node intersection()
* `I` - New parent node intersection()
* `t` - New child node translate()
* `T` - New parent node	translate()
* `r` - New child node rotate()
* `R` - New parent node rotate()
* `s` - New child node scale()
* `S` - New parent node scale()

## AUTHOR
Yuri Schaeffer <yuri@schaeffer.tk>
## REPORTING BUGS
Email or Github
## LICENCE
MIT
## SEE ALSO
openscad(1)
