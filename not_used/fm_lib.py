from read_dbs import *
from rng_core import *


def ai_deck(pool, seed):
    seed = big_adv(seed, 320)

    deck = []
    while len(deck) < 40:
        seed = adv(seed)
        new_card = pool[prn(seed) % 2048]
        if len([c for c in deck if c == new_card]) != 3:
            deck.append(new_card)

    shuffle(deck, seed)
    seed = big_adv(seed, 320)

    return (deck, seed)



def adv_across_anims(data, seed, anims):
    for a in anims:
        try:
            seed = big_adv(seed, data[0][a])
        except KeyError:
            index = seed_to_index(seed)
            try:
                adv_size = data[1][a][index]
                seed = big_adv(seed, adv_size)
            except IndexError:
                error_str = 'Animation {} doesn\'t have data for seed {}'
                raise ValueError(error_str.format(a.value, index))
    return seed


def options_to_anims(options):
    for k in options.keys():
        if k in ['dumps', 'fusions']:
            if len(options[k]) != options['numb_of_turns']:
                raise ValueError('{} is the wrong length'.format(k))
        elif k != 'numb_of_turns':
            if len(options[k]) + 1 != options['numb_of_turns']:
                raise ValueError('{} is the wrong length'.format(k))

    norm_battle_anims = [AnimType.SWIPE_DEF, AnimType.BURN]
    anims = []
    for i in range(options['numb_of_turns']):
        anims += [AnimType.DUMP] * options['dumps'][i]
        anims += [AnimType.FUSE] * options['fusions'][i]

        if i > 0:
            if options['gs'][i - 1]:
                anims.append(AnimType.GS_ANIM)
                
            if options['quicks'][i - 1]:
                anims.append(AnimType.BURN_3D)
            else:
                anims += norm_battle_anims

            anims += [AnimType.DIRECT_HIGH] * options['directs'][i - 1]
            anims += [AnimType.DIRECT_LOW] * options['direct_lows'][i - 1]

        if i != options['numb_of_turns'] - 1:
            anims += norm_battle_anims * options['enemy_dest'][i]

    anims.append(AnimType.END_OF_DUEL)
    return anims


def make_ai_play(deck, start_place, end_place, ai_sorts):
    best_card_place = start_place
    best_ai_rank = ai_sorts[deck[start_place] - 1]

    for i in range(start_place, end_place):
        if ai_sorts[deck[i] - 1] < best_ai_rank:
            best_card_place = i
            best_ai_rank = ai_sorts[deck[i] - 1]

    if best_card_place - start_place >= 5:
        deck[start_place], deck[best_card_place] = deck[best_card_place], deck[start_place]
    else:
        earlier_place = best_card_place - 1
        while earlier_place >= start_place:
            deck[earlier_place], deck[earlier_place + 1] = deck[earlier_place + 1], deck[earlier_place]
            earlier_place -= 1


def ai_sort(deck, hand_size, ai_sorts):
    for i in range(0, 40):
        end_place = min(i + hand_size, 40)
        make_ai_play(deck, i, end_place, ai_sorts)
