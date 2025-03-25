#!/usr/bin/env python3

# gui_elements.py ---
#
# Filename: gui_elements.py
# Description:
# Author: Johann
# Maintainer:
# Created: Don Mar 17 10:51:40 2016 (+0100)
# Version:
# Last-Updated:
#           By: jejellyroll
#     Update #: 1
# URL:
# Keywords:
# Compatibility:
#
#

# Commentary:
# Implements classes for gui subelements
#
#
#

# Change Log:
#
#
#
#


# Code:


import logging
from tkinter import END, BooleanVar, E, N, S, StringVar, W, ttk

from utils import (
    EV_PLAYER_FRAME_PADDING,
    FONT_FAM,
    FONT_SIZE,
    FRAME_PADDING,
    INPUT_LENGTH,
    PADX,
    PADY,
    PRE_INPUT_LENTH,
    SPACES_BEFORE_SUMMARY_LINE,
    START_RANGE_WIDTH,
)


class RangeFormatterMixin:
    @staticmethod
    def add_parenthesis(range_string: str) -> str:
        """Ajoute des parenthèses si la chaîne contient des séparateurs indiquant
        une combinaison d’éléments et si ce n’est pas déjà encadré."""
        if not range_string or len(range_string) < 3:
            return range_string
        if range_string.startswith('(') and range_string.endswith(')'):
            return range_string
        delimiters = [',', '!', ':', '+']
        if any(d in range_string for d in delimiters):
            return f"({range_string})"
        return range_string


class ScrolledTextLogger(logging.Handler):
    def __init__(self, widget):
        logging.Handler.__init__(self)
        self.widget = widget

    def emit(self, message):
        msg = self.format(message)
        def append():
            self.widget.configure(state='normal')
            self.widget.insert(END, msg + '\n')
            self.widget.configure(state='disabled')
            # Autoscroll to the bottom
            self.widget.see(END)
        # This is necessary because we can't modify the Text from other threads
        self.widget.after(0, append)


class RangeLine:
    def __init__(self, master,  x_box=True, text_field_length=INPUT_LENGTH, freq=True, equity=True):
        column=0 # counter number of already created items
        self.is_x_box=x_box
        self.is_freq=freq
        self.is_equity=equity
        self.input_range=StringVar()
        self.master_frame=master

        if self.is_x_box:
            self.x_box_value=BooleanVar()
            self.xbox=ttk.Checkbutton(self.master_frame, variable=self.x_box_value)
            self.x_box_value.set(0)
            self.xbox.grid(column=column, row=0, sticky=W)
            column=column+1
        self.input_field=ttk.Entry(self.master_frame,textvariable=self.input_range,width=INPUT_LENGTH,font=(FONT_FAM,FONT_SIZE))
        self.input_field.grid(column=column, row=0, sticky=W)
        column=column+1

        if self.is_freq:
            self.freq=StringVar()
            self.freq_lable=ttk.Label(self.master_frame,width=4,anchor=E)
            self.freq_lable.grid(column=column, row=0, sticky=W)
            self.freq_lable['textvariable'] = self.freq
            self.freq.set("0.0")
            column=column+1

        if self.is_equity:
            self.equity=StringVar()
            self.equity_lable=ttk.Label(self.master_frame,width=4,anchor=E)
            self.equity_lable.grid(column=column, row=0, sticky=W)
            self.equity_lable['textvariable'] = self.equity
            self.equity.set("0.0")
            column=column+1

        for element in self.master_frame.winfo_children():
            element.grid_configure(padx=PADX, pady=PADY)

    def get_xbox(self):
        return self.x_box_value.get()

    def get_range(self):
        return self.input_range.get()

    def set_freq(self, value):
        if value < 0 or value > 100:
            self.freq.set("??.?")
        else:
            self.freq.set(f"{value:.1f}")
        return

    def set_equity(self, value):
        if value < 0 or value > 100:
            self.equity.set("??.?")
        else:
            self.equity.set(f"{value:.1f}")
        return

