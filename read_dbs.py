from enum import Enum
import sqlite3


def read_ai_gs():
    conn = sqlite3.connect('FmDatabaseWithGS.db')
    c = conn.cursor()

    c.execute('select GuardianStar1 from CardInfo order by CardId')
    stars = c.fetchall()

    conn.close()
    return list(map(lambda x: x[0], stars))

    
def read_hand_size(opp_name):
    conn = sqlite3.connect('FmDatabase.db')
    c = conn.cursor()
    c.execute('select HandSize from Duelists where Name == ?', (opp_name,))
    sizes = c.fetchall()

    if len(sizes) != 1:
        raise ValueError('Not a valid opponent')

    conn.close()
    return sizes[0][0]


class PoolType(Enum):
    """Enum for pool types"""
    DECK = 1
    SA_POW = 2
    BCD = 3
    SA_TEC = 4


def read_pool(opp_name, pool_type):
    conn = sqlite3.connect('FmDatabaseWithGS.db')
    c = conn.cursor()

    c.execute(('select CardProb from DropPools '
               'where Duelist == ? and PoolType == ? '
               'order by CardId'), (opp_name, pool_type))
    probs = c.fetchall()
    conn.close()

    pool = []
    for i in range(1, 723):
        pool += [i] * probs[i - 1][0]

    if len(pool) >= 2048:
        pool = pool[0:2048]
    else:
        pool += [0] * (2048 - len(pool))

    return pool


class AnimType(Enum):
    BURN = 1
    BURN_3D = 2
    DIRECT_HIGH = 3
    DIRECT_LOW = 4
    DUMP = 5
    EMPTY_ANIM = 6
    END_OF_DUEL = 7
    EQUIP = 8
    FIELD_MOUNT = 9
    FIELD_USUAL = 10
    FIELD_YAMI = 11
    FUSE = 12
    GS_ANIM = 13
    SPAWN = 14
    SWIPE_ATK_HIGH = 15
    SWIPE_ATK_LOW = 16
    SWIPE_DEF = 17
    TRAP_TRIGGERED = 18


def get_anim_data():
    fixed_advs = {}
    vary_advs = {}

    conn = sqlite3.connect('AnimationDatabase.db')
    c = conn.cursor()

    c.execute('select AnimationID, Advances from FixedAdvs')
    fixed_pairs = c.fetchall()

    c.execute(('select AnimationID, AdvanceSize from VariableAdvs '
               'order by InitialSeedIndex'))
    vary_pairs = c.fetchall()

    conn.close()

    for (anim_id, advance) in fixed_pairs:
        fixed_advs[AnimType(anim_id)] = advance

    for (anim_id, advance) in vary_pairs:
        try:
            vary_advs[AnimType(anim_id)].append(advance)
        except KeyError:
            vary_advs[AnimType(anim_id)] = [advance]

    return (fixed_advs, vary_advs)


def get_ai_sorts():
    conn = sqlite3.connect('FmDatabase.db')
    c = conn.cursor()

    c.execute('select AISort from Cards order by NumSort')
    sorts = c.fetchall()

    conn.close()
    return list(map(lambda x: x[0], sorts))


def get_card_names():
    conn = sqlite3.connect('FmDatabase.db')
    c = conn.cursor()

    c.execute('select Name from Cards order by NumSort')
    sorts = c.fetchall()

    conn.close()
    return list(map(lambda x: x[0], sorts))


def get_possible_seed_index_by_order(order):
    conn = sqlite3.connect('FmDatabase.db')
    c = conn.cursor()

    # Dynamically generate the SQL query based on the length of the order array
    placeholders = ' AND '.join([f"Card{i} IN ({','.join(['?'] * len(order[i]))})" for i in range(len(order))])
    sql = f"SELECT SeedIndex FROM DeckOrders WHERE {placeholders}"

    # Flatten the order array for query parameters
    flat_order = [item for sublist in order for item in sublist]

    # Execute the query
    c.execute(sql, flat_order)
    result = c.fetchall()

    # Extract seed indexes from the result
    possible_seed_indexes = [res[0] for res in result]
    conn.close()

    return possible_seed_indexes