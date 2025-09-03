def adv(seed):
    """Advance the seed once"""
    return (1103515245 * seed + 12345) % (2 ** 32)


def prn(seed):
    """Return the random number from a seed"""
    return (seed >> 16) & 0x7FFF


def fm_shift():
    """Return the AffineShift used by FM's PRNG"""
    return (1103515245, 12345)


def mult_shifts(shift_1, shift_2):
    """Multiply two AffineShifts together"""
    new_mult = (shift_1[0] * shift_2[0]) % (2 ** 32)
    new_inc = (shift_1[0] * shift_2[1] + shift_1[1]) % (2 ** 32)
    return (new_mult, new_inc)


def shift_pow(shift, power):
    """Raise an AffineShift to a given power"""
    power %= 2 ** 32
    if power == 0:
        return (1, 0)
    elif power % 2 == 0:
        return shift_pow(mult_shifts(shift, shift), power // 2)
    else:
        return mult_shifts(shift, shift_pow(shift, power - 1))


def big_adv(seed, adv_size):
    """Advance seed adv_size times"""
    shift = shift_pow(fm_shift(), adv_size)
    return (shift[0] * seed + shift[1]) % (2 ** 32)


def discrete_log(power_of_mult):
    """Find the discrete log mod 2^32, base 1103515245"""
    if (power_of_mult % 4 != 1):
        raise ValueError('Not 1 mod 4')

    exponent = 0

    for i in range(3, 32):
        if pow(1103515245, exponent, 2 ** i) != power_of_mult % (2 ** i):
            exponent += 2 ** (i - 3)

    if pow(1103515245, exponent, 2 ** 32) != power_of_mult:
        exponent += 2 ** 29

    return exponent

def dist_from_zero(seed):
    """Find the number of seed advances from 0 to seed"""
    pow_of_mult = (1 + 1268574668 * seed) % (2 ** 32)
    possible_exp = discrete_log(pow_of_mult)

    while big_adv(0, possible_exp) != seed:
        possible_exp += 2 ** 30
        possible_exp %= 2 ** 32
    return possible_exp

def seed_to_index(seed):
    """Find the index of a seed"""
    return (dist_from_zero(seed) - 1199997605) % (2 ** 32)

def index_to_seed(index):
    return big_adv(1431655765,index)


def shuffle(deck, seed):
    """Shuffles deck according to seed"""
    for i in range(160):
        seed = adv(seed)
        place_1 = prn(seed) % 40
        seed = adv(seed)
        place_2 = prn(seed) % 40
        deck[place_1], deck[place_2] = deck[place_2], deck[place_1]


def shuffle_copy(deck, seed):
    """Shuffles deck according to seed and returns a copy"""
    deck_result = deck[:]
    for i in range(160):
        seed = adv(seed)
        place_1 = prn(seed) % 40
        seed = adv(seed)
        place_2 = prn(seed) % 40
        deck_result[place_1], deck_result[place_2] = deck_result[place_2], deck_result[place_1]
    return deck_result      

                