class Range(RangeFormatterMixin):
    def __init__(self, master, title, start_range=" ", num_sub_ranges=4, text_field_length=INPUT_LENGTH, freq=True, equity=True, x_box=True):
        self.title_frame=ttk.Frame(master, padding=FRAME_PADDING)
        self.title_frame.grid(column=0, row=0, sticky=W)

        self.title=ttk.Label(self.title_frame, text=title+":", width=6)
        self.title.grid(column=0,row=0, sticky=W)

        self.start_range_label=ttk.Label(self.title_frame, width=START_RANGE_WIDTH)
        self.start_range_label.grid(column=1,row=0, sticky=W)
        self.start_range=StringVar()
        self.start_range_label['textvariable'] = self.start_range
        self.start_range.set(start_range)

        self.start_range_full=start_range

        self.equity_freq_label=ttk.Label(self.title_frame, text="FREQ:    EQ:")
        self.equity_freq_label.grid(column=3, row=0, sticky=W)

        self.range_eq_label=ttk.Label(self.title_frame,width=4, anchor=E)
        self.range_eq_label.grid(column=4,row=0, sticky=W)
        self.range_eq=StringVar()
        self.range_eq_label['textvariable'] = self.range_eq
        self.range_eq.set("0.0")

        self.num_sub_ranges=num_sub_ranges
        self.sub_range_frames=[]
        self.sub_range_list=[]
        for i in range(0,self.num_sub_ranges):
            self.sub_range_frames.append(ttk.Frame(master, padding=FRAME_PADDING))
            self.sub_range_frames[i].grid(column=0, row=i+1, sticky=W)
            self.sub_range_list.append(RangeLine(self.sub_range_frames[i], x_box, text_field_length, freq, equity))

        self.summary_frame=ttk.Frame(master, padding=FRAME_PADDING)
        self.summary_frame.grid(column=0, row=self.num_sub_ranges+1, sticky=W)

        self.summary_title=ttk.Label(self.summary_frame, text=" "*SPACES_BEFORE_SUMMARY_LINE + "Selection Combined (Frequency Equity): ")
        self.summary_title.grid(column=0,row=0, sticky=W)

        self.summary_freq_label=ttk.Label(self.summary_frame,width=5,anchor=E)
        self.summary_freq_label.grid(column=1,row=0, sticky=W)
        self.summary_freq=StringVar()
        self.summary_freq_label['textvariable'] = self.summary_freq
        self.summary_freq.set("0.0")


        self.summary_eq_label=ttk.Label(self.summary_frame,width=5,anchor=E)
        self.summary_eq_label.grid(column=3,row=0, sticky=W)
        self.summary_eq=StringVar()
        self.summary_eq_label['textvariable'] = self.summary_eq
        self.summary_eq.set("0.0")

    def get_xbox(self, index):
        if index >= len(self.sub_range_list):
            return False
        return self.sub_range_list[index].get_xbox()

    def set_start_range(self, range_string):
        self.start_range_full=range_string
        if len(range_string) > START_RANGE_WIDTH:
            self.start_range.set(range_string[:START_RANGE_WIDTH-4]+"...")
        else:
            self.start_range.set(range_string)

    def get_start_range(self):
        return self.start_range_full

    def set_freq(self, index, value):
        if index >= len(self.sub_range_list):
            return
        self.sub_range_list[index].set_freq(value)

    def set_summary_freq(self, value):
        if value < 0 or value > 100:
            self.summary_freq.set("??.?")
        else:
            self.summary_freq.set(f"{value:.1f}")
        return

    def set_equity(self, index, value):
        if index >= len(self.sub_range_list):
            return
        self.sub_range_list[index].set_equity(value)

    def set_summary_equity(self, value):
        if value < 0 or value > 100:
            self.summary_eq.set("??.?")
        else:
            self.summary_eq.set(f"{value:.1f}")
        return

    def set_range_equity(self, value):
        if value < 0 or value > 100:
            self.range_eq.set("??.?")
        else:
            self.range_eq.set(f"{value:.1f}")
        return


    def get_selected_range(self):
        selected_parts = []
        for i in range(len(self.sub_range_list)):
            if self.get_xbox(i) and self.sub_range_list[i].get_range():
                selected_parts.append(self.sub_range_list[i].get_range())
        if selected_parts:
            selected_range = ",".join(selected_parts)
            # Ajout conditionnel des parenthèses sur chaque partie
            return f"{self.add_parenthesis(self.get_start_range())}:{self.add_parenthesis(selected_range)}"
        else:
            return self.get_start_range()


    def get_certain_range(self, index=[]): # return ranges listed in index list (0-3) with start range; empty string if index list or ranges are empty
        selected_range=""
        for i in index:
            if self.get_range(i):
                selected_range+=","+self.get_range(i)
        if selected_range:
            return self.add_parenthesis(self.get_start_range()) + ":" +self.add_parenthesis(selected_range[1:])
        else:
            return ""

    def get_range(self, index, ignore_selection=True, start_range=False): # remove ranges listed above index
                                                                          # ignore_selection == False -> Doesnt exclude selected ranges
        if index >= len(self.sub_range_list):
            return ""
        exclude_range=""
        for i in range (0, index):
            sub_range=self.sub_range_list[i].get_range()
            if sub_range:
                if ignore_selection or not self.get_xbox(i):
                    exclude_range=exclude_range + sub_range + ","

        include_range=self.add_parenthesis(self.sub_range_list[index].get_range())

        if exclude_range:
            exclude_range=self.add_parenthesis(exclude_range[:-1])
            if include_range:
                if start_range:
                    return self.add_parenthesis(self.get_start_range()) + ":" + self.add_parenthesis(include_range + "!" + exclude_range)
                else:
                    return include_range  + "!" + exclude_range
            else:
                return "" # "*" + "!" + exclude_range
        else:
            if include_range:
                if start_range:
                    return self.add_parenthesis(self.get_start_range()) + ":" + include_range
                else:
                    return self.sub_range_list[index].get_range()
            else:
                return ""



