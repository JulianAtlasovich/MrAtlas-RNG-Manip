import sqlite3
from read_dbs import *
from rng_core import *
from drop_manip_classes_and_constants import *
from db_queries import *
import copy
from itertools import permutations
from datetime import datetime
import streamlit as st

@st.cache_data(ttl=600)
def setup_load_db_to_memory_st(seed_index):
  Constants.load_dbs_to_memory(seed_index) # for performance reasons load dbs to memory only once

def get_opponent_name_by_id(opponent_id):
  return Constants.opponents[opponent_id-1][1]

def get_opponent_hand_size_by_id(opponent_id):
  return Constants.opponents[opponent_id-1][2]

def remove_last_element_from_lists(list_of_lists):
  result = []
  for aList in list_of_lists:
    result.append(aList[:-1])
  return result


def get_card_data_from_card_ids(cardIds):
  cards = []
  for cardId in cardIds:
    aCard = Card()
    aCard.cardID = cardId
    aCard.attack = Constants.card_data[cardId-1]['Attack']
    aCard.defense = Constants.card_data[cardId-1]['Defense']
    aCard.name = Constants.card_data[cardId-1]['Name']
    aCard.guardian_star = Constants.guardian_star_names[Constants.card_data[cardId-1]['GuardianStarA']]
    aCard.guardian_stars.append(Constants.guardian_star_names[Constants.card_data[cardId-1]['GuardianStarA']])
    aCard.guardian_stars.append(Constants.guardian_star_names[Constants.card_data[cardId-1]['GuardianStarB']])
    aCard.type = Constants.card_data[cardId-1]['Type']
    cards.append(aCard)
  return cards

def select_best_card_from_hand(cards_in_hand):
  best_card = -1
  best_max_stat = -1

  for i,card in enumerate(cards_in_hand):
    if card.attack > best_max_stat:
      best_max_stat = card.attack 
      best_card = i
    if card.defense > best_max_stat:
      best_max_stat = card.defense 
      best_card = i
  return cards_in_hand[best_card]

def get_field_card_from_hand(cards_in_hand):
  for card in cards_in_hand:
    if card.cardID in Constants.card_ids_field_types.keys():
      return card
  return None   

def select_best_card_from_hand_for_mages(cards_in_hand,no_field_type):
  if no_field_type == True: 
    field_card = get_field_card_from_hand(cards_in_hand)
    if field_card is not None:
      no_field_type = False
      return field_card,no_field_type
  return select_best_card_from_hand(cards_in_hand),no_field_type

def generate_opponents_cards_to_play_order(opponent_id,opp_deck,no_field_type):
  opp_hand_size = get_opponent_hand_size_by_id(opponent_id)
  cards_to_play = []
  cards_in_hand = get_card_data_from_card_ids(opp_deck[:opp_hand_size])
  for turn_number in range(len(opp_deck)-5):
    if opponent_id in Constants.opponents_with_special_field_type.keys(): #if opponent is not a mage/neku
      best_card,no_field_type = select_best_card_from_hand_for_mages(cards_in_hand,no_field_type)
    else:
      best_card = select_best_card_from_hand(cards_in_hand)
    cards_in_hand.remove(best_card)
    best_card.cards_left_in_opp_deck = 35 - turn_number # adding to identify easily the turn in which the card will be played
    cards_to_play.append(best_card)
    if opp_hand_size+turn_number < 40:
      new_card = get_card_data_from_card_ids([opp_deck[opp_hand_size+turn_number]])[0]      
      cards_in_hand.append(new_card)
  return cards_to_play

def object_list_to_value_list(object_list):
  result = []
  for myObject in object_list:
    result.append(myObject.values_to_list())
  return result

def get_event_id_by_name(event_name):
  for event in Constants.events:
    if event.name == event_name:
      return event.event_id
  return None

def create_player_deck(deck,seed_index):
  seed = index_to_seed(seed_index)
  shuffled_deck = shuffle_copy(deck, seed)
  return shuffled_deck

def create_opponent_deck(pool, seed_index,opponent_name,player_card_ids_in_deck):
    seed = index_to_seed(seed_index)
    seed = big_adv(seed, 320) #player shuffle is always 320 advancements
    seed_index += 320
    deck = []

    if opponent_name != "Duel Master K":
      while len(deck) < 40:
          seed = adv(seed)
          seed_index += 1
          new_card = pool[prn(seed) % 2048]
          if len([c for c in deck if c == new_card]) != 3:
              deck.append(new_card)
      shuffled_deck = shuffle_copy(deck, seed)
    
    else: #Duel Master K      
      shuffled_deck = create_player_deck(player_card_ids_in_deck,seed_index)

    seed = big_adv(seed, 320) #player shuffle is always 320 advancements
    seed_index += 320
    return (shuffled_deck, seed_index)

def get_event_by_id(event_id):
  return Constants.events[event_id]

def get_variable_advancement_from_event(seed_index,anim_name):
  return Constants.variable_anim_steps[anim_name][seed_index]


