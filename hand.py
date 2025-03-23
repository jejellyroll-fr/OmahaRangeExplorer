#!/usr/bin/env python3
# hand.py --- 
# 
# Filename: hand.py
# Description: 
# Author: Johann 
# Maintainer: 
# Created: Mon Mar 14 17:50:36 2016 
# Version: 
# Last-Updated: 
#           By: 
#     Update #: 0
# URL: 
# Keywords: 
# Compatibility: 
# 
# 

# Commentary: 
# 
# Possible to remove additional redudant () in remove parenthesis
# Tue Jan  3 04:05:32 2017 hilo sign - is not good because of AA-TT hands etc

from board import *
import re
import logging
import csv
from utils import RANKS_ORDERED


def replace_macros(hand, macro_file):
    if '$' not in hand:
        return hand

    reader = csv.DictReader(macro_file)
    macros = {}
    for row in reader:
        name = row["macro"].strip()
        expands_to = row["expandsTo"].strip()
        if expands_to.startswith('[') and expands_to.endswith(']'):
            expands_to = expands_to[1:-1]
        macros[name.upper()] = expands_to

    pattern = re.compile(r'\$([A-Za-z0-9_]+)')
    matches = pattern.findall(hand)
    for macro_name in matches:
        key = macro_name.upper()
        if key in macros:
            full_macro = f'${macro_name}'
            expansion = f'({macros[key]})'
            print(f"[DEBUG] Replacing {full_macro} with {expansion}")
            hand = hand.replace(full_macro, expansion)

    if '$' in hand:
        print(f"[ERROR] Unresolved macro in: {hand}")
    return hand


def parse_hand(hand,board_string):
    board = parse_board(board_string)

    # macros working with ppt server??
    try:
        macro_file=open(MACRO_FILE_LOCATION)
    except:
        logging.error("Cannot open MACRO file")
    else:
        hand = replace_macros(hand,macro_file)
        hand = expand_plus_notation(hand)
        macro_file.close()

    hand = replace_strings(hand,board)
    hand = remove_parentheses(hand)
    return hand

def expand_plus_notation(hand):
    """
    Expands shorthand like QQ+, 22+, A2s+, KTo+ to explicit hand list.
    """


    def rank_index(rank):
        try:
            return RANKS_ORDERED.index(rank)
        except ValueError:
            raise ValueError(f"Invalid rank: {rank}")

    # Pocket pairs: e.g., QQ+ → QQ, KK, AA
    def expand_pocket_plus(start_rank):
        return [r + r for r in RANKS_ORDERED[rank_index(start_rank):]]

    # Suited hands: e.g., A2s+ → A2s, A3s, ..., AKs
    def expand_suited_plus(high_rank, low_rank):
        start = rank_index(low_rank)
        return [high_rank + R + 's' for R in RANKS_ORDERED[start:] if R != high_rank]

    # Offsuit hands: e.g., KTo+ → KTo, KJo, KQo, etc.
    def expand_offsuit_plus(high_rank, low_rank):
        start = rank_index(low_rank)
        return [high_rank + R + 'o' for R in RANKS_ORDERED[start:] if R != high_rank]

    # Combo hands without suit: e.g., A2+ → A2, A3, ..., AK
    def expand_combo_plus(high_rank, low_rank):
        start = rank_index(low_rank)
        return [high_rank + R for R in RANKS_ORDERED[start:] if R != high_rank]

    import re
    pocket_pattern = re.compile(r'([2-9TJQKA])\1\+')
    pattern = re.compile(r'([2-9TJQKA])([2-9TJQKA])(s|o)?\+')

    # Expand pocket pairs
    for match in pocket_pattern.finditer(hand):
        start = match.group(1)
        expanded = ','.join(expand_pocket_plus(start))
        hand = hand.replace(match.group(0), f"({expanded})")

    # Expand other combos
    for match in pattern.finditer(hand):
        hi, lo, suited = match.groups()
        if suited == 's':
            expanded = ','.join(expand_suited_plus(hi, lo))
        elif suited == 'o':
            expanded = ','.join(expand_offsuit_plus(hi, lo))
        else:
            expanded = ','.join(expand_combo_plus(hi, lo))
        hand = hand.replace(match.group(0), f"({expanded})")

    return hand



