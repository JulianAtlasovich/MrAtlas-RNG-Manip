from rng_core import *
from read_dbs import *
from collections import defaultdict
from Cards import *
from db_queries import *
import sqlite3



class Event:
  def __init__(self, event_id, name, fixed, seed_advancements,description):   
    self.event_id = event_id
    self.name = name
    self.fixed = fixed
    self.seed_advancements = seed_advancements
    self.description = description
    self.initial_seed_index = -1
    self.new_seed_index = -1

  def has_event_id(self,event_id):
    return self.event_id == event_id

  def __str__(self):
    return "event_id: {},\tname: {},\tfixed: {},\tseed_advancements: {}".format(self.event_id, self.name, self.fixed, self.seed_advancements)


class Action:
  def __init__(self, action_id, name):
    self.action_id = action_id
    self.name = name
    

class Constants:
  fusion_combinations = [
  [0], [1], [2], [3], [4], 
  [0, 1], [0, 2], [0, 3], [0, 4], [1, 0], [1, 2], [1, 3], [1, 4], [2, 0], [2, 1], [2, 3], [2, 4], [3, 0], [3, 1], [3, 2], [3, 4], [4, 0], [4, 1], [4, 2], [4, 3], 
  [0, 1, 2], [0, 1, 3], [0, 1, 4], [0, 2, 1], [0, 2, 3], [0, 2, 4], [0, 3, 1], [0, 3, 2], [0, 3, 4], [0, 4, 1], [0, 4, 2], [0, 4, 3], [1, 0, 2], [1, 0, 3], [1, 0, 4], [1, 2, 0], [1, 2, 3], [1, 2, 4], [1, 3, 0], [1, 3, 2], [1, 3, 4], [1, 4, 0], [1, 4, 2], [1, 4, 3], [2, 0, 1], [2, 0, 3], [2, 0, 4], [2, 1, 0], [2, 1, 3], [2, 1, 4], [2, 3, 0], [2, 3, 1], [2, 3, 4], [2, 4, 0], [2, 4, 1], [2, 4, 3], [3, 0, 1], [3, 0, 2], [3, 0, 4], [3, 1, 0], [3, 1, 2], [3, 1, 4], [3, 2, 0], [3, 2, 1], [3, 2, 4], [3, 4, 0], [3, 4, 1], [3, 4, 2], [4, 0, 1], [4, 0, 2], [4, 0, 3], [4, 1, 0], [4, 1, 2], [4, 1, 3], [4, 2, 0], [4, 2, 1], [4, 2, 3], [4, 3, 0], [4, 3, 1], [4, 3, 2], 
  [0, 1, 2, 3], [0, 1, 2, 4], [0, 1, 3, 2], [0, 1, 3, 4], [0, 1, 4, 2], [0, 1, 4, 3], [0, 2, 1, 3], [0, 2, 1, 4], [0, 2, 3, 1], [0, 2, 3, 4], [0, 2, 4, 1], [0, 2, 4, 3], [0, 3, 1, 2], [0, 3, 1, 4], [0, 3, 2, 1], [0, 3, 2, 4], [0, 3, 4, 1], [0, 3, 4, 2], [0, 4, 1, 2], [0, 4, 1, 3], [0, 4, 2, 1], [0, 4, 2, 3], [0, 4, 3, 1], [0, 4, 3, 2], [1, 0, 2, 3], [1, 0, 2, 4], [1, 0, 3, 2], [1, 0, 3, 4], [1, 0, 4, 2], [1, 0, 4, 3], [1, 2, 0, 3], [1, 2, 0, 4], [1, 2, 3, 0], [1, 2, 3, 4], [1, 2, 4, 0], [1, 2, 4, 3], [1, 3, 0, 2], [1, 3, 0, 4], [1, 3, 2, 0], [1, 3, 2, 4], [1, 3, 4, 0], [1, 3, 4, 2], [1, 4, 0, 2], [1, 4, 0, 3], [1, 4, 2, 0], [1, 4, 2, 3], [1, 4, 3, 0], [1, 4, 3, 2], [2, 0, 1, 3], [2, 0, 1, 4], [2, 0, 3, 1], [2, 0, 3, 4], [2, 0, 4, 1], [2, 0, 4, 3], [2, 1, 0, 3], [2, 1, 0, 4], [2, 1, 3, 0], [2, 1, 3, 4], [2, 1, 4, 0], [2, 1, 4, 3], [2, 3, 0, 1], [2, 3, 0, 4], [2, 3, 1, 0], [2, 3, 1, 4], [2, 3, 4, 0], [2, 3, 4, 1], [2, 4, 0, 1], [2, 4, 0, 3], [2, 4, 1, 0], [2, 4, 1, 3], [2, 4, 3, 0], [2, 4, 3, 1], [3, 0, 1, 2], [3, 0, 1, 4], [3, 0, 2, 1], [3, 0, 2, 4], [3, 0, 4, 1], [3, 0, 4, 2], [3, 1, 0, 2], [3, 1, 0, 4], [3, 1, 2, 0], [3, 1, 2, 4], [3, 1, 4, 0], [3, 1, 4, 2], [3, 2, 0, 1], [3, 2, 0, 4], [3, 2, 1, 0], [3, 2, 1, 4], [3, 2, 4, 0], [3, 2, 4, 1], [3, 4, 0, 1], [3, 4, 0, 2], [3, 4, 1, 0], [3, 4, 1, 2], [3, 4, 2, 0], [3, 4, 2, 1], [4, 0, 1, 2], [4, 0, 1, 3], [4, 0, 2, 1], [4, 0, 2, 3], [4, 0, 3, 1], [4, 0, 3, 2], [4, 1, 0, 2], [4, 1, 0, 3], [4, 1, 2, 0], [4, 1, 2, 3], [4, 1, 3, 0], [4, 1, 3, 2], [4, 2, 0, 1], [4, 2, 0, 3], [4, 2, 1, 0], [4, 2, 1, 3], [4, 2, 3, 0], [4, 2, 3, 1], [4, 3, 0, 1], [4, 3, 0, 2], [4, 3, 1, 0], [4, 3, 1, 2], [4, 3, 2, 0], [4, 3, 2, 1], 
  [0, 1, 2, 3, 4], [0, 1, 2, 4, 3], [0, 1, 3, 2, 4], [0, 1, 3, 4, 2], [0, 1, 4, 2, 3], [0, 1, 4, 3, 2], [0, 2, 1, 3, 4], [0, 2, 1, 4, 3], [0, 2, 3, 1, 4], [0, 2, 3, 4, 1], [0, 2, 4, 1, 3], [0, 2, 4, 3, 1], [0, 3, 1, 2, 4], [0, 3, 1, 4, 2], [0, 3, 2, 1, 4], [0, 3, 2, 4, 1], [0, 3, 4, 1, 2], [0, 3, 4, 2, 1], [0, 4, 1, 2, 3], [0, 4, 1, 3, 2], [0, 4, 2, 1, 3], [0, 4, 2, 3, 1], [0, 4, 3, 1, 2], [0, 4, 3, 2, 1], [1, 0, 2, 3, 4], [1, 0, 2, 4, 3], [1, 0, 3, 2, 4], [1, 0, 3, 4, 2], [1, 0, 4, 2, 3], [1, 0, 4, 3, 2], [1, 2, 0, 3, 4], [1, 2, 0, 4, 3], [1, 2, 3, 0, 4], [1, 2, 3, 4, 0], [1, 2, 4, 0, 3], [1, 2, 4, 3, 0], [1, 3, 0, 2, 4], [1, 3, 0, 4, 2], [1, 3, 2, 0, 4], [1, 3, 2, 4, 0], [1, 3, 4, 0, 2], [1, 3, 4, 2, 0], [1, 4, 0, 2, 3], [1, 4, 0, 3, 2], [1, 4, 2, 0, 3], [1, 4, 2, 3, 0], [1, 4, 3, 0, 2], [1, 4, 3, 2, 0], [2, 0, 1, 3, 4], [2, 0, 1, 4, 3], [2, 0, 3, 1, 4], [2, 0, 3, 4, 1], [2, 0, 4, 1, 3], [2, 0, 4, 3, 1], [2, 1, 0, 3, 4], [2, 1, 0, 4, 3], [2, 1, 3, 0, 4], [2, 1, 3, 4, 0], [2, 1, 4, 0, 3], [2, 1, 4, 3, 0], [2, 3, 0, 1, 4], [2, 3, 0, 4, 1], [2, 3, 1, 0, 4], [2, 3, 1, 4, 0], [2, 3, 4, 0, 1], [2, 3, 4, 1, 0], [2, 4, 0, 1, 3], [2, 4, 0, 3, 1], [2, 4, 1, 0, 3], [2, 4, 1, 3, 0], [2, 4, 3, 0, 1], [2, 4, 3, 1, 0], [3, 0, 1, 2, 4], [3, 0, 1, 4, 2], [3, 0, 2, 1, 4], [3, 0, 2, 4, 1], [3, 0, 4, 1, 2], [3, 0, 4, 2, 1], [3, 1, 0, 2, 4], [3, 1, 0, 4, 2], [3, 1, 2, 0, 4], [3, 1, 2, 4, 0], [3, 1, 4, 0, 2], [3, 1, 4, 2, 0], [3, 2, 0, 1, 4], [3, 2, 0, 4, 1], [3, 2, 1, 0, 4], [3, 2, 1, 4, 0], [3, 2, 4, 0, 1], [3, 2, 4, 1, 0], [3, 4, 0, 1, 2], [3, 4, 0, 2, 1], [3, 4, 1, 0, 2], [3, 4, 1, 2, 0], [3, 4, 2, 0, 1], [3, 4, 2, 1, 0], [4, 0, 1, 2, 3], [4, 0, 1, 3, 2], [4, 0, 2, 1, 3], [4, 0, 2, 3, 1], [4, 0, 3, 1, 2], [4, 0, 3, 2, 1], [4, 1, 0, 2, 3], [4, 1, 0, 3, 2], [4, 1, 2, 0, 3], [4, 1, 2, 3, 0], [4, 1, 3, 0, 2], [4, 1, 3, 2, 0], [4, 2, 0, 1, 3], [4, 2, 0, 3, 1], [4, 2, 1, 0, 3], [4, 2, 1, 3, 0], [4, 2, 3, 0, 1], [4, 2, 3, 1, 0], [4, 3, 0, 1, 2], [4, 3, 0, 2, 1], [4, 3, 1, 0, 2], [4, 3, 1, 2, 0], [4, 3, 2, 0, 1], [4, 3, 2, 1, 0]
  ]

  opponents = [
  [1, 'Simon Muran',5],
  [2, 'Teana',5],
  [3, 'Jono',5],
  [4, 'Villager1',5],
  [5, 'Villager2',5],
  [6, 'Villager3',5],
  [7, 'Seto',10],
  [8, 'Heishin',20],
  [9, 'Rex Raptor',8],
  [10, 'Weevil Underwood',8],
  [11, 'Mai Valentine',10],
  [12, 'Bandit Keith',12],
  [13, 'Shadi',12],
  [14, 'Yami Bakura',14],
  [15, 'Pegasus',16],
  [16, 'Isis',16],
  [17, 'Kaiba',16],
  [18, 'Mage Soldier',12],
  [19, 'Jono 2nd',10],
  [20, 'Teana 2nd',10],
  [21, 'Ocean Mage',14],
  [22, 'High Mage Secmeton',16],
  [23, 'Forest Mage',14],
  [24, 'High Mage Anubisius',16],
  [25, 'Mountain Mage',14],
  [26, 'High Mage Atenza',16],
  [27, 'Desert Mage',14],
  [28, 'High Mage Martis',16],
  [29, 'Meadow Mage',14],
  [30, 'High Mage Kepura',16],
  [31, 'Labyrinth Mage',16],
  [32, 'Seto 2nd',18],
  [33, 'Guardian Sebek',20],
  [34, 'Guardian Neku',20],
  [35, 'Heishin 2nd',20],
  [36, 'Seto 3rd',20],
  [37, 'DarkNite',20],
  [38, 'Nitemare',20],
  [39, 'Duel Master K',15]
  ]

  actions = []  
  actions.append(Action(1, 'Dump'))
  actions.append(Action(2, 'Fusion'))
  actions.append(Action(4, 'Attack Card'))
  actions.append(Action(5, 'Attack LP'))
  actions.append(Action(6, 'Equip'))
  actions.append(Action(7, 'Change Field'))
  actions.append(Action(8, 'Trap Triggered'))

  #'attack card
  #field card
  #direct attack


  events = []
  events.append(Event(0 ,"INITIAL_DECKS_SHUFFLING"     ,False  ,None,"Player and Opponent decks are shuffled using initial seed index"))
  events.append(Event(1 ,"BURN"     ,False  ,None,"Animation after an attack that burns a card"))
  events.append(Event(2 ,"BURN_3D"    ,False  ,None,"Animation after an attack that burns a card after 3D mode"))
  events.append(Event(3 ,"DIRECT_HIGH"  ,True ,4864, "Attacking to the opponent life points >= 1000 damage"))
  events.append(Event(4 ,"DIRECT_LOW"   ,True ,2624,"Attacking to the opponent life points < 1000 damage"))
  events.append(Event(5 ,"DUMP"     ,True ,1, "Selecting 2 cards to be fused that can't be fused"))
  events.append(Event(6 ,"EMPTY_ANIM"   ,False  ,None, "Placeholder for no animation"))
  events.append(Event(7 ,"END_OF_DUEL"  ,True ,15, "You win animation"))
  events.append(Event(8 ,"EQUIP"      ,True ,96, "Using an equip card"))
  events.append(Event(9 ,"FIELD_MOUNT"  ,True ,2880, "Field spell card Mountain activated"))
  events.append(Event(10,"FIELD_USUAL"  ,True ,4928, "Field spell card activated, that is not Mountain or Yami"))
  events.append(Event(11,"FIELD_YAMI"   ,True ,1856, "Field spell card Yami activated"))
  events.append(Event(12,"FUSION"     ,True ,4552, "Fusion animation"))
  events.append(Event(13,"GS_ANIM"    ,False  ,None, "Guardian Star animation"))
  events.append(Event(14,"SPAWN_3D"   ,True ,1056,"Spawning a monster in 3D mode"))
  events.append(Event(15,"SWIPE_ATK_HIGH" ,True ,4956, "Attacking animation when opponent card is in attack mode and attack deals >= 1000 damage"))
  events.append(Event(16,"SWIPE_ATK_LOW"  ,True ,2716, "Attacking animation when opponent card is in attack mode and attack deals < 1000 damage"))
  events.append(Event(17,"SWIPE_DEF"    ,True ,4926, "Attacking animation when opponent card is in defense mode"))
  events.append(Event(18,"TRAP_TRIGGERED" ,True ,2752, "Animation after an attack that triggers a trap card"))
  events.append(Event(19,"LOSE_ATTACK"  ,True ,4864, "Animation after attacking an opponent monster and losing the attack"))

  field_types = []
  field_types.append([1,"*None*"])
  field_types.append([2,"Forest"])
  field_types.append([3,"Wasteland"])
  field_types.append([4,"Mountain"])
  field_types.append([5,"Sogen"])
  field_types.append([6,"Umi"])
  field_types.append([7,"Yami"])

  card_types = {
    0: 'Dragon',
    1: 'Spellcaster',
    2: 'Zombie',
    3: 'Warrior',
    4: 'Beast-Warrior',
    5: 'Beast',
    6: 'Winged Beast',
    7: 'Fiend',
    8: 'Fairy',
    9: 'Insect',
    10: 'Dinosaur',
    11: 'Reptile',
    12: 'Fish',
    13: 'Sea Serpent',
    14: 'Machine',
    15: 'Thunder',
    16: 'Aqua',
    17: 'Pyro',
    18: 'Rock',
    19: 'Plant',
    20: 'Magic',
    21: 'Trap',
    22: 'Ritual',
    23: 'Equip'
  }



  opponents_with_special_field_type = {
    21: 6, #opponent_id : fielt_type
    22: 6,
    23: 2,
    24: 2,
    25: 4,
    26: 4,
    27: 3,
    28: 3,
    29: 5,
    30: 5,
    34: 7,
  }
  
  field_cards_positive_influence_on_types = defaultdict(lambda: [])
  field_cards_positive_influence_on_types[2] = [4,5,9]
  field_cards_positive_influence_on_types[3] = [2,10,18]
  field_cards_positive_influence_on_types[4] = [0,6,15]
  field_cards_positive_influence_on_types[5] = [3,4]
  field_cards_positive_influence_on_types[6] = [15,16]
  field_cards_positive_influence_on_types[7] = [1,7] #spellcasters and fiend
      

  field_cards_negative_influence_on_types = defaultdict(lambda: [])
  field_cards_negative_influence_on_types[6] = [14,17] #machine and pyro
  field_cards_negative_influence_on_types[7] = [8] #fairy

  card_ids_field_types = {
    330: "Forest",
    331: "Wasteland",
    332: "Mountain",
    333: "Sogen",
    334: "Umi",
    335: "Yami",
  }

  anims_steps_adv = {
    'DIRECT_HIGH' : 4864,
    'DIRECT_LOW'  : 2624,
    'END_OF_DUEL' : 15,
    'FUSION'    : 4552,
    'SPAWN_3D': 1056,
    'DUMP'      : 1,
    'SWIPE_ATK_HIGH': 4956,
    'SWIPE_ATK_LOW' : 2716,
    'SWIPE_DEF'   : 4926,  
    'LOSE_ATTACK' : 4864,
    'EQUIP': 96,
    'FIELD_MOUNT': 2880,
    'FIELD_USUAL': 4928,
    'FIELD_YAMI': 1856,
    "SPAWN_3D": 1056,
    "TRAP_TRIGGERED": 2752
  }


  guardian_star_strong_against = {
    'MARS'    : 'JUPITER',
    'JUPITER' : 'SATURN',
    'SATURN'  : 'URANUS',
    'URANUS'  : 'PLUTO',
    'PLUTO'   : 'NEPTUNE',
    'NEPTUNE' : 'MARS',
    'MERCURY'   : 'SUN',
    'SUN'   : 'MOON',
    'MOON'    : 'VENUS',
    'VENUS'   : 'MERCURY'
  }

  guardian_star_names = [
    "N/A",
    "MARS",
    "JUPITER",
    "SATURN",
    "URANUS",
    "PLUTO",
    "NEPTUNE",
    "MERCURY",
    "SUN",
    "MOON",
    "VENUS"
  ]

  non_monster_card_types = {
    20: 'MAGIC',
    21: 'TRAP',
    22: 'RITUAL',
    23: 'EQUIP'
  }

  non_monster_card_type_names = {
    'MAGIC': 20,
    'TRAP': 21,
    'RITUAL': 22,
    'EQUIP': 23
  }


  card_data = card_data
  
  enemy_drop_pool = list()

  duel_rank_points_remaining_LP = {
    '8000': 6,
    '7000 - 7999': 4,
    '1000 - 6999': 0,
    '100 - 999': -5,
    '< 100': -7
  }

  duel_rank_keys = ['num_fusions', 'num_effectives', 'num_facedowns', 'num_magics','num_equips', 'num_traps', 'num_cards_left','num_defensive_wins', 'remaining_lp', 'num_opp_cards_left']
  
  duel_rank_defaults = {
    'num_fusions': 0,
    'num_effectives': 0,
    'num_facedowns': 0,
    'num_magics': 0,
    'num_equips': 0,
    'num_traps': 0,
    'num_cards_left': 35,
    'num_defensive_wins': 0,
    'remaining_lp': '8000',
    'num_opp_cards_left': 35
  }

  fusions = find_fusion_db()
  card_equips = get_equips_db()
  #fusions = {}
  #variable_anim_steps = {}
  @classmethod
  def load_dbs_to_memory(cls,initial_seed_index):
    cls.variable_anim_steps = {}
    seeds_to_consider = 150000
    animation_db_cursor = (sqlite3.connect('AnimationDatabase.db')).cursor()
    query = 'select InitialSeedIndex,AdvanceSize from VariableAdvs where AnimationID = {} and InitialSeedIndex between {} and {}'.format(1,initial_seed_index,initial_seed_index+seeds_to_consider)
    cls.variable_anim_steps['BURN'] = dict(animation_db_cursor.execute(query).fetchall())
    query = 'select InitialSeedIndex,AdvanceSize from VariableAdvs where AnimationID = {} and InitialSeedIndex between {} and {}'.format(2,initial_seed_index,initial_seed_index+seeds_to_consider)
    cls.variable_anim_steps['BURN_3D'] = dict(animation_db_cursor.execute(query).fetchall())
    query = 'select InitialSeedIndex,AdvanceSize from VariableAdvs where AnimationID = {} and InitialSeedIndex between {} and {}'.format(13,initial_seed_index,initial_seed_index+seeds_to_consider)
    cls.variable_anim_steps['GS_ANIM'] = dict(animation_db_cursor.execute(query).fetchall())
    
    


