#! /usr/bin/env python3

import argparse
from sushi_state import get_shuffled_cards, HAND_SIZES, SushiCardType, GameState, score_round, score_pudding
from typing import List, Optional, Callable, Dict
import subprocess

import ai_rand1

AI_TYPES: Dict[str, Callable[[GameState], List[SushiCardType]]] = {
    'ai_rand1': ai_rand1.play_turn 
}



def sum_lists(first: List[int], second: List[int]) -> List[int]:
    return [x + y for x, y in zip(first, second)]


def required_length(nmin: int, nmax: Optional[int]):
    class RequiredLength(argparse.Action):
        def __call__(self, parser, args, values, option_string=None):
            if (nmin is not None and nmin > len(values)) or (nmax is not None and nmax < len(values)):
                msg = 'argument "{f}" requires between {nmin} and {nmax} arguments'.format(
                    f=self.dest, nmin=nmin, nmax=nmax)
                raise argparse.ArgumentTypeError(msg)
            setattr(args, self.dest, values)
    return RequiredLength

def run_player(player, state: GameState) -> List[SushiCardType]:

    pass

# TODO: Fix to deal with running out of cards for large number of players
# NOTE: Modifies draw_cards
def deal_hands(draw_cards:List[SushiCardType], player_count:int) -> List[List[SushiCardType]]:
    hand_size = HAND_SIZES[player_count]
    hands: List[List[SushiCardType]] = [ [] for i in range(player_count) ]
    for i in range(player_count):
        for _ in range(hand_size):
            hands[i].append(draw_cards.pop(0))
    return hands


# Players pass hands to the next higher numbered player wrapping at the top
def run_round(players:List[str]):
    draw_cards = get_shuffled_cards()
    state = GameState.make_empty(len(players))
    for round_num in range(3):
        start_hand_size = HAND_SIZES[len(players)]
        state.hands = deal_hands(draw_cards, len(players))
        state.round_num = round_num
        round_plays: List[List[SushiCardType]] = [ [] for i in range(len(players)) ]
        for turn in range(start_hand_size):
            for i, player in enumerate(players):
                if turn == 0:
                    unhidden = list(state.hands)
                    state.hands[1:] = [[SushiCardType.HIDDEN] * start_hand_size] * (len(players) - 1)
                played = AI_TYPES[player](state)
                if len(played) == 2:
                    try:
                        state.played_cards[0].index(SushiCardType.CHOPSTICKS)
                    except ValueError:
                        raise ValueError(f'ai {player} tried to play 2 cards without chopsticks')
                elif len(played) != 1:
                    raise ValueError(f'ai {player} tried to play {len(played)} cards')
                hand_copy = list(state.hands[0])
                for played_card in played:
                    try:
                        hand_copy.remove(played_card)
                    except ValueError:
                        raise ValueError(f'ai {player} tried to play {played} with a hand of {state.hands[0]}')
                round_plays[i] = played
                if turn == 0:
                    state.hands = unhidden
                state.rotate()
            for i in range(len(players)):
                for card in round_plays[i]:
                    state.hands[i].remove(card)
                    if card != SushiCardType.PUDDING:
                        state.played_cards[i].append(card)
                    else:
                        state.puddings[i] += 1
                if len(round_plays[i]) == 2:
                    state.hands[i].append(SushiCardType.CHOPSTICKS)
                    state.played_cards[i].remove(SushiCardType.CHOPSTICKS)
        round_scores = score_round(state.played_cards)
        state.scores = sum_lists(round_scores, state.scores)
        for i in range(len(players)):
            state.discard_pile += state.played_cards[i]
            state.played_cards[i] = [] 
    pudding_scores = score_pudding(state.puddings)
    state.scores = sum_lists(pudding_scores, state.scores)
    state.pretty_print()
    
    


def main(players:List[str], games: int):
    run_round(players)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Run a series of games between a set of AIs")
    parser.add_argument('-p', '--players', nargs='+', choices=AI_TYPES.keys(),
                        help='<Requires 2-5> AI types for players', action=required_length(2, 5), required=True)
    parser.add_argument("-n", type=int, default=100,
                        help="Number of games to run")
    try:
        args = parser.parse_args()
    except argparse.ArgumentTypeError as err:
        print(err)
        exit(1)
    main(args.players, args.n)