def get_index_positions(list_of_elems, element):
    ''' Returns the indexes of all occurrences of give element in
    the list- listOfElements '''
    index_pos_list = []
    index_pos = 0
    while True:
        try:
            index_pos = list_of_elems.index(element, index_pos)
            index_pos_list.append(index_pos)
            index_pos += 1
        except ValueError as e:
            break
    return index_pos_list


def read_deck_and_hand():
  with open('my_deck.txt') as f:
    my_deck = f.read().splitlines()
  my_deck = list(map(int,my_deck))
  
  hand = input('insert card ids for first 5 cards separated by space: ').strip().split(' ')
  hand = list(map(int,hand))
  return my_deck,hand
  
def get_initial_possible_seeds(my_deck,hand):
  order = []
  for i in range(len(hand)):
    card_pos = get_index_positions(my_deck,hand[i])
    order.append(card_pos)
  possible_seed_indexes = get_possible_seed_index_by_order(order)
  return possible_seed_indexes

### new stuff ###


def get_adv_steps_from_anim(index,anim_name):
  """return the new seed and index after an animation (fixed or variable)"""  
  variable_animations = {
    'BURN': 1,
    'BURN_3D': 2,
    'GS_ANIM': 13      
  }

  if anim_name not in variable_animations.keys():
    steps_to_adv = Constants.anims_steps_adv[anim_name] 
  else:
    #anim_id = variable_animations[anim_name]
    steps_to_adv = get_variable_advancement_from_event(index,anim_name)
  return steps_to_adv 
  