class RangePreflop(RangeFormatterMixin):
    def __init__(self, master, player="Player", text_field_length=INPUT_LENGTH):
        self.title=ttk.Label(master, text=player)
        self.title.grid(column=0, row=0, sticky=W)

        self.include_range=StringVar()
        self.include_range.set("")
        self.exclude_range=StringVar()
        self.exclude_range.set("")

        self.input_range1=ttk.Entry(master,textvariable=self.include_range,width=text_field_length,font=(FONT_FAM,FONT_SIZE))
        self.input_range1.grid(column=0, row=1, sticky=W)

        ttk.Label(master, text=" ! ").grid(column=1, row=1, sticky=W)

        self.input_range2=ttk.Entry(master,textvariable=self.exclude_range,width=text_field_length//2,font=(FONT_FAM,FONT_SIZE))
        self.input_range2.grid(column=2, row=1, sticky=W)

        for element in master.winfo_children():
            element.grid_configure(padx=PADX, pady=PADY)


    def get_range(self):
        if not self.include_range.get():
            return ""
        if not self.exclude_range.get():
            return self.include_range.get()
        else:
            return self.add_parenthesis(self.include_range.get()) + "!" + self.add_parenthesis(self.exclude_range.get())

class EvCalcPlayer:
    def __init__(self,master,player="Player", text_field_length=INPUT_LENGTH, pre_field_length=PRE_INPUT_LENTH):
        self.preframe=ttk.Frame(master,padding=EV_PLAYER_FRAME_PADDING)
        self.preframe.grid(column=0, row=0, sticky=(N, W, E, S))

        self.playerframe=ttk.Frame(master,padding=EV_PLAYER_FRAME_PADDING)
        self.playerframe.grid(column=0, row=1, sticky=(N, W, E, S))

        self.pre=RangePreflop(self.preframe,player,pre_field_length)
        self.post=Range(self.playerframe,"Range")


#
# gui_elements.py ends here