def replace_strings(hand, board):
    """
    Returns string with all + or < expressions replaced.
    """
    ranks = return_ranks(board)
    ranks_no_count = set(ranks)
    suits = return_suits(board)
    flushes = return_flushes(board)
    straights = return_straights(ranks)
    fulls_or_better = return_fulls_or_better(ranks)
    hand_board_int = hand_board_intersections(ranks)
    str_draws = return_straight_draws(ranks)
    kickers = return_kicker(ranks)
    flush_suit = []

    if flushes:
        flush_suit += [flushes[0][1:]]

    str_flush = return_str_flush(board)

    # 3 to 4 card wraps with +
    match_expr = re.compile(r'[' + ''.join(RANKS) + r']{3,4}\+')
    hand_sections = match_expr.findall(hand)
    if hand_sections:
        str_draws = return_straight_draws(ranks)
        for x in hand_sections:
            compare_x = ''.join(sorted(x[:-1], key=lambda x: RANK_ORDER[x], reverse=True))
            if compare_x in str_draws:
                replace_hands = str_draws[:str_draws.index(compare_x)+1]
                hand = hand.replace(x, range_string(replace_hands))

    # Flush / flushdraw / blocker
    match_expr = re.compile(r'[' + ''.join(RANKS) + r'][' + ''.join(SUITS) + r']{1,2}\+')
    hand_sections = match_expr.findall(hand)
    if hand_sections:
        for x in hand_sections:
            compare_x = x[:-1]
            if len(compare_x) == 2:
                flush_blocker = return_flush_blocker(board)
                if compare_x in flush_blocker:
                    replace_hands = flush_blocker[:flush_blocker.index(compare_x)+1]
                    hand = hand.replace(x, range_string(replace_hands))
            else:
                if flushes:
                    flushes = return_flushes(board)
                    if compare_x in flushes:
                        replace_hands = fulls_or_better + flushes[:flushes.index(compare_x)+1]
                        hand = hand.replace(x, range_string(replace_hands))
                    else:
                        flush_drw = return_flushdraws(board, compare_x[-1])
                        if flush_drw:
                            replace_hands = flush_drw[:flush_drw.index(compare_x)+1]
                            hand = hand.replace(x, range_string(replace_hands))

    # Straights, straight draws, hand/board intersections
    match_expr = re.compile(r'[' + ''.join(RANKS) + r']{2}\+')
    hand_sections = match_expr.findall(hand)
    if hand_sections:
        for x in hand_sections:
            compare_x = ''.join(sorted(x[:-1], key=lambda x: RANK_ORDER[x], reverse=True))
            if compare_x in fulls_or_better:
                replace_hands = str_flush + fulls_or_better[:fulls_or_better.index(compare_x)+1]
                hand = hand.replace(x, range_string(replace_hands))
            elif compare_x in straights:
                replace_hands = str_flush + fulls_or_better + flush_suit + straights[:straights.index(compare_x)+1]
                hand = hand.replace(x, range_string(replace_hands))
            elif compare_x in str_draws:
                replace_hands = str_draws[:str_draws.index(compare_x)+1]
                hand = hand.replace(x, range_string(replace_hands))
            elif compare_x in hand_board_int:
                replace_hands = str_flush + fulls_or_better + flush_suit + straights + hand_board_int[:hand_board_int.index(compare_x)+1]
                hand = hand.replace(x, range_string(replace_hands))
            elif x[1] in hand_board_int:
                replace_hands = hand_board_int[:hand_board_int.index(x[1])]
                better_kickers = kickers[:kickers.index(x[0])+1]
                replace_hands = str_flush + fulls_or_better + flush_suit + straights + replace_hands + [k + x[1] for k in better_kickers]
                hand = hand.replace(x, range_string(replace_hands))

    # One pair or better
    match_expr = re.compile(r'[' + ''.join(RANKS) + r']{1}\+')
    hand_sections = match_expr.findall(hand)
    if hand_sections:
        for x in hand_sections:
            compare_x = x[:-1]
            if compare_x in hand_board_int:
                replace_hands = str_flush + fulls_or_better + flush_suit + straights + hand_board_int[:hand_board_int.index(compare_x)+1]
                hand = hand.replace(x, range_string(replace_hands))

    # Hi-Lo hands like A2< etc.
    match_expr = re.compile(r'[' + ''.join(LOW_CARDS) + r']{2}\<')
    hand_sections = match_expr.findall(hand)
    if hand_sections:
        low_hands = return_lows(ranks)
        for x in hand_sections:
            compare_x = x[:-1]
            if compare_x in low_hands:
                replace_hands = low_hands[:low_hands.index(compare_x)+1]
                hand = hand.replace(x, range_string(replace_hands))

    if '+' in hand:
        logging.error("Could not resolve one or more + expressions in hand:\n{0}".format(hand))
    if '<' in hand:
        logging.error("Could not resolve one or more < expressions in hand:\n{0}".format(hand))

    return hand