def get_best_fusion(hand):
  best_card = None
  best_fusion_combination = None
  max_attack = -1
  
  """ fusion_combinations = [
  [0], [1], [2], [3], [4], 
  [0, 1], [0, 2], [0, 3], [0, 4], [1, 0], [1, 2], [1, 3], [1, 4], [2, 0], [2, 1], [2, 3], [2, 4], [3, 0], [3, 1], [3, 2], [3, 4], [4, 0], [4, 1], [4, 2], [4, 3], 
  [0, 1, 2], [0, 1, 3], [0, 1, 4], [0, 2, 1], [0, 2, 3], [0, 2, 4], [0, 3, 1], [0, 3, 2], [0, 3, 4], [0, 4, 1], [0, 4, 2], [0, 4, 3], [1, 0, 2], [1, 0, 3], [1, 0, 4], [1, 2, 0], [1, 2, 3], [1, 2, 4], [1, 3, 0], [1, 3, 2], [1, 3, 4], [1, 4, 0], [1, 4, 2], [1, 4, 3], [2, 0, 1], [2, 0, 3], [2, 0, 4], [2, 1, 0], [2, 1, 3], [2, 1, 4], [2, 3, 0], [2, 3, 1], [2, 3, 4], [2, 4, 0], [2, 4, 1], [2, 4, 3], [3, 0, 1], [3, 0, 2], [3, 0, 4], [3, 1, 0], [3, 1, 2], [3, 1, 4], [3, 2, 0], [3, 2, 1], [3, 2, 4], [3, 4, 0], [3, 4, 1], [3, 4, 2], [4, 0, 1], [4, 0, 2], [4, 0, 3], [4, 1, 0], [4, 1, 2], [4, 1, 3], [4, 2, 0], [4, 2, 1], [4, 2, 3], [4, 3, 0], [4, 3, 1], [4, 3, 2], 
  [0, 1, 2, 3], [0, 1, 2, 4], [0, 1, 3, 2], [0, 1, 3, 4], [0, 1, 4, 2], [0, 1, 4, 3], [0, 2, 1, 3], [0, 2, 1, 4], [0, 2, 3, 1], [0, 2, 3, 4], [0, 2, 4, 1], [0, 2, 4, 3], [0, 3, 1, 2], [0, 3, 1, 4], [0, 3, 2, 1], [0, 3, 2, 4], [0, 3, 4, 1], [0, 3, 4, 2], [0, 4, 1, 2], [0, 4, 1, 3], [0, 4, 2, 1], [0, 4, 2, 3], [0, 4, 3, 1], [0, 4, 3, 2], [1, 0, 2, 3], [1, 0, 2, 4], [1, 0, 3, 2], [1, 0, 3, 4], [1, 0, 4, 2], [1, 0, 4, 3], [1, 2, 0, 3], [1, 2, 0, 4], [1, 2, 3, 0], [1, 2, 3, 4], [1, 2, 4, 0], [1, 2, 4, 3], [1, 3, 0, 2], [1, 3, 0, 4], [1, 3, 2, 0], [1, 3, 2, 4], [1, 3, 4, 0], [1, 3, 4, 2], [1, 4, 0, 2], [1, 4, 0, 3], [1, 4, 2, 0], [1, 4, 2, 3], [1, 4, 3, 0], [1, 4, 3, 2], [2, 0, 1, 3], [2, 0, 1, 4], [2, 0, 3, 1], [2, 0, 3, 4], [2, 0, 4, 1], [2, 0, 4, 3], [2, 1, 0, 3], [2, 1, 0, 4], [2, 1, 3, 0], [2, 1, 3, 4], [2, 1, 4, 0], [2, 1, 4, 3], [2, 3, 0, 1], [2, 3, 0, 4], [2, 3, 1, 0], [2, 3, 1, 4], [2, 3, 4, 0], [2, 3, 4, 1], [2, 4, 0, 1], [2, 4, 0, 3], [2, 4, 1, 0], [2, 4, 1, 3], [2, 4, 3, 0], [2, 4, 3, 1], [3, 0, 1, 2], [3, 0, 1, 4], [3, 0, 2, 1], [3, 0, 2, 4], [3, 0, 4, 1], [3, 0, 4, 2], [3, 1, 0, 2], [3, 1, 0, 4], [3, 1, 2, 0], [3, 1, 2, 4], [3, 1, 4, 0], [3, 1, 4, 2], [3, 2, 0, 1], [3, 2, 0, 4], [3, 2, 1, 0], [3, 2, 1, 4], [3, 2, 4, 0], [3, 2, 4, 1], [3, 4, 0, 1], [3, 4, 0, 2], [3, 4, 1, 0], [3, 4, 1, 2], [3, 4, 2, 0], [3, 4, 2, 1], [4, 0, 1, 2], [4, 0, 1, 3], [4, 0, 2, 1], [4, 0, 2, 3], [4, 0, 3, 1], [4, 0, 3, 2], [4, 1, 0, 2], [4, 1, 0, 3], [4, 1, 2, 0], [4, 1, 2, 3], [4, 1, 3, 0], [4, 1, 3, 2], [4, 2, 0, 1], [4, 2, 0, 3], [4, 2, 1, 0], [4, 2, 1, 3], [4, 2, 3, 0], [4, 2, 3, 1], [4, 3, 0, 1], [4, 3, 0, 2], [4, 3, 1, 0], [4, 3, 1, 2], [4, 3, 2, 0], [4, 3, 2, 1], 
  [0, 1, 2, 3, 4], [0, 1, 2, 4, 3], [0, 1, 3, 2, 4], [0, 1, 3, 4, 2], [0, 1, 4, 2, 3], [0, 1, 4, 3, 2], [0, 2, 1, 3, 4], [0, 2, 1, 4, 3], [0, 2, 3, 1, 4], [0, 2, 3, 4, 1], [0, 2, 4, 1, 3], [0, 2, 4, 3, 1], [0, 3, 1, 2, 4], [0, 3, 1, 4, 2], [0, 3, 2, 1, 4], [0, 3, 2, 4, 1], [0, 3, 4, 1, 2], [0, 3, 4, 2, 1], [0, 4, 1, 2, 3], [0, 4, 1, 3, 2], [0, 4, 2, 1, 3], [0, 4, 2, 3, 1], [0, 4, 3, 1, 2], [0, 4, 3, 2, 1], [1, 0, 2, 3, 4], [1, 0, 2, 4, 3], [1, 0, 3, 2, 4], [1, 0, 3, 4, 2], [1, 0, 4, 2, 3], [1, 0, 4, 3, 2], [1, 2, 0, 3, 4], [1, 2, 0, 4, 3], [1, 2, 3, 0, 4], [1, 2, 3, 4, 0], [1, 2, 4, 0, 3], [1, 2, 4, 3, 0], [1, 3, 0, 2, 4], [1, 3, 0, 4, 2], [1, 3, 2, 0, 4], [1, 3, 2, 4, 0], [1, 3, 4, 0, 2], [1, 3, 4, 2, 0], [1, 4, 0, 2, 3], [1, 4, 0, 3, 2], [1, 4, 2, 0, 3], [1, 4, 2, 3, 0], [1, 4, 3, 0, 2], [1, 4, 3, 2, 0], [2, 0, 1, 3, 4], [2, 0, 1, 4, 3], [2, 0, 3, 1, 4], [2, 0, 3, 4, 1], [2, 0, 4, 1, 3], [2, 0, 4, 3, 1], [2, 1, 0, 3, 4], [2, 1, 0, 4, 3], [2, 1, 3, 0, 4], [2, 1, 3, 4, 0], [2, 1, 4, 0, 3], [2, 1, 4, 3, 0], [2, 3, 0, 1, 4], [2, 3, 0, 4, 1], [2, 3, 1, 0, 4], [2, 3, 1, 4, 0], [2, 3, 4, 0, 1], [2, 3, 4, 1, 0], [2, 4, 0, 1, 3], [2, 4, 0, 3, 1], [2, 4, 1, 0, 3], [2, 4, 1, 3, 0], [2, 4, 3, 0, 1], [2, 4, 3, 1, 0], [3, 0, 1, 2, 4], [3, 0, 1, 4, 2], [3, 0, 2, 1, 4], [3, 0, 2, 4, 1], [3, 0, 4, 1, 2], [3, 0, 4, 2, 1], [3, 1, 0, 2, 4], [3, 1, 0, 4, 2], [3, 1, 2, 0, 4], [3, 1, 2, 4, 0], [3, 1, 4, 0, 2], [3, 1, 4, 2, 0], [3, 2, 0, 1, 4], [3, 2, 0, 4, 1], [3, 2, 1, 0, 4], [3, 2, 1, 4, 0], [3, 2, 4, 0, 1], [3, 2, 4, 1, 0], [3, 4, 0, 1, 2], [3, 4, 0, 2, 1], [3, 4, 1, 0, 2], [3, 4, 1, 2, 0], [3, 4, 2, 0, 1], [3, 4, 2, 1, 0], [4, 0, 1, 2, 3], [4, 0, 1, 3, 2], [4, 0, 2, 1, 3], [4, 0, 2, 3, 1], [4, 0, 3, 1, 2], [4, 0, 3, 2, 1], [4, 1, 0, 2, 3], [4, 1, 0, 3, 2], [4, 1, 2, 0, 3], [4, 1, 2, 3, 0], [4, 1, 3, 0, 2], [4, 1, 3, 2, 0], [4, 2, 0, 1, 3], [4, 2, 0, 3, 1], [4, 2, 1, 0, 3], [4, 2, 1, 3, 0], [4, 2, 3, 0, 1], [4, 2, 3, 1, 0], [4, 3, 0, 1, 2], [4, 3, 0, 2, 1], [4, 3, 1, 0, 2], [4, 3, 1, 2, 0], [4, 3, 2, 0, 1], [4, 3, 2, 1, 0]
  ] """

  # Iterate over all possible fusion combinations
  for fusion_combination in Constants.fusion_combinations:    
    seed_index_delta = 0
    card_to_play = hand[fusion_combination[0]]

    if len(fusion_combination) > 1:
      # Fuse the result with the remaining cards in the combination
      for card_index in fusion_combination[1:]:
        (fusion_result,fusion_succeded) = find_fusion(card_to_play,hand[card_index])       
        if fusion_succeded:
          card_to_play = fusion_result
          seed_index_delta += Constants.anims_steps_adv['FUSION']
        
        elif can_card_be_equipped(card_to_play,hand[card_index]):
          card_to_play = equip_card(card_to_play,hand[card_index])
          seed_index_delta += Constants.anims_steps_adv['EQUIP']

        else:
          card_to_play = result_from_failed_fusion(card_to_play,hand[card_index])
          seed_index_delta += Constants.anims_steps_adv['DUMP']

    # Check if the resulting card has the highest attack
    if card_to_play.attack > max_attack:      
      max_attack = card_to_play.attack
      best_card = card_to_play
      best_fusion_combination = fusion_combination
      best_seed_index_delta = seed_index_delta
      new_hand = [x for x in hand if x not in fusion_combination]
  return best_card, best_fusion_combination, best_seed_index_delta, new_hand



