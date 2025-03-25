#!/usr/bin/env python3
# ppt.py ---
#
# Filename: ppt.py
# Description:
# Author: Johann
# Maintainer:
# Created: Die Mar 15 17:44:58 2016 (+0100)
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
#
#
#
#

# Change Log:
#
#
#

# Code:

import logging
import re
import subprocess
import time
import xmlrpc.client

from board import return_next_cards
from hand import parse_hand
from utils import (
    DOTS,
    PPT_GAME,
    PPT_IN_RANGE_TRIAL,
    PPT_LOCATION,
    PPT_MAX_SEC,
    PPT_NEXT_CARD_EQ_TRIAL,
    PPT_NUM_DIGETS,
    PPT_RANK_QUERY_TRIAL,
    PPT_SERVER_PORT,
    PPT_SYNTAX,
    PPT_THREAD_CNT,
    PPT_TRIAL,
    TEST_QUERY,
)


class OddsOracleServer:
    def __init__(self,ppt_location=PPT_LOCATION,ppt_port=PPT_SERVER_PORT, trial=PPT_TRIAL, max_time=PPT_MAX_SEC, thread_cnt=PPT_THREAD_CNT,game=PPT_GAME, syntax=PPT_SYNTAX):
        self.ppt_client = xmlrpc.client.ServerProxy(ppt_port)
        self.ppt_location=ppt_location
        self.trial=trial
        self.max_time=max_time
        self.thread_cnt=thread_cnt
        self.game=game
        self.dead=""
        self.syntax=syntax
        self.board=""

    def start_ppt(self):
        logging.info("Check / Start PPT Server")
        logging.info("Try to Run TEST QUERY")
        try:
            logging.info(self.ppt_client.PPTServer.executePQL(TEST_QUERY, self.trial, self.max_time, self.thread_cnt))
        except Exception as e:
            logging.error("No connection to PPT server... try to open it & wait 2 sec")
            logging.debug("Exception caught while executing first query: %s", e)
            self.ppt_server = subprocess.Popen(
                ['java', '-cp', 'p2.jar', 'propokertools.cli.XMLRPCServer'],
                cwd=self.ppt_location,
                stdout=subprocess.PIPE
            )
            time.sleep(2)
            logging.info("Try executing first sample again")
            logging.info(self.run_query(TEST_QUERY))


    def log_ppt_answer(self,answer):
        if "ERROR" in answer:
            logging.error(answer)
        elif "EQUITY" in answer or "INRANGE" in answer or "NUM_BETTER_HANDS" in answer or "GET5BETPERCENT" in answer or "EV4BET" in answer or "EVCALL4BET" in answer or "RANK" in answer:
            logging.debug(f"PPT answer is: \n {answer}")
        else:
            logging.warning("Unexpected PPT Answer...CHECK Result:\n".format())
        return

    def run_query(self, query):
        trial = self.trial if "5" not in self.game else self.trial // 4  # cut trials with 5card games
        try:
            result = self.ppt_client.PPTServer.executePQL(query, trial, self.max_time, self.thread_cnt)
        except Exception as e:
            logging.error("No Connection to PPT Server")
            logging.debug("Exception in run_query: %s", e)
            return ""
        self.log_ppt_answer(result)
        return result


    def parse_ppt_answer(self, answer, keyword="EQUITY", num_digets=PPT_NUM_DIGETS):
        number = 0.0
        if not answer:
            logging.error("[parse_ppt_answer] Empty answer from PPT")
            return number

        found_keyword = False

        for line in answer.splitlines():
            if keyword in line:
                found_keyword = True
                logging.debug(f"[parse_ppt_answer] Matching line: {line}")
                match = re.search(r'\d+[.,]\d+', line)
                if match is None:
                    logging.error(f"[parse_ppt_answer] No number found in line: {line}")
                    continue
                value = match.group(0).replace(',', '.')  # ← 🔥 conversion ici
                logging.debug(f"[parse_ppt_answer] Extracted value: {value}")
                if value == "0.0":
                    return 0.0
                if value == "1.0":
                    return 1.0
                if len(value) >= num_digets and '.' in value:
                    try:
                        return float(value)
                    except ValueError:
                        logging.error(f"[parse_ppt_answer] Couldn't convert to float: {value}")
                        return number
                else:
                    logging.error(f"[parse_ppt_answer] Value doesn't meet digit/format requirement: {value}")

        if not found_keyword:
            logging.error(f"[parse_ppt_answer] No line with keyword '{keyword}' found in answer:\n{answer}")

        return number



    def equity_query(self, hero_range, villain_range):
        hero_range=self.format_range(hero_range)
        villain_range=self.format_range(villain_range)

        query=("select avg(riverEquity(hero)) as EQUITY \n"
               f"from game='{self.game}', \n"
               f"syntax='{self.syntax}', \n"
               f"hero='{hero_range}', \n"
               f"villain='{villain_range}', \n"
               f"board='{self.board}', \n"
               f"dead='{self.dead}'\n")
        logging.debug("Running an Equity Query with:")
        logging.debug(f"Game: {self.game}, Syntax: {self.syntax}, Board: {self.board}, Dead: {self.dead}")
        logging.debug(f"Hero Range: {hero_range}")
        logging.debug(f"Villain Range: {villain_range}")

        return (self.parse_ppt_answer(self.run_query(query),"EQUITY"))*100

    def equity_query_3way(self, hero_range, villain1_range, villain2_range):
        hero_range=self.format_range(hero_range)
        villain1_range=self.format_range(villain1_range)
        villain2_range=self.format_range(villain2_range)

        query=("select avg(riverEquity(hero)) as EQUITY \n"
               f"from game='{self.game}', \n"
               f"syntax='{self.syntax}', \n"
               f"hero='{hero_range}', \n"
               f"villain1='{villain1_range}', \n"
               f"villain2='{villain2_range}', \n"
               f"board='{self.board}', \n"
               f"dead='{self.dead}'\n")
        logging.debug("Running an Equity Query 3way with:")
        logging.debug(f"Game: {self.game}, Syntax: {self.syntax}, Board: {self.board}, Dead: {self.dead}")
        logging.debug(f"Hero Range: {hero_range}")
        logging.debug(f"Villain1 Range: {villain1_range}")
        logging.debug(f"Villain2 Range: {villain2_range}")

        return (self.parse_ppt_answer(self.run_query(query),"EQUITY"))*100


    def in_range_query(self, hero_range, villain_range, sub_range):
        hero_range=self.format_range(hero_range)
        villain_range=self.format_range(villain_range)
        sub_range=self.format_range(sub_range)

        query=(f"select count(inRange(hero,'{sub_range}')) as INRANGE \n"
               f"from game='{self.game}', \n"
               f"syntax='{self.syntax}', \n"
               f"hero='{hero_range}', \n"
               f"villain='{villain_range}', \n"
               f"board='{self.board}', \n"
               f"dead='{self.dead}'\n")
        logging.debug("Running an InRange/Frequency Query with:")
        logging.debug(f"Game: {self.game}, Syntax: {self.syntax}, Board: {self.board}, Dead: {self.dead}")
        logging.debug(f"Hero Range: {hero_range}")
        logging.debug(f"Hero SubRange: {sub_range}")
        logging.debug(f"Villain Range: {villain_range}")

        trial=self.trial
        self.trial=PPT_IN_RANGE_TRIAL
        answer = self.parse_ppt_answer(self.run_query(query),"INRANGE")
        self.trial=trial
        return answer

    def in_range_query_3way(self, hero_range, villain1_range, villain2_range, sub_range):
        hero_range=self.format_range(hero_range)
        villain1_range=self.format_range(villain1_range)
        villain2_range=self.format_range(villain2_range)
        sub_range=self.format_range(sub_range)

        query=(f"select count(inRange(hero,'{sub_range}')) as INRANGE \n"
               f"from game='{self.game}', \n"
               f"syntax='{self.syntax}', \n"
               f"hero='{hero_range}', \n"
               f"villain1='{villain1_range}', \n"
               f"villain2='{villain2_range}', \n"
               f"board='{self.board}', \n"
               f"dead='{self.dead}'\n")
        logging.debug("Running an InRange/Frequency Query 3 way with:")
        logging.debug(f"Game: {self.game}, Syntax: {self.syntax}, Board: {self.board}, Dead: {self.dead}")
        logging.debug(f"Hero Range: {hero_range}")
        logging.debug(f"Hero SubRange: {sub_range}")
        logging.debug(f"Villain1 Range: {villain1_range}")
        logging.debug(f"Villain2 Range: {villain2_range}")

        trial=self.trial
        self.trial=PPT_IN_RANGE_TRIAL
        answer = self.parse_ppt_answer(self.run_query(query),"INRANGE")
        self.trial=trial
        return answer

    def str2float(self,string):
        try:
            return float(string)
        except ValueError:
            logging.error(f"Could not convert entry to a valid number (Entry Text: {string})")
            return 0.0

    def rank_query(self, equity, hero_range, villain_range, street):
        hero_range=self.format_range(hero_range)
        villain_range=self.format_range(villain_range)

        query=(f"select count(minEquity(hero,{street},{equity/100:.4f})) as NUM_BETTER_HANDS \n"
               f"from game='{self.game}', \n"
               f"syntax='{self.syntax}', \n"
               f"hero='{hero_range}', \n"
               f"villain='{villain_range}', \n"
               f"board='{self.board}', \n"
               f"dead='{self.dead}'\n")

        logging.debug(query + "\n\n")

        logging.debug("Running an Rank Query with:")
        logging.debug(f"Game: {self.game}, Syntax: {self.syntax}, Board: {self.board}, Dead: {self.dead}")
        logging.debug(f"Hero Range: {hero_range}")
        logging.debug(f"Villain Range: {villain_range}")
        logging.debug(f"Calc how often Hero has more than {equity:.1f} equity")

        trial=self.trial
        self.trial=PPT_RANK_QUERY_TRIAL
        answer=self.parse_ppt_answer(self.run_query(query),"NUM_BETTER_HANDS")
        self.trial=trial
        return answer

    def bet_vs_1_calculations(self, result_label_var, hero_range, villain_range, hero_hand, pot_size=0, stack_size=0, bet_size=0, raise_size=0, rraise_size=0, street="flop"): #hero / villain_range are gui_element_objects
        hero_start_range=hero_range.get_start_range()
        # hero_bet_range=hero_range.get_certain_range([0,2]) # hero bets range 1 and 3
        # hero_bluff_range=hero_range.get_certain_range([2]) # hero bluffs range 3
        # hero_value_range=hero_range.get_certain_range([0]) # hero vbets/goes broke? range 1
        # hero_xb_range=hero_range.get_certain_range([1]) # range 2 is middle range

        villain_start_range=villain_range.get_start_range()
        villain_call_range=villain_range.get_certain_range([1])
        villain_raise_range=villain_range.get_certain_range([0,2])
        villain_fold_range=villain_range.get_certain_range([3])
        villain_value_range=villain_range.get_certain_range([0])

        result_str=""
        if not all([pot_size,stack_size,bet_size,raise_size,rraise_size]):
            result_str+="One or more numbers are empty/zero/invalid ->\n"
            result_str+="Please enter valid amouts or leave default values.\n"
            result_label_var.set(result_str)
            return

        if not all([villain_start_range,villain_call_range,villain_raise_range,villain_fold_range,villain_value_range]):
            result_str+="One or more Villain ranges are empty ->\n"
            result_str+="Please enter valid subranges...for fold range (subrange 4) put at least *\n"
            result_label_var.set(result_str)
            return

        if not all([hero_start_range,hero_hand]):
            result_str+="Missing Hero range/hand ->\n"
            result_str+="Please enter at least startrange and example hand for Hero \n"
            result_label_var.set(result_str)
            return

        ## run equity/frequency queries

        logging.info(DOTS)
        logging.info("START EV CALCS")

        hand_eq_vs_range=self.equity_query(hero_hand,villain_start_range)

        hand_eq_vs_raise_range=self.equity_query(hero_hand,villain_raise_range)
        hand_eq_vs_call_range=self.equity_query(hero_hand,villain_call_range)
        hand_eq_vs_fold_range=self.equity_query(hero_hand,villain_fold_range)
        hand_eq_vs_value_raise_range=self.equity_query(hero_hand,villain_value_range)
        hand_ranking=self.rank_query(hand_eq_vs_range,hero_start_range,villain_start_range,street)

        villain_raise_freq=self.in_range_query(villain_start_range,hero_hand,villain_raise_range)
        villain_value_raise_freq=self.in_range_query(villain_start_range,hero_hand,villain_value_range)
        villain_call_freq=self.in_range_query(villain_start_range,hero_hand,villain_call_range)
        villain_fold_freq=self.in_range_query(villain_start_range,hero_hand,villain_fold_range)



        ## convert string variables to float values

        pot_size=self.str2float(pot_size)
        stack_size=self.str2float(stack_size)
        bet_size=self.str2float(bet_size)
        raise_size=self.str2float(raise_size)
        rraise_size=self.str2float(rraise_size)


        result_str+="General Infos:\n"
        result_str+=f"Stacksizes: {stack_size}; Pot: {pot_size} -> SPR = {stack_size/pot_size:.1f}\n"
        result_str+=f"Betsize: {bet_size} ({bet_size/pot_size*100:.1f}% pot); Alpha: {(bet_size/(bet_size+pot_size))*100:.1f}%; 1-Alpha: {(1-bet_size/(bet_size+pot_size))*100:.1f}%\n"
        result_str+=f"Raisesize: {raise_size}; Alpha: {100*raise_size/(raise_size+pot_size+bet_size):.1f}%; 1-Alpha: {100*(1-raise_size/(raise_size+pot_size+bet_size)):.1f}%\n"
        result_str+=f"Reraisesize: {rraise_size}; Alpha: {100*(rraise_size-bet_size)/(rraise_size+pot_size+raise_size):.1f}%; 1-Alpha: {100*(1-(rraise_size-bet_size)/(rraise_size+pot_size+raise_size)):.1f}%\n"
        result_str+=f"Stackoff Equity: {stack_size/(pot_size+2*stack_size)*100:.1f}% ({(stack_size-bet_size)/(pot_size+2*stack_size)*100:.1f}% after bet; {(stack_size-raise_size)/(pot_size+2*stack_size)*100:.1f}% after raise; {(stack_size-rraise_size)/(pot_size+2*stack_size)*100:.1f}% after reraise).\n"


        result_str+="\nEquities and Frequencies:\n"
        result_str+=f"Hero startrange equity: {hero_range.range_eq.get()}% vs villain startrange\n"
        result_str+=f"{hero_hand} equity: {hand_eq_vs_range:.1f}% ({hand_ranking:.1f}% of hero startrange has more equity)\n"
        try:
            villain_r_f_freq=1-villain_value_raise_freq/villain_raise_freq
            result_str+=f"Villain raises: {villain_raise_freq:.1f}%; calls: {villain_call_freq:.1f}%; folds: {villain_fold_freq:.1f}%; folds vs reraise: {villain_r_f_freq*100:.1f}%\n"
        except ZeroDivisionError:
            logging.error("Some Frequencies are off...Division by zero error")
            return
        result_str+=f"{hero_hand} equity vs raise {hand_eq_vs_raise_range:.1f}% ({hand_eq_vs_value_raise_range:.1f}% vs value); {hand_eq_vs_call_range:.1f}% vs call; {hand_eq_vs_fold_range:.1f}% vs fold-range\n"

        result_str+="\nEV for low SPR situations (asume equity realisation 100%):\n"
        result_str+="Ev BF = {:.2f}\n".format(villain_fold_freq/100*pot_size + villain_raise_freq/100*(-bet_size) +
                                          villain_call_freq/100*(hand_eq_vs_call_range/100*(pot_size+2*bet_size) - bet_size))
        result_str+="Ev BC = {:.2f}\n".format(villain_fold_freq/100*pot_size + villain_raise_freq/100*(hand_eq_vs_raise_range/100*(2*raise_size+pot_size) - raise_size) +
                                          villain_call_freq/100*(hand_eq_vs_call_range/100*(pot_size+2*bet_size) - bet_size))
        result_str+=f"Ev XB = {hand_eq_vs_range*pot_size/100:.2f}\n"

        result_str+="\nEV for high SPR situations (EV as expression of realisation factors R_vs_range, R_vs_call, R_vs_raise):\n"

        result_str+=f"Ev BF = {villain_fold_freq/100*pot_size-villain_raise_freq/100*bet_size-villain_call_freq/100*bet_size:.2f}"
        result_str+=f" + {villain_call_freq/100*hand_eq_vs_call_range/100*(pot_size+2*bet_size):.2f}*R_vs_call\n"

        result_str+=f"Ev BC = {villain_fold_freq/100*pot_size-villain_raise_freq/100*raise_size-villain_call_freq/100*bet_size:.2f}"
        result_str+=f" + {villain_raise_freq/100*hand_eq_vs_raise_range/100*(2*raise_size+pot_size):.2f}*R_vs_raise"
        result_str+=f" + {villain_call_freq/100*hand_eq_vs_call_range/100*(pot_size+2*bet_size):.2f}*R_vs_call\n"
        result_str+=f"Ev XB = {hand_eq_vs_range*pot_size/100:.2f} * R_vs_range \n"
        result_str+=f"Ev BF = EV XB if R_vs_range = {(villain_fold_freq/100*pot_size-villain_raise_freq/100*bet_size-villain_call_freq/100*bet_size)/(hand_eq_vs_range*pot_size/100):.2f} + {(villain_call_freq/100*hand_eq_vs_call_range/100*(pot_size+2*bet_size))/(hand_eq_vs_range*pot_size/100):.2f}*R_vs_call\n"


        result_str+="\nDefend vs Raise:\n"
        result_str+=f"Reraise Bluff no Equity: Villain folds {villain_r_f_freq*100:.1f}% ({100*(rraise_size-bet_size)/(rraise_size+pot_size+raise_size):.1f}% needed)\n"
        result_str+=f"Semibluff reraise needs {100*(-villain_r_f_freq*(pot_size+bet_size+raise_size) + (1-villain_r_f_freq)*(rraise_size-bet_size))/((1-villain_r_f_freq)*(pot_size+2*rraise_size)):.1f}% equity\n"

        result_label_var.set(result_str)
        logging.info("DOONNEEE!!")
        logging.info(DOTS)
        return


    def bet_vs_2_calculations(self, result_label_var, hero_range, villain1_range, villain2_range, hero_hand, pot_size=0, stack_size1=0, stack_size2=0, bet_size=0, raise_size=0, rraise_size=0, street="flop"): #hero / villain_range are gui_element_objects

        hero_start_range=hero_range.get_start_range()
        # hero_bet_range=hero_range.get_certain_range([0,2]) # hero bets range 1 and 3
        # hero_bluff_range=hero_range.get_certain_range([2]) # hero bluffs range 3
        # hero_value_range=hero_range.get_certain_range([0]) # hero vbets/goes broke? range 1
        # hero_xb_range=hero_range.get_certain_range([1]) # range 2 is middle range

        villain1_start_range=villain1_range.get_start_range()
        villain1_call_range=villain1_range.get_certain_range([1])
        villain1_raise_range=villain1_range.get_certain_range([0,2])
        villain1_fold_range=villain1_range.get_certain_range([3])
        villain1_value_range=villain1_range.get_certain_range([0])

        villain2_start_range=villain2_range.get_start_range()
        villain2_call_range=villain2_range.get_certain_range([1])
        villain2_raise_range=villain2_range.get_certain_range([0,2])
        villain2_fold_range=villain2_range.get_certain_range([3])
        villain2_value_range=villain2_range.get_certain_range([0])

        villain1_raise_range_low_spr=villain1_range.get_certain_range([0,1])
        villain2_raise_range_low_spr=villain2_range.get_certain_range([0,1])
        villain1_fold_range_low_spr=villain1_range.get_certain_range([2,3])
        villain2_fold_range_low_spr=villain2_range.get_certain_range([2,3])

        result_str=""
        if not all([pot_size,stack_size1,stack_size2,bet_size,raise_size,rraise_size]):
            result_str+="One or more numbers are empty/zero/invalid ->\n"
            result_str+="Please enter valid amouts or leave default values.\n"
            result_label_var.set(result_str)
            return

        if not all([villain1_start_range,villain1_call_range,villain1_raise_range,villain1_fold_range,villain1_value_range]):
            result_str+="One or more Villain1 ranges are empty ->\n"
            result_str+="Please enter valid subranges...for fold range (subrange 4) put at least *\n"
            result_label_var.set(result_str)
            return

        if not all([villain2_start_range,villain2_call_range,villain2_raise_range,villain2_fold_range,villain2_value_range]):
            result_str+="One or more Villain2 ranges are empty ->\n"
            result_str+="Please enter valid subranges...for fold range (subrange 4) put at least *\n"
            result_label_var.set(result_str)
            return

        if not all([hero_start_range,hero_hand]):
            result_str+="Missing Hero range/hand ->\n"
            result_str+="Please enter at least startrange and example hand for Hero \n"
            result_label_var.set(result_str)
            return

        ## run equity/frequency queries
        logging.info(DOTS)
        logging.info("START EV CALCS")

        hand_eq_vs_ranges=self.equity_query_3way(hero_hand,villain1_start_range,villain2_start_range)

        # results for low spr situations:
        hand_eq_vs_ship1_range=self.equity_query(hero_hand,villain1_raise_range_low_spr)
        hand_eq_vs_ship2_range=self.equity_query(hero_hand,villain2_raise_range_low_spr)
        hand_eq_vs_ship12_range=self.equity_query_3way(hero_hand,villain1_raise_range_low_spr,villain2_value_range)

        villain1_ship_freq=self.in_range_query_3way(villain1_start_range,hero_hand,villain2_fold_range_low_spr,villain1_raise_range_low_spr)
        villain2_ship_freq=self.in_range_query_3way(villain2_start_range,hero_hand,villain1_fold_range_low_spr,villain2_raise_range_low_spr)
        villain2_overship_freq=self.in_range_query_3way(villain2_start_range,hero_hand,villain1_raise_range_low_spr,villain2_value_range)

        # general frequencies (raise range 1+3, call range 2):

        hand_eq_vs_v1_1=self.equity_query(hero_hand,villain1_value_range)
        hand_eq_vs_v2_1=self.equity_query(hero_hand,villain2_value_range)
        hand_eq_vs_v12_1=self.equity_query_3way(hero_hand,villain1_value_range,villain2_value_range)


        villain1_raise_freq=self.in_range_query_3way(villain1_start_range,hero_hand,villain2_start_range,villain1_raise_range)
        villain2_raise_freq=self.in_range_query_3way(villain2_start_range,hero_hand,villain2_fold_range,villain2_raise_range)
        villain1_calls_freq=self.in_range_query_3way(villain1_start_range,hero_hand,villain2_start_range,villain1_call_range)
        villain2_calls_freq=self.in_range_query_3way(villain2_start_range,hero_hand,villain1_fold_range,villain2_call_range)
        villain1_folds_freq=self.in_range_query_3way(villain1_start_range,hero_hand,villain2_start_range,villain1_fold_range)
        villain2_folds_freq=self.in_range_query_3way(villain2_start_range,hero_hand,villain1_fold_range,villain2_fold_range)

        hand_eq_vs_v1_2=self.equity_query(hero_hand,villain1_call_range)
        hand_eq_vs_v2_2=self.equity_query(hero_hand,villain2_call_range)
        hand_eq_vs_v12_2=self.equity_query_3way(hero_hand,villain1_call_range,villain2_call_range)

        ## convert string variables to float values

        pot_size=self.str2float(pot_size)
        stack_size1=self.str2float(stack_size1)
        stack_size2=self.str2float(stack_size2)
        bet_size=self.str2float(bet_size)
        raise_size=self.str2float(raise_size)
        rraise_size=self.str2float(rraise_size)

        result_str+=f"Stacksize vs V1: {stack_size1}; vs V2: {stack_size2} Pot: {pot_size}\n"
        if stack_size1-stack_size2 > 0:
            sidepot=(stack_size1-stack_size2)*2
            sideplayer=1
        else:
            sidepot=(stack_size2-stack_size1)*2
            sideplayer=2
        result_str+=f"Potentional sidepot with V{sideplayer} is {sidepot}\n"
        result_str+=f"Betsize: {bet_size} ({bet_size/pot_size*100:.1f}% pot); Alpha: {(bet_size/(bet_size+pot_size))*100:.1f}%; 1-Alpha: {(1-bet_size/(bet_size+pot_size))*100:.1f}%\n"
        result_str+=f"Raisesize: {raise_size}; Alpha: {100*raise_size/(raise_size+pot_size+bet_size):.1f}%; 1-Alpha: {100*(1-raise_size/(raise_size+pot_size+bet_size)):.1f}%\n"
        result_str+=f"Stackoff Equity vs V1: {stack_size1/(pot_size+2*stack_size1)*100:.1f}% , vs V2: {stack_size2/(pot_size+2*stack_size2)*100:.1f}%, vs V12 (only main pot): {min(stack_size1,stack_size2)/(pot_size+3*min(stack_size1,stack_size2))*100:.1f}%.\n"

        result_str+=f"Stackoff Equity after bet vs V1: {(stack_size1-bet_size)/(pot_size+2*stack_size1)*100:.1f}% , vs V2: {(stack_size2-bet_size)/(pot_size+2*stack_size2)*100:.1f}%, vs V12 (only main pot): {(min(stack_size1,stack_size2)-bet_size)/(pot_size+3*min(stack_size1,stack_size2))*100:.1f}%.\n"

        result_str+=f"\nHero startrange equity: {hero_range.range_eq.get()}% vs V1 and V2 startrange\n"
        result_str+=f"{hero_hand} equity: {hand_eq_vs_ranges:.1f}% \n"
        result_str+=f"Hand equity vs V1 range 1: {hand_eq_vs_v1_1:.1f}%; V2 range 1: {hand_eq_vs_v2_1:.1f}%; V12 range 1: {hand_eq_vs_v12_1:.1f}%\n"
        result_str+=f"Cbet gets raised (V1 raises range 1+3, calls 2; V2 raises 1+3 when V1 folds 4)~: {villain1_raise_freq + (1-villain1_raise_freq/100)*villain2_raise_freq:.1f}\n"
        result_str+=f"Both fold: {(villain1_folds_freq/100)*(villain2_folds_freq/100)*100:.1f}; "
        result_str+=f"bet get called ~:{villain1_calls_freq+(1-villain1_calls_freq/100)*villain2_calls_freq:.1f} \n"
        result_str+=f"Equity vs call V1: {hand_eq_vs_v1_2:.1f}%; vs call V2: {hand_eq_vs_v2_2:.1f}%; vs call both: {hand_eq_vs_v12_2:.1f}%\n"

        v1_ship_v2_fold=(villain1_ship_freq/100)*(1-villain2_overship_freq/100)
        v1_fold_v2_ship=(1-villain1_ship_freq/100)*(villain2_ship_freq/100)
        v1_fold_v2_fold=(1-villain1_ship_freq/100)*(1-villain2_ship_freq/100)
        v1_ship_v2_ship=(villain1_ship_freq/100)*(villain2_overship_freq/100)

        result_str+="\nLow SPR spot (3bet pot...only bet/ship left):\n"
        result_str+=f"V1 ships range 1 + 2 and V2 folds: {v1_ship_v2_fold*100:.1f}%\n"
        result_str+=f"V2 folds and V2 ships range 1 + 2: {v1_fold_v2_ship*100:.1f}%\n"
        result_str+=f"V1 folds and V2 folds 3 + 4: {v1_fold_v2_fold*100:.1f}%\n"
        result_str+=f"V1 ships range 1 + 2 and V2 ships range 1: {v1_ship_v2_ship*100:.1f}%\n"

        ev_both_fold=v1_fold_v2_fold*pot_size
        ev_v1_ship_v2_fold=v1_ship_v2_fold*(hand_eq_vs_ship1_range/100*(pot_size+stack_size1*2)-stack_size1)
        ev_v1_fold_v2_ships=v1_fold_v2_ship*(hand_eq_vs_ship2_range/100*(pot_size+stack_size2*2)-stack_size2)
        if sideplayer == 1:
            ev_v1_ship_v2_ships=v1_ship_v2_ship*(hand_eq_vs_ship12_range/100*(pot_size+stack_size2*3)-stack_size2+
                                                 hand_eq_vs_ship1_range/100*(sidepot)-sidepot/2)
        else:
            ev_v1_ship_v2_ships=v1_ship_v2_ship*(hand_eq_vs_ship12_range/100*(pot_size+stack_size1*3)-stack_size1+
                                                 hand_eq_vs_ship2_range/100*(sidepot)-sidepot/2)

        result_str+=f"Equity vs V1: {hand_eq_vs_ship1_range:.1f}%; vs V2: {hand_eq_vs_ship2_range:.1f}%; 3way: {hand_eq_vs_ship12_range:.1f}%\n"
        result_str+=f"Relative EVs of bet/call...Both fold: {ev_both_fold:.2f}; vs V1: {ev_v1_ship_v2_fold:.2f}; vs V2: {ev_v1_fold_v2_ships:.2f}; vs V12: {ev_v1_ship_v2_ships:.2f}; OVERALL:{ev_both_fold+ev_v1_ship_v2_fold+ev_v1_fold_v2_ships+ev_v1_ship_v2_ships:.2f}\n"


        result_label_var.set(result_str)
        logging.info("DOONNEEE!!")
        logging.info(DOTS)
        return



    def do_4bet(self,result_str,hand,villain_3brange,villain_5brange,stack_size,open_size,bet3_size,pot_size):
        logging.info(DOTS)
        logging.info("4BET CALC")
        logging.info(f"4-bet {hand} vs V1 range: {villain_3brange}")
        stack_size=self.str2float(stack_size)
        open_size=self.str2float(open_size)
        bet3_size=self.str2float(bet3_size)
        pot_size=self.str2float(pot_size)

        pot_call_3bet=pot_size+bet3_size-open_size
        pot_flop=pot_call_3bet*3
        invest_pre=bet3_size-open_size+pot_call_3bet
        invest_post=stack_size-pot_call_3bet-bet3_size

        logging.info(f"We invest {invest_pre} pre (total 4bet size: {invest_pre+open_size}) wiht pot otf: {pot_flop} and stacks left: {invest_post}")

        query = (
            f"select count(inRange(villain, '{villain_5brange}')) as GET5BETPERCENT,\n"
            "avg(riverEquity(hero)) as EQUITY,"
            "avg( \n"
            "case \n"
            f"when inRange(villain, '{villain_5brange}')\n"
            f"then riverEquity(hero)*{pot_flop + invest_post * 2} - {invest_pre + invest_post} \n"
            "else\n"
            "case\n"
            f"when minEquity(villain,flop,{invest_post / (pot_flop + 2 * invest_post):.4f})\n"
            f"then {pot_flop + invest_post * 2}*riverEquity(hero) - {invest_pre + invest_post}\n"
            f"else {pot_flop}\n"
            "end\n"
            "end\n"
            ") as EV4BET\n"
            f"from game='{self.game}',\n"
            f"syntax='{self.syntax}',\n"
            f"hero='{hand}',\n"
            f"villain='{villain_3brange}'"
        )

        logging.info("Run the following 4bet query:\n" + query)
        logging.info("\n")
        logging.info(self.run_query(query))
        return


    def call_4bet(self,result_str,hand,villain_4brange,stack_size,open_size,bet3_size,pot_size):
        logging.info(DOTS)
        logging.info("CALL 4BET CALC")
        logging.info(f"Call 4-bet {hand} vs V1 range: {villain_4brange}")
        stack_size=self.str2float(stack_size)
        open_size=self.str2float(open_size)
        bet3_size=self.str2float(bet3_size)
        pot_size=self.str2float(pot_size)

        pot_call_3bet=pot_size+bet3_size-open_size
        pot_flop=pot_call_3bet*3
        invest_pre=pot_call_3bet
        invest_post=stack_size-pot_call_3bet-bet3_size

        logging.info(f"We invest {invest_pre:.2f} pre (total 4bet size: {invest_pre+bet3_size:.2f}) wiht pot otf: {pot_flop:.2f} and stacks left: {invest_post:.2f}")

        query=("select avg(riverEquity(hero)) as EQUITY,\n"
               "avg( \n"
               "case\n"
               f"when minEquity(hero,flop,{invest_post/(invest_post*2+pot_flop):.4f})\n"
                f"then {pot_flop+2*invest_post}*riverEquity(hero) - {invest_pre+invest_post}\n"
                 f"else {-invest_pre}\n"
               "end) as EVCALL4BET\n"
               f"from game='{self.game}',\n"
               f"syntax='{self.syntax}',\n"
               f"hero='{hand}',\n"
               f"villain='{villain_4brange}'")
        logging.info("Run the following call 4bet query:\n" + query)
        logging.info("\n")
        logging.info(self.run_query(query))
        return

    def next_card_eval(self, hero_range, villain_range):
        next_cards=return_next_cards(self.board,False)
        board_original=self.board
        result=[]
        overall_equity=self.equity_query(hero_range,villain_range)
        logging.info(DOTS)
        logging.info(f"Hero Range: {hero_range}")
        logging.info(f"Villain Range: {villain_range}")
        logging.info(f"For board {self.board}, Hero equity is {overall_equity:.2f}% \n")
        result.append((self.board,overall_equity,0.0))
        self.trial=PPT_NEXT_CARD_EQ_TRIAL
        for card in next_cards:
            self.board+=card
            equity=self.equity_query(hero_range,villain_range)
            logging.info(f"For board {self.board}, Hero equity is {equity:.2f}% (Difference: {equity-overall_equity:.2f}%)")
            result.append((self.board,equity,equity-overall_equity))
            self.board=board_original
        logging.info("\n")
        logging.info("Sorted results for next Card:")
        result.sort(key=lambda x:x[1],reverse=True)
        for x in result:
            logging.info(f"For board {x[0]}, Hero equity is {x[1]:.2f}% (Difference: {x[2]:.2f}%)")
        logging.info("DONE")
        logging.info(DOTS)
        self.trial=PPT_TRIAL
        return

    def format_range(self,hand_range):
        return parse_hand(hand_range,self.board)

    def table_item(self,string,size):
        if len(string)>size:
            return string
        spaces=size-len(string)
        spaces_before=spaces//2
        return(spaces_before*" "+string+(spaces-spaces_before)*" ")

    def rank_hand_query(self,hand,num_plr):
        query=(f"select avg(handRankingFor(hero,'{num_plr}')) as RANK \n"
               f"from game='{self.game}',\n"
               f"syntax='{self.syntax}',\n"
               f"hero='{hand}',\n"
               f"dead='{self.dead}'\n")
        trial=self.trial
        self.trial=PPT_RANK_QUERY_TRIAL
        answer=self.run_query(query)
        answer=self.parse_ppt_answer(answer,"RANK")
        self.trial=trial
        return answer

    def rank_hand(self,hand):
        horizontal_line=80*"-"
        width=8

        logging.info(horizontal_line)
        logging.info("Rankings:")
        logging.info("|"+self.table_item("VR",width)+"|"+self.table_item("3H",width)+"|"+self.table_item("6H",width)+"|"+self.table_item("10H",width)+"|")
        rank_vr=self.table_item(str(round(self.rank_hand_query(hand,"vr"),1)),width)
        rank_3h=self.table_item(str(round(self.rank_hand_query(hand,"3h"),1)),width) if "5" not in self.game else  self.table_item("--",width)
        rank_6h=self.table_item(str(round(self.rank_hand_query(hand,"6h"),1)),width)
        rank_10h=self.table_item(str(round(self.rank_hand_query(hand,"10h"),1)),width) if "5" not in self.game else self.table_item(str(round(self.rank_hand_query(hand,"9h"),1)),width)
        logging.info("|"+rank_vr+"|"+rank_3h+"|"+rank_6h+"|"+rank_10h+"|\n")

        logging.info("vs PPT 6h Ranking HU:")
        logging.info("|"+self.table_item("2%",width)+"|"+self.table_item("4%",width)+"|"+self.table_item("6%",width)+"|"+self.table_item("10%",width)+"|"
                     +self.table_item("15%",width)+"|"+self.table_item("20%",width)+"|"+self.table_item("25%",width)+"|"+self.table_item("30%",width)+"|"
                     +self.table_item("40%",width)+"|"+self.table_item("50%",width)+"|"+self.table_item("75%",width)+"|"+self.table_item("100%",width)+"|")

        vs_2=self.table_item(str(round(self.equity_query(hand,"2%6h"),1)),width)
        vs_4=self.table_item(str(round(self.equity_query(hand,"4%6h"),1)),width)
        vs_6=self.table_item(str(round(self.equity_query(hand,"6%6h"),1)),width)
        vs_10=self.table_item(str(round(self.equity_query(hand,"10%6h"),1)),width)
        vs_15=self.table_item(str(round(self.equity_query(hand,"15%6h"),1)),width)
        vs_20=self.table_item(str(round(self.equity_query(hand,"20%6h"),1)),width)
        vs_25=self.table_item(str(round(self.equity_query(hand,"25%6h"),1)),width)
        vs_30=self.table_item(str(round(self.equity_query(hand,"30%6h"),1)),width)
        vs_40=self.table_item(str(round(self.equity_query(hand,"40%6h"),1)),width)
        vs_50=self.table_item(str(round(self.equity_query(hand,"50%6h"),1)),width)
        vs_75=self.table_item(str(round(self.equity_query(hand,"75%6h"),1)),width)
        vs_100=self.table_item(str(round(self.equity_query(hand,"100%6h"),1)),width)

        logging.info("|"+vs_2+"|"+vs_4+"|"+vs_6+"|"+vs_10+"|"+vs_15+"|"+vs_20+"|"+vs_25+"|"+vs_30+"|"+vs_40+"|"+vs_50+"|"+vs_75+"|"+vs_100+"|\n")
        logging.info("vs PPT 6h Ranking 3WAY:")
        logging.info("|"+self.table_item("15%",width)+"|"+self.table_item("15%",width)+"|"+self.table_item("15%",width)+"|"+self.table_item("25%",width)+"|"
                     +self.table_item("25%",width)+"|"+self.table_item("25%",width)+"|"+self.table_item("35%",width)+"|"+self.table_item("35%",width)+"|"
                     +self.table_item("35%",width)+"|"+self.table_item("50%",width)+"|"+self.table_item("50%",width)+"|"+self.table_item("50%",width)+"|")
        logging.info("|"+self.table_item("4%",width)+"|"+self.table_item("30%!4%",width)+"|"+self.table_item("30%",width)+"|"+self.table_item("6%",width)+"|"
                     +self.table_item("40%",width)+"|"+self.table_item("40%!6%",width)+"|"+self.table_item("8%",width)+"|"+self.table_item("50%",width)+"|"
                     +self.table_item("50%!8%",width)+"|"+self.table_item("12%",width)+"|"+self.table_item("60%",width)+"|"+self.table_item("60%!%12",width)+"|")

        vs_15_4=self.table_item(str(round(self.equity_query_3way(hand,"15%6h","4%6h"),1)),width)
        vs_15_30=self.table_item(str(round(self.equity_query_3way(hand,"15%6h","30%6h"),1)),width)
        vs_15_30n4=self.table_item(str(round(self.equity_query_3way(hand,"15%6h","30%6h!4%6h"),1)),width)
        vs_25_6=self.table_item(str(round(self.equity_query_3way(hand,"25%6h","6%6h"),1)),width)
        vs_25_40=self.table_item(str(round(self.equity_query_3way(hand,"25%6h","40%6h"),1)),width)
        vs_25_40n6=self.table_item(str(round(self.equity_query_3way(hand,"25%6h","40%6h!6%6h"),1)),width)
        vs_35_8=self.table_item(str(round(self.equity_query_3way(hand,"35%6h","8%6h"),1)),width)
        vs_35_50=self.table_item(str(round(self.equity_query_3way(hand,"35%6h","50%6h"),1)),width)
        vs_35_50n8=self.table_item(str(round(self.equity_query_3way(hand,"35%6h","50%6h!8%6h"),1)),width)
        vs_50_12=self.table_item(str(round(self.equity_query_3way(hand,"50%6h","12%6h"),1)),width)
        vs_50_60=self.table_item(str(round(self.equity_query_3way(hand,"50%6h","60%6h"),1)),width)
        vs_50_60n12=self.table_item(str(round(self.equity_query_3way(hand,"50%6h","60%6h!12%6h"),1)),width)


        logging.info("|"+vs_15_4+"|"+vs_15_30+"|"+vs_15_30n4+"|"+vs_25_6+"|"+vs_25_40+"|"+vs_25_40n6+"|"+vs_35_8+"|"+vs_35_50+"|"+vs_35_50n8+"|"+vs_50_12+"|"+vs_50_60+"|"+vs_50_60n12+"|\n")

        width=15
        if self.game=="omahahi":
            logging.info("some equities for omahahi common situations")
            logging.info("MP:")
            logging.info("|"+self.table_item("$3b4o%",width)+"|"+self.table_item("$3b6i%",width)+"|"+self.table_item("$FI20!$3b6i",width)+"|"+self.table_item("$FI30!3b4o",width)+"|"
                     +self.table_item("$FI40!3b4o",width)+"|"+self.table_item("$FI20!$3b6i",width)+"|"+self.table_item("$FI30!$3b6i",width)+"|")
            logging.info("|"+self.table_item("",width)+"|"+self.table_item("",width)+"|"+self.table_item("",width)+"|"+self.table_item("",width)+"|"
                     +self.table_item("",width)+"|"+self.table_item("$FI40!$3b4o",width)+"|"+self.table_item("$FI50!$3b4o",width)+"|")

            vs_3b4=self.table_item(str(round(self.equity_query(hand,"$3b4o"),1)),width)
            vs_3b6=self.table_item(str(round(self.equity_query(hand,"$3b6i"),1)),width)
            vs_fi20n6=self.table_item(str(round(self.equity_query(hand,"$FI20!$3b6i"),1)),width)
            vs_fi30n4=self.table_item(str(round(self.equity_query(hand,"$FI30!$3b4o"),1)),width)
            vs_fi40n4=self.table_item(str(round(self.equity_query(hand,"$FI40!$3b4o"),1)),width)
            vs_fi20n6fi40n4=self.table_item(str(round(self.equity_query_3way(hand,"$FI20!$3b6i","$FI40!$3b4o"),1)),width)
            vs_fi30n6fi50n4=self.table_item(str(round(self.equity_query_3way(hand,"$FI30!$3b6i","$FI50!$3b4o"),1)),width)

            logging.info("|"+vs_3b4+"|"+vs_3b6+"|"+vs_fi20n6+"|"+vs_fi30n4+"|"+vs_fi40n4+"|"+vs_fi20n6fi40n4+"|"+vs_fi30n6fi50n4+"|\n")

            logging.info("CO:")
            logging.info("|"+self.table_item("$FI15",width)+"|"+self.table_item("$3b6o",width)+"|"+self.table_item("$3b8i",width)+"|"+self.table_item("$FI25!$3b8i",width)+"|"+self.table_item("$FI50!3b6o",width)+"|"
                     +self.table_item("60!3b6o",width)+"|"+self.table_item("$FI25!$3b8i",width)+"|"+self.table_item("$FI25!$3b8i",width)+"|")
            logging.info("|"+self.table_item("",width)+"|"+self.table_item("",width)+"|"+self.table_item("",width)+"|"+self.table_item("",width)+"|"+self.table_item("",width)+"|"
                     +self.table_item("",width)+"|"+self.table_item("$FI50!$3b6o",width)+"|"+self.table_item("$FI60!$3b6o",width)+"|")

            vs_fi15=self.table_item(str(round(self.equity_query(hand,"$FI15"),1)),width)
            vs_3b6=self.table_item(str(round(self.equity_query(hand,"$3b6o"),1)),width)
            vs_3b8=self.table_item(str(round(self.equity_query(hand,"$3b8i"),1)),width)
            vs_fi25n8=self.table_item(str(round(self.equity_query(hand,"$FI25!$3b8i"),1)),width)
            vs_fi50n6=self.table_item(str(round(self.equity_query(hand,"$FI50!$3b6o"),1)),width)
            vs_60n6=self.table_item(str(round(self.equity_query(hand,"60%6h!$3b6o"),1)),width)
            vs_fi25n8fi50n6=self.table_item(str(round(self.equity_query_3way(hand,"$FI25!$3b8i","$FI50!$3b6o"),1)),width)
            vs_fi25n860n6=self.table_item(str(round(self.equity_query_3way(hand,"$FI25!$3b8i","60%6h!$3b6o"),1)),width)

            logging.info("|"+vs_fi15+"|"+vs_3b6+"|"+vs_3b8+"|"+vs_fi25n8+"|"+vs_fi50n6+"|"+vs_60n6+"|"+vs_fi25n8fi50n6+"|"+vs_fi25n860n6+"|\n")


            logging.info("BU:")

            logging.info("|"+self.table_item("$FI25",width)+"|"+self.table_item("$3b8o",width)+"|"+self.table_item("$3b10o",width)+"|"+self.table_item("$3b15o",width)+"|"+self.table_item("$FI50!3b8o",width)+"|"
                     +self.table_item("60%!3b10o",width)+"|"+self.table_item("$FI25!$3b10o",width)+"|"+self.table_item("$FI25!$3b10o",width)+"|")
            logging.info("|"+self.table_item("",width)+"|"+self.table_item("",width)+"|"+self.table_item("",width)+"|"+self.table_item("",width)+"|"+self.table_item("",width)+"|"
                     +self.table_item("",width)+"|"+self.table_item("60%!$3b8o",width)+"|"+self.table_item("$3b10o",width)+"|")

            vs_fi25=self.table_item(str(round(self.equity_query(hand,"$FI25"),1)),width)
            vs_3b8=self.table_item(str(round(self.equity_query(hand,"$3b8o"),1)),width)
            vs_3b10=self.table_item(str(round(self.equity_query(hand,"$3b10o"),1)),width)
            vs_3b15=self.table_item(str(round(self.equity_query(hand,"$3b15o"),1)),width)
            vs_fi50n8=self.table_item(str(round(self.equity_query(hand,"$FI50!$3b8o"),1)),width)
            vs_60n10=self.table_item(str(round(self.equity_query(hand,"60%6h!$3b10o"),1)),width)
            vs_fi25n10fi60n8=self.table_item(str(round(self.equity_query_3way(hand,"$FI25!$3b10o","60%!3b8o"),1)),width)
            vs_fi25n103b10=self.table_item(str(round(self.equity_query_3way(hand,"$FI25!$3b10o","$3b10o"),1)),width)

            logging.info("|"+vs_fi25+"|"+vs_3b8+"|"+vs_3b10+"|"+vs_3b15+"|"+vs_fi50n8+"|"+vs_60n10+"|"+vs_fi25n10fi60n8+"|"+vs_fi25n103b10+"|\n")

            logging.info("SB:")

            logging.info("|"+self.table_item("$FI40",width)+"|"+self.table_item("$FI50",width)+"|"+self.table_item("65%",width)+"|"+self.table_item("$3b15i",width)+"|"+self.table_item("$4b3",width)+"|"
                     +self.table_item("$FI50",width)+"|"+self.table_item("$FI50!AA",width)+"|"+self.table_item("$FI50!$4b4",width)+"|")
            logging.info("|"+self.table_item("",width)+"|"+self.table_item("",width)+"|"+self.table_item("",width)+"|"+self.table_item("",width)+"|"+self.table_item("",width)+"|"
                     +self.table_item("60%!$3b10o",width)+"|"+self.table_item("$3b10o",width)+"|"+self.table_item("$3b15o",width)+"|")

            vs_fi40=self.table_item(str(round(self.equity_query(hand,"$FI40"),1)),width)
            vs_fi50=self.table_item(str(round(self.equity_query(hand,"$FI50"),1)),width)
            vs_65=self.table_item(str(round(self.equity_query(hand,"65%"),1)),width)
            vs_3b15=self.table_item(str(round(self.equity_query(hand,"$3b15o"),1)),width)
            vs_4b3=self.table_item(str(round(self.equity_query(hand,"$4b3"),1)),width)
            vs_5060n10=self.table_item(str(round(self.equity_query_3way(hand,"$FI50","60%6h!$3b10o"),1)),width)
            vs_50nAA3b10=self.table_item(str(round(self.equity_query_3way(hand,"$FI50!AA","$3b10o"),1)),width)
            vs_50n4b43b15=self.table_item(str(round(self.equity_query_3way(hand,"$FI50!$4b4","$3b15o"),1)),width)

            logging.info("|"+vs_fi40+"|"+vs_fi50+"|"+vs_65+"|"+vs_3b15+"|"+vs_4b3+"|"+vs_5060n10+"|"+vs_50nAA3b10+"|"+vs_50n4b43b15+"|\n")

            logging.info("BB:")

            logging.info("|"+self.table_item("70%",width)+"|"+self.table_item("$FI50",width)+"|"+self.table_item("$FI50",width)+"|"+self.table_item("$FI50",width)+"|"+self.table_item("$FI50",width)+"|")
            logging.info("|"+self.table_item("",width)+"|"+self.table_item("$FI25!$3b10o",width)+"|"+self.table_item("$FI35!$3b15o",width)+"|"+self.table_item("$3b10o",width)+"|"+self.table_item("$3b15o",width)+"|")

            vs_70=self.table_item(str(round(self.equity_query(hand,"70%6h"),1)),width)
            vs_fi50fi25n3b10=self.table_item(str(round(self.equity_query_3way(hand,"$FI50","$FI25!$3b10o"),1)),width)
            vs_fi50fi35n3b15=self.table_item(str(round(self.equity_query_3way(hand,"$FI50","$FI25!$3b15o"),1)),width)
            vs_fi503b10=self.table_item(str(round(self.equity_query_3way(hand,"$FI50","$3b10o"),1)),width)
            vs_fi503b15=self.table_item(str(round(self.equity_query_3way(hand,"$FI50","$3b15o"),1)),width)

            logging.info("|"+vs_70+"|"+vs_fi50fi25n3b10+"|"+vs_fi50fi35n3b15+"|"+vs_fi503b10+"|"+vs_fi503b15+"|\n")
        logging.info(horizontal_line)
        return


#
# ppt.py ends here