def range_string(hand_range):
    """
    takes list of hands and returns string in form of (hand1, hand2, hand3 ...)
    delets useless hands from hand range list ( for example KK if K is also in the range)
    """
    hand_range_compact=[]
    for x in hand_range:
        if not any([r in x for r in hand_range if r!=x]):
            hand_range_compact.append(x)

    hand_string='('
    for x in hand_range_compact:
        hand_string=hand_string+x+', '
    hand_string=hand_string[0:-2] + ')'
    
    return hand_string

def remove_parentheses(range_string):
    start_index=0
    index_touple_list=[]
    
    for char in range_string: # find index of matching parenthesis and save as touple list
        if char != '(':
            start_index+=1
            continue # find first (
        sub_string=range_string[start_index+1:]
        # print(sub_string)
        end_index=start_index+1
        counter=0
        for char_sub in sub_string:
            # print("Index= {0} Counter= {1} Char= {2}".format(end_index,counter,char_sub))
            if char_sub == ')' and counter==0 :
                index_touple_list.append((start_index,end_index))
                break # found closing )
            elif char_sub == '(':
                counter+=1
                end_index+=1
            elif char_sub == ')':
                counter-=1
                end_index+=1
            else:
                end_index+=1
        start_index+=1

    remove_index_list=[] # list of indizes to remove from string
    for touple in index_touple_list:
        if (touple[0] == 0) and (touple[1] == len(range_string)-1): # remove if they are at beginning and end
            remove_index_list.append(touple[0])
            remove_index_list.append(touple[1])
        if (range_string[touple[0]+1] == '(') and (range_string[touple[1]-1] == ')'): # double parenthesis
            if (touple[0]+1,touple[1]-1) in index_touple_list: # check if inner parenthesis are matching -> redundent
                remove_index_list.append(touple[0])
                remove_index_list.append(touple[1])
        if touple[1] - touple[0] == 1: # empty parenthesis
            remove_index_list.append(touple[0])
            remove_index_list.append(touple[1])
        # if touple[0] == 0: # start string
        #     if touple[1] == len(range_string)-1: # remove if they are at beginning and end
        #         remove_index_list.append(touple[0])
        #         remove_index_list.append(touple[1])
        #     elif range_string[touple[1]+1] == ",": # remove if first is on position 0 and second follows, 
        #         remove_index_list.append(touple[0])
        #         remove_index_list.append(touple[1])
                
        # possible to add additional stuff here (remove if there are only , before after etc) FIXME?

#    print(index_touple_list)
    return_string=''
    for index in range(len(range_string)): # deleting parenthesis
        if index not in remove_index_list:
            return_string+=range_string[index]       
    return return_string
    
def test():
    hand_string="$4B2:(Jss+,9K+)"
    board_string="Ks3s3s6h7d"
    sample_board=parse_board(board_string)
    #print(hand_string)
    print(parse_hand(hand_string,board_string))
    print("50%:(((A,4,5):(34,ss)))()")
    print(remove_parentheses("50%:(((A,4,5):(34,ss)))()"))

if __name__ == '__main__':
    import timeit
    if DEBUG:
        test()



# 
# hand.py ends here