def find_fusion(card1,card2):   
  fusion_succeded = False
  non_monster_card_types = """ 
  20: 'Magic',
  21: 'Trap',
  22: 'Ritual',
  23: 'Equip' """
  if card1.type < 20 and card2.type < 20: #both are monsters 
    result_id =  Constants.fusions.get(tuple(sorted((card1.cardID, card2.cardID)))) 
    if result_id is None:
      result = card2
    else: 
      result = get_card_data_from_card_ids([result_id])[0]
      fusion_succeded = True
    return result,fusion_succeded
  else:
    # To be implemented: fusion with magic/trap cards
    return card1,fusion_succeded


def add_equips(card,number_of_equips):
  result = copy.deepcopy(card)
  result.attack  += 500 * number_of_equips
  result.defense += 500 * number_of_equips
  return result

def is_card_monster_type(card):
  return card.type not in list(Constants.non_monster_card_types.keys())

def result_from_failed_fusion(card1,card2):
  if is_card_monster_type(card1) and is_card_monster_type(card2):
    return card2
  elif is_card_monster_type(card1) and not is_card_monster_type(card2): 
    return card1
  elif not is_card_monster_type(card1) and is_card_monster_type(card2): 
    return card2
  elif not is_card_monster_type(card1) and not is_card_monster_type(card2): 
    return card2


def field_has_positive_influence_on_card(card,field_type):
  return card.type in Constants.field_cards_positive_influence_on_types[field_type]

def field_has_negative_influence_on_card(card,field_type):
  return card.type in Constants.field_cards_negative_influence_on_types[field_type]


def apply_field_modifiers_to_card_copy(card,field_type):
  card_copy = copy.deepcopy(card)
  if field_has_positive_influence_on_card(card_copy,field_type):
    card_copy.attack += 500
    card_copy.defense += 500
  if field_has_negative_influence_on_card(card,field_type):     
    card_copy.attack -= 500
    card_copy.defense -= 500
  return card_copy

def is_guardian_star_strong_against(my_card, enemy_card):
  if(my_card.guardian_star == 'N/A'):
    return False
  else:
    return Constants.guardian_star_strong_against[my_card.guardian_star] == enemy_card.guardian_star

def is_guardian_star_weak_against(my_card, enemy_card):
  if(enemy_card.guardian_star == 'N/A'):
    return False
  else:
    return Constants.guardian_star_strong_against[enemy_card.guardian_star] == my_card.guardian_star

