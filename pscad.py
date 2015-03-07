#!/usr/bin/env python3

import curses
import urwid
from Datastruct import Node
from clipboard import Clippy
import importer
from undo import Undo
from pretty import fabulous, addstr
from sys import argv

UNDO_CAP = 1000
SPACE_PER_INDENT = 4
HELP_STRING = "yYxXpPgGuU *!#% (in) [dui trs]"

palette = [
    ('default', 'white', ''),
    ('edit', 'black', 'yellow'),
    ('error', 'white', 'dark red'),
    ('select', 'white', 'dark blue'),
    ('status', 'black', 'white'),
    ('bg', 'white', ''),]
    

# TODO
# hotkeys for diff etc
# fix fablous for function defs

def main(stdscr, infile=None, outfile=None):
    init_colors()
    buffer = None
    undo = Undo(UNDO_CAP)

    if infile:
        tree = importer.import_scad(infile)
        if not tree:
            raise(Exception("Error importing from file %s"%infile))
    else:
        tree = Node("Document root")
    undo.store(tree)
    sel_node = tree
    scroll = 0
    stdscr.refresh()
    while 1:
        y,x = stdscr.getmaxyx()
        sel_idx = tree.offset(sel_node)
        tree_h = tree.descendants + 1
        sel_h = sel_node.descendants + 1
        pad = curses.newpad(tree_h, x)
        render(tree, pad, sel_node)
        if sel_idx < scroll:
            while sel_idx < scroll:
                scroll -= (y//2)
            scroll = max(0, scroll)
        elif sel_idx-scroll >= y-2:
            while sel_idx-scroll >= y-2:
                scroll += y//2
        elif (sel_idx-scroll)+sel_h > y and sel_h<y:
            d = (sel_idx-scroll+sel_h+1) - y
            scroll += d

        # paint screen
        pad.refresh(0+scroll,0, 0,0, y-3, x-1)
        # clear unpainted screen
        if tree_h-scroll < y:
            stdscr.move(tree_h-scroll, 0)
            stdscr.clrtobot()

        print_buffer(stdscr, buffer)
        usage(stdscr)
        status(stdscr)

        changes = F_STAT_CLEAR

        c = stdscr.getch()
        if c == ord('i'): #import
            fn = '/home/yuri/Documents/pscad/headphon0.scad'
            t = importer.import_scad(fn)
            if not t:
                status(stdscr, "Error importing file %s"%(fn))
            else:
                tree = t
                changes = F_STAT_EXPORT|F_STAT_UNDO
                sel_node = tree
                status(stdscr, "imported file %s"%(fn))
        elif c == ord('e'): #export
            r = importer.export_scad('/home/yuri/Documents/pscad/temp.scad', tree)

        if changes & F_STAT_EXPORT and outfile:
            r = importer.export_scad(outfile, tree)

def debug_print_tree(tree, i=0):
    print("  "*i + "< "+str(tree)+" >")
    for c in tree.children:
         debug_print_tree(c, i+1)

            
    
class SelectText(urwid.Widget):

    def __init__(self, node, treelist, buf):
        super(urwid.Widget, self).__init__()
        self.edit = urwid.Edit("", node.content)
        self.text = urwid.Text(node.content)
        # do not wrap
        self.text.set_layout('left', 'clip')
        self.edit.set_layout('left', 'clip')
        key = urwid.connect_signal(self.edit, 'change', SelectText.handler, user_args=[self])
        self.showedit = 0
        self.node = node
        self.treelist = treelist
        self.indent = node.depth()
        self.buf = buf

    def rows(self, size, focus=False):
        return 1

    def sizing(self):
        if self.showedit:
            return self.edit.sizing()
        return self.text.sizing()

    def selectable(self):
        return True

    def handler(self, widget, newtext):
        ## TODO VALIDATE CONTENT, BRIGHT RED ON ERROR
        self.text.set_text(newtext)

    def get_cursor_coords(self, size):
        if self.showedit:
            return self.edit.get_cursor_coords(size)
        return None

    def keypress(self, size, key):
        if key == 'enter':
            self.showedit ^= 1
            self._invalidate() # mark widget as changed
            ## update so an undo can be saved
            if self.showedit == 0:
                self.treelist.update()
            return None
            
        if self.showedit:
            return self.edit.keypress(size, key)
            
        ## in Text mode
        if key == 'g':              ## Be siblings parent
            self.node.gobble()
        elif key == 'G':            ## Be childs sibling
            self.node.degobble()
        elif key == 'tab':          ## Be sibling child
            self.node.cling()
        elif key == 'shift tab':    ## Be parents sibling
            self.node.decling()
        elif key == 'p':            ## Be next sibling
            self.node.merge_after(self.buf.load())
        elif key == 'P':            ## Be previous sibling
            self.node.merge_before(self.buf.load())
        elif key == 'y':            ## Cut node, transfer children to parent
            self.buf.store(self.node.detach())
        elif key == 'Y':            ## Cut subtree
            self.buf.store(self.node.split())
        elif key == 'x':            ## Delete node, transfer children to parent
            self.node.detach()
        elif key == 'X':            ## Delete subtree
            self.node.split()
        elif key == '*':
            self.toggle_modifier("*")
        elif key == '!':
            self.toggle_modifier("!")
        elif key == '#':
            self.toggle_modifier("#")
        elif key == '%':
            self.toggle_modifier("%")
        else:
            return key

        self.treelist.update()
        return None

    def render(self, size, focus=False):
        if self.showedit:
            map2 = urwid.AttrMap(self.edit, 'edit')
        elif focus:
            map2 = urwid.AttrMap(self.text, 'select')
        else:
            map2 = urwid.AttrMap(self.text, 'default')
        return map2.render(size, focus)

    def toggle_modifier(self, char):
        mods = "*!#%"
        if char not in mods:
            return
        t = self.node.content
        for c in t:
            if c not in mods:
                self.node.content = char+t
                return
            elif c == char:
                 self.node.content = t.replace(char, "", 1)
                 return
                 
class TreeListBox(urwid.ListBox):
    def __init__(self, manager, indent_width):
        self.manager = manager
        body = urwid.SimpleFocusListWalker([])
        self.indent = indent_width;
        self.d = 0
        self.update()
        self.buf = Clippy()
        super(TreeListBox, self).__init__(body)

    def update(self):
        self.manager.undo_store()
        self.update_tree = True
        self._invalidate()

    def render(self, size, focus=False):
        if self.update_tree:
            self.update_tree = False
            tree_text = []
            for node in self.manager.get_tree():
                t = SelectText(node, self, self.buf)
                p = urwid.Padding(t, align='left', width='pack', min_width=None, left=node.depth()*self.indent)
                tree_text.append(p)
            if len(self.body) > 0: 
                pos = self.focus_position
            else:
                pos = 0
            self.body.clear()
            self.body.extend(tree_text)
            if pos < len(self.body):
                self.focus_position = pos
            self.d+=1

        
        canvas = super(TreeListBox, self).render(size, focus)
        return canvas

    def keypress(self, size, key):
        global status
        key = super(TreeListBox, self).keypress(size, key)
        if key == 'esc':
            for n in self.body:
                w = n._original_widget
                if w.showedit:
                    w.showedit = 0
                    w._invalidate()
            return None
        elif key == 'u':
            if self.manager.undo():
                self.update_tree = True
                self._invalidate()
            return None
        elif key == 'U':
            if self.manager.reundo():
                self.update_tree = True
                self._invalidate()
            return None
        return key

def show_or_exit(key):
    if key in ('q', 'Q'):
        raise urwid.ExitMainLoop()

class Manager():
    def __init__(self, argv):
        self.tree = Node("No Document loaded!")
        self.undo = Undo(UNDO_CAP)
        self.tree = importer.import_scad(argv[1])


    def undo_store(self):
        self.undo.store(self.tree)

    def undo(self):
        r = self.undo.undo()
        if r:
            self.tree = r
            return True
        return False
        
    def redo(self):
        r = self.undo.redo()
        if r:
            self.tree = r
            return True
        return False

    def get_tree(self):
        return self.tree


if __name__ == "__main__":
    status = urwid.Text("")
    helptext = urwid.Text(HELP_STRING)
    footer = urwid.Pile([status, helptext])
    footer_pretty = urwid.AttrMap(footer, 'status')

    manager = Manager(argv)
    tree_list = TreeListBox(manager, SPACE_PER_INDENT)
    body = urwid.AttrMap(tree_list, 'bg')

    frame = urwid.Frame(body, footer=footer_pretty, focus_part='body')

    main = urwid.MainLoop(frame, palette, unhandled_input=show_or_exit)
    main.run()
