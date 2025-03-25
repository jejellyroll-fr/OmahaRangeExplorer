import logging
import tkinter as tk
from tkinter import ttk

import pytest

from gui_elements import (
    EvCalcPlayer,
    Range,
    RangeLine,
    RangePreflop,
    ScrolledTextLogger,
)


# Fixture to create and destroy a Tk instance
@pytest.fixture
def root():
    r = tk.Tk()
    yield r
    r.destroy()


def test_range_line_get_range(root):
    # Creates a frame and an instance of RangeLine
    frame = ttk.Frame(root)
    rl = RangeLine(frame, x_box=True)
    # By default, no value is entered, so get_range() must return an empty string.
    assert rl.get_range() == ""


def test_range_line_get_xbox(root):
    frame = ttk.Frame(root)
    rl = RangeLine(frame, x_box=True)
    # The checkbox is set to false (0)
    assert rl.get_xbox() is False


def test_range_add_parenthesis(root):
    frame = ttk.Frame(root)
    # Create an instance of Range with a single sub-range so that you can test the add_parenthesis method.
    r = Range(frame, "Test", "A", num_sub_ranges=1, x_box=False, freq=False, equity=False)
    # Si la chaîne contient un '+', elle doit être encadrée de parenthèses.
    assert r.add_parenthesis("A+B") == "(A+B)"
    # If the string contains a comma, parentheses are added.
    assert r.add_parenthesis("a,b") == "(a,b)"
    # If the string is already enclosed in brackets, it remains unchanged.
    assert r.add_parenthesis("(test)") == "(test)"
    # If the string is short (< 3 characters), it is not modified.
    assert r.add_parenthesis("ab") == "ab"
    # Otherwise, the string is returned as is.
    assert r.add_parenthesis("test") == "test"


def test_range_get_selected_range(root):
    frame = ttk.Frame(root)
    # We create a Range with 2 sub-ranges.
    r = Range(frame, "Test", "Start", num_sub_ranges=2, x_box=True, freq=False, equity=False)
    # By default, no box is ticked => the function must return the start range.
    assert r.get_selected_range() == "Start"

    # Simulation: enter ‘sub1’ in the first sub-range and tick the box.
    r.sub_range_list[0].input_range.set("sub1")
    r.sub_range_list[0].x_box_value.set(True)
    expected = r.add_parenthesis("Start") + ":" + r.add_parenthesis("sub1")
    assert r.get_selected_range() == expected


def test_range_preflop_get_range(root):
    frame = ttk.Frame(root)
    rp = RangePreflop(frame, "Player")
    # Test without exclusion: if exclude_range is empty, include_range must be returned.
    rp.include_range.set("A")
    rp.exclude_range.set("")
    assert rp.get_range() == "A"
    # Test with exclusion: wait for concatenation with ‘!’ and enclose in brackets.
    rp.exclude_range.set("B")
    expected = rp.add_parenthesis("A") + "!" + rp.add_parenthesis("B")
    assert rp.get_range() == expected


def test_ev_calc_player(root):
    frame = ttk.Frame(root)
    ecp = EvCalcPlayer(frame, "TestPlayer")
    # Check that the ‘pre’ attribute is an instance of RangePreflop
    assert isinstance(ecp.pre, RangePreflop)
    # Check that the ‘post’ attribute is an instance of Range
    assert isinstance(ecp.post, Range)


def test_scrolled_text_logger(root):
    # Create a Text widget and a logger that uses it
    text_widget = tk.Text(root)
    logger = ScrolledTextLogger(text_widget)
    # Define a simple formatter
    formatter = logging.Formatter('%(message)s')
    logger.setFormatter(formatter)
    # Create a LogRecord
    record = logging.LogRecord("test", logging.INFO, "", 0, "Hello", None, None)
    logger.emit(record)
    # Force execution of all scheduled tasks, including the after() callback
    root.update()
    content = text_widget.get("1.0", tk.END)
    assert "Hello" in content