def exist_guardian_star_interaction(my_card, enemy_card):
  return is_guardian_star_weak_against(my_card, enemy_card) or is_guardian_star_strong_against(my_card, enemy_card)


def equip_card(card1,card2):
  result = None
  equip_card = None
  monster_card = None
  if is_card_monster_type(card2) and card1.type == Constants.non_monster_card_type_names['EQUIP']:
    equip_card = card1
    monster_card = card2
  elif is_card_monster_type(card1) and card2.type == Constants.non_monster_card_type_names['EQUIP']:
    equip_card = card2
    monster_card = card1
  
  if equip_card.cardID in Constants.card_equips[monster_card.cardID]:
    if equip_card.name == 'Megamorph':
      result = copy.deepcopy(monster_card)
      result.attack += 1000
      result.defense += 1000
    elif equip_card.name != 'Megamorph':
      result = copy.deepcopy(monster_card)
      result.attack += 500
      result.defense += 500 
  return result


def can_card_be_equipped(card1,card2):
  if is_card_monster_type(card1) and card2.type == Constants.non_monster_card_type_names['EQUIP']:
    return card2.cardID in Constants.card_equips[card1.cardID] 
  elif is_card_monster_type(card2) and card1.type == Constants.non_monster_card_type_names['EQUIP']:
    return card1.cardID in Constants.card_equips[card2.cardID]
  else:
    return False



def make_best_fusion_from_hand(hand_ids):
  hand = get_card_data_from_card_ids(hand_ids)
  best_card, best_fusion_combination, best_seed_index_delta, new_hand = get_best_fusion(hand)
  if len(best_fusion_combination) == 1:
    return 'Select card {}'.format(best_card.name)
  else:
    return 'Fuse cards {} to get result {}'.format([hand[i].name for i in best_fusion_combination], best_card.name)

def generate_main_phase_actions(hand,my_cards_in_field,initial_seed_index,field_type,enemy_card):
  """receives a hand, returns all possible fusions"""
  main_phase_actions = []
  for fusion_combination in Constants.fusion_combinations:
    main_phase_action_pair = generate_main_phase_action_pair(hand,fusion_combination,field_type,enemy_card)
    for main_phase_action in main_phase_action_pair:
      if main_phase_action is not None and main_phase_action not in main_phase_actions:
        main_phase_action.my_cards_in_field = my_cards_in_field[:] # we save a copy, not a reference, this is required
        main_phase_action.my_cards_in_field.append(main_phase_action.card_result)
        main_phase_action.seed_index = initial_seed_index + main_phase_action.seed_index_delta
        main_phase_actions.append(main_phase_action)
  return main_phase_actions

def generate_main_phase_action_pair(hand,fusion_combination,field_type,enemy_card):
  """receives a hand and a fusion combination e.g. [1,2,3], returns the result of that fusion in both GS"""
  main_phase_action_pair = []
  for guardian_star_option in range(2):
    card_to_play = hand[fusion_combination[0]]
    card_to_play.guardian_star = card_to_play.guardian_stars[guardian_star_option]
    seed_index_delta = 0
    if len(fusion_combination) == 1:    
      description  = 'Play card in position {} "{}" from hand in GS {} "{}"'.format(fusion_combination[0]+1,card_to_play.name,guardian_star_option+1,card_to_play.guardian_star)
      action_type = 'CARD SELECT'
    else:
      for card_index in fusion_combination[1:]:
        (fusion_result,fusion_succeded) = find_fusion(card_to_play,hand[card_index])       
        if fusion_succeded:
          card_to_play = fusion_result
          seed_index_delta += Constants.anims_steps_adv['FUSION']
        
        elif can_card_be_equipped(card_to_play,hand[card_index]):
          card_to_play = equip_card(card_to_play,hand[card_index])
          seed_index_delta += Constants.anims_steps_adv['EQUIP']

        else:
          card_to_play = result_from_failed_fusion(card_to_play,hand[card_index])
          seed_index_delta += Constants.anims_steps_adv['DUMP']
      card_to_play.guardian_star = card_to_play.guardian_stars[guardian_star_option]
      description  = 'Fuse cards in position {}. \nResult "{}" in GS {} "{}"'.format([x+1 for x in fusion_combination],card_to_play.name[:25],guardian_star_option+1,card_to_play.guardian_star)
      action_type = 'FUSION'
    card_to_play = apply_field_modifiers_to_card_copy(card_to_play,field_type)
    
    if guardian_star_option == 0 and is_card_monster_type(card_to_play):
      has_GS_interaction = exist_guardian_star_interaction(card_to_play,enemy_card)
      a_main_phase_action = Main_phase_action(card_to_play,seed_index_delta,description,action_type)
      main_phase_action_pair.append(a_main_phase_action)
    
    if guardian_star_option == 1 and is_card_monster_type(card_to_play):
      new_has_GS_interaction = exist_guardian_star_interaction(card_to_play,enemy_card)
      if new_has_GS_interaction != has_GS_interaction:
        a_main_phase_action = Main_phase_action(card_to_play,seed_index_delta,description,action_type)
        main_phase_action_pair.append(a_main_phase_action)
  return main_phase_action_pair


