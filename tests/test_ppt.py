# test_ppt.py

import pytest

from ppt import OddsOracleServer


@pytest.fixture(scope="module")
def ppt_client():
    client = OddsOracleServer(trial=100000)
    client.start_ppt()
    client.board = "Ks4h3c"
    return client

def test_rank_query(ppt_client):
    rank = ppt_client.rank_query(25, "10%", "50%", "flop")
    assert 0 <= rank <= 100, f"Rank should be between 0 and 100, got {rank}"

def test_in_range_query(ppt_client):
    in_range = ppt_client.in_range_query("AA", "10%", "As")
    assert 0 <= in_range <= 100, f"InRange should be between 0 and 100, got {in_range}"
