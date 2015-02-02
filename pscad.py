#!/bin/env python

import curses
from Datastruct import Node
import importer
from copy import deepcopy

def usage(win):
    helptext = "yYxXpP (in) [dui trs]"
    my, mx = win.getmaxyx()
    win.addnstr(my-1, mx-1-len(helptext), helptext, mx-1, curses.A_REVERSE)
    
def print_buffer(win, buffer):
    if not buffer:
        text = "Buffer empty"
    elif buffer.children:
        text = "Buffer: %s {...}" % str(buffer) 
    else:
        text = "Buffer: " + str(buffer)
    
    my, mx = win.getmaxyx()
    win.addnstr(my-1, 0, text, mx-1, curses.A_REVERSE)

def render(node, pwin, sel_node, index=0, depth=0, root=True):
    y,x = pwin.getyx()
    highlight = 0
    offset = 0
    INDENT = 4
    my, mx = pwin.getmaxyx()

    if not index%2:
        offset = 1
    
    if root:
        y, x = 0, 0
    if node == sel_node:
        highlight = curses.A_BOLD|curses.color_pair(3)
    pwin.addnstr(y, x, " "*mx, mx-x-1, highlight)
    pwin.addnstr(y, x, str(node), mx-x-1, highlight)

    h = 1;
    for i, child in enumerate(node.children):
        if y+h+1 > my:
            break
        pwin.move(y+h, x+INDENT)
        ch = render(child, pwin, sel_node, i+offset, depth+1, False)
        for j in range(ch):
            pwin.addnstr(y+h+j, x, " "*INDENT, mx-x-1, highlight)
        h += ch
    return h

def height(node, sel_node): #-> height, sel_height
    s = None
    l = None
    if node == sel_node: s = 0
    h = 1;
    for i, child in enumerate(node.children):
        ch, sel, hh = height(child, sel_node)
        if sel != None:
            s = h+sel
            l = hh
        h += ch
    if s == 0:
        l = h
    return h, s, l

def main(stdscr):
    curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_BLUE)
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_WHITE)
    buffer = None

    tree = None
    sel_node = tree
    scroll = 0
    usage(stdscr)
    print_buffer(stdscr, buffer)
    while 1:
        c = stdscr.getch()
        if c == ord('n'):
            #make child of selected node
            curses.echo()
            s = stdscr.getstr(10,0, 15)
            curses.noecho()
            node = Node(s)
            stdscr.addnstr(10,0, " "*15, 15)
            if not tree or not sel_node:
                tree = node
                sel_node = node
            else:
                sel_node.add_child(0, node)
                sel_node = node
                
        elif c == ord('i'): #import
            tree = importer.import_scad('/home/yuri/Documents/headphone/headphon0.scad')
            sel_node = tree
        elif c == ord('q'): #quit
            break
        elif c == ord('Y'):
            if sel_node:
                buffer = sel_node
                if not sel_node.parent:
                    tree = None
                    sel_node = None
                else:
                    sel_node = sel_node.parent.rnext(sel_node)
                    if not sel_node:
                        sel_node = tree
                    buffer.parent.children.remove(buffer)
        elif c == ord('y'):
            if sel_node:
                buffer = sel_node
                if not sel_node.parent:
                    pass
                else:
                    sel_node = sel_node.next()
                    i = buffer.parent.children.index(buffer)

                    buffer.parent.children.remove(buffer)
                    buffer.children.reverse()
                    for child in buffer.children:
                        buffer.parent.add_child(i, child)
                        child.parent = buffer.parent
                    buffer.children = []
        elif c == ord('X'):
            if sel_node:
                t_buffer = sel_node
                if not sel_node.parent:
                    tree = None
                    sel_node = None
                else:
                    sel_node = sel_node.parent.rnext(sel_node)
                    if not sel_node:
                        sel_node = tree
                    t_buffer.parent.children.remove(t_buffer)
                    t_buffer = None
        elif c == ord('x'):
            if sel_node:
                t_buffer = sel_node
                if not sel_node.parent:
                    pass
                else:
                    sel_node = sel_node.next()
                    i = t_buffer.parent.children.index(t_buffer)

                    t_buffer.parent.children.remove(t_buffer)
                    t_buffer.children.reverse()
                    for child in t_buffer.children:
                        t_buffer.parent.add_child(i, child)
                        child.parent = t_buffer.parent
                    t_buffer.children = []
                    t_buffer = None
        elif c == ord('P'):
            if not buffer:
                pass
            elif sel_node and not sel_node.parent:
                pass
            elif sel_node:
                i = sel_node.parent.children.index(sel_node)
                sel_node.parent.add_child(i, buffer)
                buffer.parent = sel_node.parent
                buffer = deepcopy(buffer)
            else:
                tree = buffer
                buffer = deepcopy(buffer)
                tree.parent = None
                sel_node = tree
        elif c == ord('p'):
            if not buffer:
                pass
            elif sel_node and not sel_node.parent:
                pass
            elif sel_node:
                i = sel_node.parent.children.index(sel_node)
                sel_node.parent.add_child(i+1, buffer)
                buffer.parent = sel_node.parent
                buffer = deepcopy(buffer)
            else:
                tree = buffer
                buffer = deepcopy(buffer)
                tree.parent = None
                sel_node = tree

        elif c == curses.KEY_UP:
            if sel_node:
                sel_node = sel_node.prev()
        elif c == curses.KEY_DOWN:
            if sel_node:
                sel_node = sel_node.next()

        if tree:
            y,x = stdscr.getmaxyx()
            tree_h, sel_idx, sel_h = height(tree, sel_node)
            pad = curses.newpad(tree_h, x)
            render(tree, pad, sel_node, sel_idx)


            if sel_idx < scroll:
                scroll -= y/2
                scroll = max(0, scroll)
            elif sel_idx-scroll >= y-1:
                scroll += y/2
            elif (sel_idx-scroll)+sel_h > y and sel_h<y:
                d = (sel_idx-scroll+sel_h) - y
                scroll += d

            stdscr.addnstr(y-1, 15, str((sel_idx, sel_h, y, scroll)), x-1, curses.A_REVERSE)

            pad.refresh(0+scroll,0, 0,0, y-2, x-1)
            if tree_h-scroll < y:
                pad = curses.newpad(y-(tree_h-scroll), x)
                pad.refresh(0,0, (tree_h-scroll),0, y-2, x-1)
                
        else:
            stdscr.clear()

        usage(stdscr)
        print_buffer(stdscr, buffer)


curses.wrapper(main)
#~ import_scad('/home/yuri/Documents/headphone/headphon0.scad')
#~ import_scad('/home/yuri/Documents/headphone/test.scad')