def is_enemy_card_destroyed_f(my_card, enemy_card,is_enemy_card_in_atk):
  attack = my_card.attack
  is_enemy_card_destroyed = False
  attack_difference = 0
  if is_enemy_card_in_atk:
    defense = enemy_card.attack
  else:
    defense = enemy_card.defense
  
  if is_guardian_star_strong_against(my_card, enemy_card):
    attack  += 500
  if is_guardian_star_weak_against(my_card, enemy_card):
    defense += 500
  
  if is_enemy_card_in_atk:
    is_enemy_card_destroyed = (attack >= defense)  
  else:
    is_enemy_card_destroyed = (attack > defense)

  attack_difference = attack - defense
  return (is_enemy_card_destroyed,attack_difference)


def adv_from_atk_to_atk_tie(current_seed_index,attack_type):
  if attack_type == 'Normal':
    current_seed_index += get_adv_steps_from_anim(current_seed_index,'SWIPE_DEF')
    current_seed_index += get_adv_steps_from_anim(current_seed_index,'BURN')
    current_seed_index += get_adv_steps_from_anim(current_seed_index,'SWIPE_DEF')
    current_seed_index += get_adv_steps_from_anim(current_seed_index,'BURN')
  elif attack_type == 'Quick3D':
    current_seed_index += get_adv_steps_from_anim(current_seed_index,'BURN_3D')
    current_seed_index += get_adv_steps_from_anim(current_seed_index,'BURN_3D')
  elif attack_type == 'SPAWN_3D':
    current_seed_index += get_adv_steps_from_anim(current_seed_index,'SPAWN_3D')
    current_seed_index += get_adv_steps_from_anim(current_seed_index,'BURN_3D')  
    current_seed_index += get_adv_steps_from_anim(current_seed_index,'BURN_3D')
  return current_seed_index

def adv_from_atk_to_atk_win(current_seed_index,card_attack_difference,attack_type): 
  if attack_type == 'Normal':
    if card_attack_difference >= 1000:
      current_seed_index += get_adv_steps_from_anim(current_seed_index,'SWIPE_ATK_HIGH')
    else:
      current_seed_index += get_adv_steps_from_anim(current_seed_index,'SWIPE_ATK_LOW')
    current_seed_index += get_adv_steps_from_anim(current_seed_index,'BURN')
  elif attack_type == 'Quick3D':
    current_seed_index += get_adv_steps_from_anim(current_seed_index,'BURN_3D')
  elif attack_type == 'SPAWN_3D':
    current_seed_index += get_adv_steps_from_anim(current_seed_index,'SPAWN_3D')
    current_seed_index += get_adv_steps_from_anim(current_seed_index,'BURN_3D')  
  return current_seed_index

def adv_from_atk_to_atk_lose(current_seed_index,card_attack_difference,attack_type):  
  if attack_type == 'Normal':
    current_seed_index += get_adv_steps_from_anim(current_seed_index,'LOSE_ATTACK')
    if card_attack_difference <= -1000:
      current_seed_index += get_adv_steps_from_anim(current_seed_index,'SWIPE_ATK_HIGH')
    else:
      current_seed_index += get_adv_steps_from_anim(current_seed_index,'SWIPE_ATK_LOW')
    current_seed_index += get_adv_steps_from_anim(current_seed_index,'BURN')
  elif attack_type == 'Quick3D':
    current_seed_index += get_adv_steps_from_anim(current_seed_index,'BURN_3D')
  elif attack_type == 'SPAWN_3D':
    current_seed_index += get_adv_steps_from_anim(current_seed_index,'SPAWN_3D')
    current_seed_index += get_adv_steps_from_anim(current_seed_index,'BURN_3D')
  return current_seed_index

def adv_from_atk_to_def_win(current_seed_index,attack_type):
  if attack_type == 'Normal':
    current_seed_index += get_adv_steps_from_anim(current_seed_index,'SWIPE_DEF')
    current_seed_index += get_adv_steps_from_anim(current_seed_index,'BURN')
  elif attack_type == 'Quick3D':
    current_seed_index += get_adv_steps_from_anim(current_seed_index,'BURN_3D')
  elif attack_type == 'SPAWN_3D':
    current_seed_index += get_adv_steps_from_anim(current_seed_index,'SPAWN_3D')
    current_seed_index += get_adv_steps_from_anim(current_seed_index,'BURN_3D')
  return current_seed_index 

def adv_from_atk_to_def_tie(current_seed_index,attack_type):  
  if attack_type == 'Normal':
    current_seed_index += get_adv_steps_from_anim(current_seed_index,'LOSE_ATTACK')
  elif attack_type == 'Quick3D':
    current_seed_index += 0 #no advancements
  elif attack_type == 'SPAWN_3D':
    current_seed_index += get_adv_steps_from_anim(current_seed_index,'SPAWN_3D')   
  return current_seed_index