class Card():
  def __init__(self):
    self.attack = 0
    self.defense = 0
    self.cardID = 0
    self.name = ''
    self.guardian_star = '' #the first one, AI will always play this one
    self.guardian_stars = []
    self.type = 0
    self.cards_left_in_opp_deck = 0

  def __str__(self):
    return "cardID: {},name: {}, attack: {},defense: {}, type: {}, GS: {}\n".format(self.cardID, self.name ,self.attack,self.defense,self.type,self.guardian_stars)
  
  def values_to_list(self):
    return [self.cardID, self.name ,self.attack,self.defense,self.guardian_star]    

  def to_dict(self):
    return {
        "ID": self.cardID,
        "Name": self.name,
        "Attack": self.attack,
        "Defense": self.defense,
        "Guardian Star": self.guardian_star,
        "Guardian Stars": self.guardian_stars,
        "Cards left in Opp Deck": self.cards_left_in_opp_deck

    }

class Main_phase_action:
  def __init__(self,card_result,seed_index_delta,description,action_type):
    self.my_cards_in_field = []
    self.seed_index = None
    self.description = description
    self.seed_index_delta = seed_index_delta
    self.card_result = card_result
    self.action_type = action_type
    self.new_hand = []
    self.events = []
    

  def __eq__(self, other):
    return self.card_result.cardID == other.card_result.cardID and self.seed_index_delta == other.seed_index_delta and self.card_result.guardian_star == self.card_result.guardian_star
  
  def __str__(self):
    return "current_seed_index: {}, seed_index_delta: {},card result: {},description: {}\n".format(self.seed_index,self.seed_index_delta, self.card_result.name ,self.description)

