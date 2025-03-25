import pytest

from board import (
    RANK_ORDER,
    RANKS,
    SUITS,
    hand_board_intersections,
    pairs,
    parse_board,
    rank_count,
    return_fulls_or_better,
    return_lows,
    return_next_cards,
    return_ranks,
    return_str_flush,
    return_straight_draws,
    return_straights,
    return_string,
    return_suits,
)


# Fixture to create a board from a character string
@pytest.fixture
def sample_board():
    board_string = "AsKs9s9h"
    return parse_board(board_string)

# Fixture to extract rows from the board sample
@pytest.fixture
def ranks(sample_board):
    return return_ranks(sample_board)

def test_parse_board(sample_board):
    # Checks that the board is a list and that each element is a string of 2 characters (e.g. ‘As’).
    assert isinstance(sample_board, list)
    for card in sample_board:
        assert isinstance(card, str)
        assert len(card) == 2

def test_return_ranks(ranks):
    # Check that the ranks obtained are in RANKS
    for r in ranks:
        assert r in RANKS

def test_return_suits(sample_board):
    suits = return_suits(sample_board)
    # Checks that each tuple is consistent
    for count, suit in suits:
        assert suit in SUITS
        assert isinstance(count, int)
        assert count > 0

def test_return_string(sample_board):
    board_str = return_string(sample_board, "river")
    # Checks that the result is a string composed only of valid characters
    assert isinstance(board_str, str)
    for char in board_str:
        assert char in RANKS or char in SUITS

def test_return_next_cards():
    # Test on return_next_cards with all_cards=False
    board_input = "Ks4s3c"
    cards = return_next_cards(board_input, False)
    # Check that each card is a 2-character string and that the cards on the board are not present.
    for card in cards:
        assert isinstance(card, str)
        assert len(card) == 2
    for card in ["Ks", "4s", "3c"]:
        assert card not in cards

def test_return_fulls_or_better(ranks):
    result = return_fulls_or_better(ranks)
    assert isinstance(result, list)

def test_rank_count(ranks):
    counts = rank_count(ranks)
    assert isinstance(counts, list)
    assert len(counts) == 4
    # Each sub-list must be sorted in descending order according to RANK_ORDER
    for sublist in counts:
        if sublist:
            sorted_sublist = sorted(sublist, key=lambda x: RANK_ORDER[x], reverse=True)
            assert sublist == sorted_sublist


def test_hand_board_intersections(ranks):
    intersections = hand_board_intersections(ranks)
    assert isinstance(intersections, list)

def test_return_straights(ranks):
    straights = return_straights(ranks)
    assert isinstance(straights, list)

def test_return_straight_draws(ranks):
    draws = return_straight_draws(ranks)
    assert isinstance(draws, list)

def test_return_str_flush(sample_board):
    str_flush = return_str_flush(sample_board)
    assert isinstance(str_flush, list)

def test_return_lows(ranks):
    lows = return_lows(ranks)
    assert isinstance(lows, list)

def test_pairs(ranks):
    pr = pairs(ranks)
    assert isinstance(pr, list)