def adv_from_atk_to_def_lose(current_seed_index,card_attack_difference,attack_type):  
  if attack_type == 'Normal':
    current_seed_index += get_adv_steps_from_anim(current_seed_index,'LOSE_ATTACK')
    if card_attack_difference <= -1000:
      current_seed_index += get_adv_steps_from_anim(current_seed_index,'DIRECT_HIGH')
    else:
      current_seed_index += get_adv_steps_from_anim(current_seed_index,'DIRECT_LOW')
  elif attack_type == 'Quick3D':
    current_seed_index += 0 #no advancements
  elif attack_type == 'SPAWN_3D':
    current_seed_index += get_adv_steps_from_anim(current_seed_index,'SPAWN_3D')    
  return current_seed_index

def seed_advancement_from_attack_animations(my_card, enemy_card,initial_seed_index,is_enemy_card_in_atk,attack_type):
  current_seed_index = initial_seed_index
  
  (is_enemy_card_destroyed,attack_difference) = is_enemy_card_destroyed_f(my_card, enemy_card,is_enemy_card_in_atk)
  #card_attack_difference = attack_difference(my_card, enemy_card,is_enemy_card_in_atk) #result of the attack
  if exist_guardian_star_interaction(my_card, enemy_card):
    current_seed_index += get_adv_steps_from_anim(initial_seed_index,'GS_ANIM')
  

  if is_enemy_card_in_atk:
    if is_enemy_card_destroyed: #my card won
      current_seed_index = adv_from_atk_to_atk_win(current_seed_index,attack_difference,attack_type)
    elif attack_difference == 0: #cards with same number both die
      current_seed_index = adv_from_atk_to_atk_tie(current_seed_index,attack_type)      
    else:
      current_seed_index = adv_from_atk_to_atk_lose(current_seed_index,attack_difference,attack_type)
  else: #enemy in defense
    if attack_difference > 0:
      current_seed_index = adv_from_atk_to_def_win(current_seed_index,attack_type)      
    elif attack_difference == 0:
      current_seed_index = adv_from_atk_to_def_tie(current_seed_index,attack_type)
    else:
      current_seed_index = adv_from_atk_to_def_lose(current_seed_index,attack_difference,attack_type)

  return current_seed_index-initial_seed_index



def create_action_from_my_card_attack_to_enemy_card(card_index,my_card,enemy_card,attack_order_seed,is_enemy_card_in_atk,attack_type):
  new_battle_phase_action = Battle_phase_action() 
  new_battle_phase_action.description = 'ATK in mode "{}" with card in position {} "{}" to enemy card'.format(attack_type,card_index+1,my_card.name)
  new_battle_phase_action.action_type = attack_type
  new_battle_phase_action.seed_index_delta = seed_advancement_from_attack_animations(my_card,enemy_card,attack_order_seed,is_enemy_card_in_atk,attack_type)
  new_battle_phase_action.current_seed_index = attack_order_seed + new_battle_phase_action.seed_index_delta
  return new_battle_phase_action

def create_action_from_my_card_attack_to_enemy_LP(card_index,my_card,attack_order_seed):
  new_battle_phase_action = Battle_phase_action() 
  new_battle_phase_action.description = 'ATK with card in position {} "{}" to enemy LP'.format(card_index+1,my_card.name)
  new_battle_phase_action.action_type = 'DIRECT ATK'
  if my_card.attack >= 1000:
    new_battle_phase_action.seed_index_delta = get_adv_steps_from_anim(0,'DIRECT_HIGH')
  else:
    new_battle_phase_action.seed_index_delta = get_adv_steps_from_anim(0,'DIRECT_LOW')
  new_battle_phase_action.current_seed_index = attack_order_seed + new_battle_phase_action.seed_index_delta   
  return new_battle_phase_action


def create_attack_combination(attack_order,my_cards,enemy_card,attack_order_seed,enemy_LP,is_enemy_card_in_atk,attack_type):
  attack_combination = []
  enemy_card_destroyed = False
  for card_index in attack_order:
    if enemy_LP <= 0:
      break
  
    my_card = my_cards[card_index]
    if not enemy_card_destroyed:
      new_battle_phase_action = create_action_from_my_card_attack_to_enemy_card(card_index,my_card,enemy_card,attack_order_seed,is_enemy_card_in_atk,attack_type)
      (enemy_card_destroyed,attack_difference) = is_enemy_card_destroyed_f(my_card,enemy_card,is_enemy_card_in_atk)
      if is_enemy_card_in_atk:
        enemy_LP -= attack_difference
    else:
      new_battle_phase_action = create_action_from_my_card_attack_to_enemy_LP(card_index,my_card,attack_order_seed)       
      enemy_LP -= my_card.attack
    attack_order_seed += new_battle_phase_action.seed_index_delta
    #TODO create a class called Attack_combination that has a specific seed index delta, and only add to the list the attack combinations that are not in that list already
    attack_combination.append(new_battle_phase_action)
  is_enemy_dead = enemy_LP<=0
  return is_enemy_dead,attack_combination
  