class Battle_phase_action:
  def __init__(self):
    self.description = ""
    self.seed_index_delta = 0
    self.current_seed_index = 0
    self.action_type = ''

  def __str__(self):
    return "current_seed_index {}, seed_index_delta: {},description: {}\n".format(self.current_seed_index,self.seed_index_delta, self.description)

class Play:
  def __init__(self, seed_index):   
    self.final_seed_index = 0
    self.main_phase_action = None
    self.battle_phase_actions = []
    self.drop_card = None
    self.my_cards_in_field=[]
    self.seed_index = seed_index
    self.seed = index_to_seed(seed_index)


  def calculate_drop(self,enemy_drop_pool):
    seed_index_advancements = 0
    seed_index_advancements += self.main_phase_action.seed_index_delta 
    for battle_phase_action in self.battle_phase_actions:
      seed_index_advancements += battle_phase_action.seed_index_delta
    seed_index_advancements += Constants.anims_steps_adv['END_OF_DUEL']
    self.final_seed_index = self.seed_index + seed_index_advancements
    seed = big_adv(self.seed, seed_index_advancements)
    rng_num = prn(seed) % 2048                         
    cardId = enemy_drop_pool[rng_num]

    self.drop_card = Card()
    self.drop_card.cardID = cardId
    self.drop_card.attack = Constants.card_data[cardId-1]['Attack']
    self.drop_card.defense = Constants.card_data[cardId-1]['Defense']
    self.drop_card.name = Constants.card_data[cardId-1]['Name']
    self.drop_card.type = Constants.card_data[cardId-1]['Type']
    
    
  def __str__(self):
    text = 'main_phase_action: {}'.format(self.main_phase_action)
    for bpa in self.battle_phase_actions:
      text+='battle_phase_action: {}'.format(str(bpa))
    text+='end of duel: seed_index_delta: {}, current_seed_index {}\n'.format(15,self.final_seed_index)
    text+='drop_name: {},dropID: {}\n'.format(self.drop_card.name,self.drop_card.cardID)
    return text

  def __eq__(self, other):
    return self.drop_card.cardID == other.drop_card.cardID

  