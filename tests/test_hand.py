from hand import parse_hand, remove_parentheses


def test_parse_hand_with_macro_and_board():
    hand_string = "$4B2:(Jss+,9K+)"
    board_string = "Ks3s3s6h7d"

    result = parse_hand(hand_string, board_string)


    assert isinstance(result, str)
    assert "+" not in result

def test_remove_parentheses():
    range_str = "50%:(((A,4,5):(34,ss)))()"
    cleaned = remove_parentheses(range_str)
    assert cleaned == "50%:(A,4,5):(34,ss)"