def generate_attack_combinations_from_cards_in_field(enemy_card,remaining_enemy_LP,main_phase_action,is_enemy_card_in_atk,attack_type):
  attack_orders = list(permutations(range(len(main_phase_action.my_cards_in_field)))) 
  attack_combinations = []
  for i,attack_order in enumerate(attack_orders):
    is_enemy_dead,attack_combination = create_attack_combination(attack_order,main_phase_action.my_cards_in_field,enemy_card,main_phase_action.seed_index,remaining_enemy_LP,is_enemy_card_in_atk,attack_type)
    if is_enemy_dead:
      attack_combinations.append(attack_combination)  
  return attack_combinations

def calculate_duel_rank(num_fusions,num_effectives,num_facedowns,num_magics,num_equips,num_traps,cards_used,num_turns,num_defensive_wins,remaining_lp):
  duel_rank_points = 52 # 50 base + 2 for Total Annihilation victory condition
  duel_rank_points += Constants.duel_rank_points_remaining_LP[remaining_lp]
  # Cards Used
  if 0 <= cards_used <= 8:
    duel_rank_points += 15
  elif 9 <= cards_used <= 12:
    duel_rank_points += 12
  elif 13 <= cards_used <= 32:
    duel_rank_points += 0
  elif 33 <= cards_used <= 36:
    duel_rank_points += -5
  elif 37 <= cards_used <= 40:
    duel_rank_points += -7

  # Turns
  if 0 <= num_turns <= 4:
      duel_rank_points += 12
  elif 5 <= num_turns <= 8:
      duel_rank_points += 8
  elif 9 <= num_turns <= 28:
      duel_rank_points += 0
  elif 29 <= num_turns <= 32:
      duel_rank_points += -8
  elif 33 <= num_turns <= 36:
      duel_rank_points += -12

  # Effective Attacks
  if 0 <= num_effectives <= 1:
      duel_rank_points += 4
  elif 2 <= num_effectives <= 3:
      duel_rank_points += 2
  elif 4 <= num_effectives <= 9:
      duel_rank_points += 0
  elif 10 <= num_effectives <= 19:
      duel_rank_points += -2
  elif 20 <= num_effectives <= 160:
      duel_rank_points += -4

  # Defensive Wins
  if 0 <= num_defensive_wins <= 1:
      duel_rank_points += 0
  elif 2 <= num_defensive_wins <= 5:
      duel_rank_points += -10
  elif 6 <= num_defensive_wins <= 9:
      duel_rank_points += -20
  elif 10 <= num_defensive_wins <= 14:
      duel_rank_points += -30
  elif 15 <= num_defensive_wins <= 180:
      duel_rank_points += -40

  # Face-Down Plays
  if num_facedowns == 0:
      duel_rank_points += 0
  elif 1 <= num_facedowns <= 10:
      duel_rank_points += -2
  elif 11 <= num_facedowns <= 20:
      duel_rank_points += -4
  elif 21 <= num_facedowns <= 30:
      duel_rank_points += -6
  elif 31 <= num_facedowns <= 36:
      duel_rank_points += -8

  # Fusions
  if num_fusions == 0:
      duel_rank_points += 4
  elif 1 <= num_fusions <= 4:
      duel_rank_points += 0
  elif 5 <= num_fusions <= 9:
      duel_rank_points += -4
  elif 10 <= num_fusions <= 14:
      duel_rank_points += -8
  elif num_fusions >= 15:
      duel_rank_points += -12

  # Equips
  if num_equips == 0:
      duel_rank_points += 4
  elif 1 <= num_equips <= 4:
      duel_rank_points += 0
  elif 5 <= num_equips <= 9:
      duel_rank_points += -4
  elif 10 <= num_equips <= 14:
      duel_rank_points += -8
  elif num_equips >= 15:
      duel_rank_points += -12

  # Magics
  if num_magics == 0:
      duel_rank_points += 2
  elif 1 <= num_magics <= 3:
      duel_rank_points += -4
  elif 4 <= num_magics <= 6:
      duel_rank_points += -8
  elif 7 <= num_magics <= 9:
      duel_rank_points += -12
  elif 10 <= num_magics <= 36:
      duel_rank_points += -16

  # Trigger Trap
  if num_traps == 0:
      duel_rank_points += 2
  elif 1 <= num_traps <= 2:
      duel_rank_points += -8
  elif 3 <= num_traps <= 4:
      duel_rank_points += -16
  elif 5 <= num_traps <= 6:
      duel_rank_points += -24
  elif 7 <= num_traps <= 36:
      duel_rank_points += -32

  if duel_rank_points >= 80:
      duel_rank =  "SA Pow"
  elif 20 <= duel_rank_points <= 79:
      duel_rank = "BCD"
  else:
      duel_rank = "SA Tech"
  return (duel_rank_points,duel_rank)
  
#### FRONT END FUNCTIONS ####
@st.cache_data
def st_read_pool(opponent_name, battle_rank):
  return read_pool(opponent_name, battle_rank)

  
     

