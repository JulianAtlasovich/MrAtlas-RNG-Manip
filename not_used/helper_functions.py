
from drop_manip_classes_and_constants import *
from fm_lib import *
from read_dbs import *
from rng_core import *
from itertools import permutations
from datetime import datetime
from tabulate import tabulate
import copy

def field_has_positive_influence_on_card(card,field_type):
  return card.type in Constants.field_cards_positive_influence_on_types[field_type]

def field_has_negative_influence_on_card(card,field_type):
  return card.type in Constants.field_cards_negative_influence_on_types[field_type]

def apply_field_modifiers_to_cards(cards,field_type):
  for card in cards:
    if field_has_positive_influence_on_card(card,field_type):
      card.attack += 500
      card.defense += 500
    if field_has_negative_influence_on_card(card,field_type):     
      card.attack -= 500
      card.defense -= 500

def apply_field_modifiers_to_card_copy(card,field_type):
  card_copy = copy.deepcopy(card)
  if field_has_positive_influence_on_card(card_copy,field_type):
    card_copy.attack += 500
    card_copy.defense += 500
  if field_has_negative_influence_on_card(card,field_type):     
    card_copy.attack -= 500
    card_copy.defense -= 500
  return card_copy


def add_equips(card,number_of_equips):
  result = copy.deepcopy(card)
  result.attack  += 500 * number_of_equips
  result.defense += 500 * number_of_equips
  return result

def get_initial_input_values(initial_seed_index):
  if initial_seed_index is None: 
    initial_seed_index = int(input('initial seed index: ').strip())
  
  hand_ids = list(map(int,input('enter ids of cards in your hand in order separated by space: ').strip().split(' ')))
  hand = get_card_data_from_card_ids(hand_ids)
  
  my_cards_in_field = []
  field_pos = 1
  card_id_in_field =  int(input('enter id of card in position 1 in the field:  ').strip())
  while card_id_in_field != 0:
    card_in_field = get_card_data_from_card_ids([card_id_in_field])[0]
    number_of_equips = int(input('how many times was that card equipped, megamorph counts as 2. (original atk {}): '.format(card_in_field.attack)))
    card_in_field = add_equips(card_in_field,number_of_equips)
    guardian_star_selection = int(input('enter the guardian star of the card. 1 for "{}", or 2 for "{}": '.format(card_in_field.guardian_stars[0],card_in_field.guardian_stars[1])))
    card_in_field.guardian_star = card_in_field.guardian_stars[guardian_star_selection-1]
    my_cards_in_field.append(card_in_field)
    field_pos += 1
    card_id_in_field = int(input('enter ID of card in position {} in the field, or enter 0 if there are no more cards: '.format(field_pos)))

  enemy_card = int(input('enter opponent card ID in the field: ').strip())
  enemy_card = get_card_data_from_card_ids([enemy_card])[0]
  is_enemy_card_in_atk = int(input('enter 1 if opponents cards is in DEF mode or 2 if it is in ATK: ').strip())
  is_enemy_card_in_atk = False if is_enemy_card_in_atk == 1 else True

  remaining_enemy_LP = int(input('enter opponent life points remaining: ').strip())
  battle_rank = int(input('enter battle rank option (1: SAPow, 2: BCD, 3: SATec): ').strip())
  
  print(tabulate(Constants.field_types,headers=['field type ID','name']))
  field_type = int(input('enter the current field type ID: ').strip())
  apply_field_modifiers_to_cards(my_cards_in_field,field_type)
  apply_field_modifiers_to_cards([enemy_card],field_type)
  return initial_seed_index,hand,my_cards_in_field,enemy_card,remaining_enemy_LP,battle_rank,is_enemy_card_in_atk,field_type

def get_adv_steps_from_anim(index,anim_name):
  """return the new seed and index after an animation (fixed or variable)"""  
  if anim_name != 'BURN' and anim_name != 'GS_ANIM' and anim_name != 'BURN_3D':
    steps_to_adv = Constants.anims_steps_adv[anim_name] 
  else:
    steps_to_adv = get_variable_anim_steps(index,anim_name)
  return steps_to_adv 
  
def get_variable_anim_steps(index,anim_name):
  AdvanceSize = Constants.variable_anim_steps[anim_name][index]
  return AdvanceSize

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

def can_card_be_equipped(card1,card2):
  return card2.cardID in Constants.equips[card1.cardID] or card1.cardID in Constants.equips[card2.cardID]

def equip_card(card1,card2):
  result = None
  equip_card = None
  monster_card = None
  if card1.type == Constants.non_monster_card_type_names['EQUIP'] and is_card_monster_type(card2):
    equip_card = card1
    monster_card = card2
  elif card2.type == Constants.non_monster_card_type_names['EQUIP'] and is_card_monster_type(card1):
    equip_card = card2
    monster_card = card1
  if equip_card is None or monster_card is None:
    return None

  if monster_card.cardID in Constants.equips[equip_card.cardID]:
    if equip_card.name == 'Megamorph':
      result = copy.deepcopy(monster_card)
      result.attack += 1000
      result.defense += 1000
    elif equip_card.name != 'Megamorph':
      result = copy.deepcopy(monster_card)
      result.attack += 500
      result.defense += 500 
  return result

  
def generate_atack_combinations_from_cards_in_field(enemy_card,remaining_enemy_LP,main_phase_action,is_enemy_card_in_atk,attack_type):
  attack_orders = list(permutations(range(len(main_phase_action.my_cards_in_field)))) 
  attack_combinations = []
  for attack_order in attack_orders:
    is_enemy_dead,attack_combination = create_attack_combination(attack_order,main_phase_action.my_cards_in_field,enemy_card,main_phase_action.seed_index,remaining_enemy_LP,is_enemy_card_in_atk,attack_type)
    if is_enemy_dead:
      attack_combinations.append(attack_combination)  
  return attack_combinations

    

def print_list(list):
  for e in list:
    print(e)

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
  card_attack_difference = attack_difference(my_card, enemy_card,is_enemy_card_in_atk) #result of the attack
  if exist_guardian_star_interaction(my_card, enemy_card):
    current_seed_index += get_adv_steps_from_anim(initial_seed_index,'GS_ANIM')
  
  if is_enemy_card_in_atk:
    if card_attack_difference > 0: #my card won
      current_seed_index = adv_from_atk_to_atk_win(current_seed_index,card_attack_difference,attack_type)
    elif card_attack_difference == 0: #cards with same number both die
      current_seed_index = adv_from_atk_to_atk_tie(current_seed_index,attack_type)      
    else:
      current_seed_index = adv_from_atk_to_atk_lose(current_seed_index,card_attack_difference,attack_type)
  else:
    if card_attack_difference > 0:
      current_seed_index = adv_from_atk_to_def_win(current_seed_index,attack_type)      
    elif card_attack_difference == 0:
      current_seed_index = adv_from_atk_to_def_tie(current_seed_index,attack_type)
    else:
      current_seed_index = adv_from_atk_to_def_lose(current_seed_index,card_attack_difference,attack_type)

  return current_seed_index-initial_seed_index

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

def is_card_stronger_than(my_card, enemy_card,is_enemy_card_in_atk):
  attack = my_card.attack
  if is_enemy_card_in_atk:
    defense = enemy_card.attack
  else:
    defense = enemy_card.defense
  if is_guardian_star_strong_against(my_card, enemy_card):
    attack  += 500
  if is_guardian_star_weak_against(my_card, enemy_card):
    defense += 500
  return attack > defense

def is_enemy_card_destroyed(my_card, enemy_card,is_enemy_card_in_atk):
  attack = my_card.attack
  if is_enemy_card_in_atk:
    defense = enemy_card.attack
  else:
    defense = enemy_card.defense
  if is_guardian_star_strong_against(my_card, enemy_card):
    attack  += 500
  if is_guardian_star_weak_against(my_card, enemy_card):
    defense += 500
  if is_enemy_card_in_atk:
    return attack >= defense
  else:
    return attack > defense

def attack_difference(my_card, enemy_card,is_enemy_card_in_atk):
  attack  = my_card.attack
  if is_enemy_card_in_atk:
    defense = enemy_card.attack
  else:
    defense = enemy_card.defense
  if is_guardian_star_strong_against(my_card, enemy_card):
    attack  += 500
  if is_guardian_star_weak_against(my_card, enemy_card):
    defense += 500
  return attack - defense

def create_action_from_my_card_attack_to_enemy_card(card_index,my_card,enemy_card,attack_order_seed,is_enemy_card_in_atk,attack_type):
  new_battle_phase_action = Battle_phase_action() 
  new_battle_phase_action.description = 'ATK with card in position {} "{}" to enemy card'.format(card_index+1,my_card.name)
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

def update_enemy_LP_after_attack(enemy_LP,my_card,enemy_card,is_enemy_card_in_atk):
  if is_enemy_card_in_atk and is_card_stronger_than(my_card, enemy_card,is_enemy_card_in_atk):
    enemy_LP -= attack_difference(my_card,enemy_card,is_enemy_card_in_atk)
  return enemy_LP


def create_attack_combination(attack_order,my_cards,enemy_card,attack_order_seed,enemy_LP,is_enemy_card_in_atk,attack_type):
  attack_combination = []
  enemy_card_destroyed = False
  for card_index in attack_order:
    if enemy_LP <= 0:
      pass
    else: 
      attack_seed_delta = 0
      my_card = my_cards[card_index]
      if not enemy_card_destroyed:
        new_battle_phase_action = create_action_from_my_card_attack_to_enemy_card(card_index,my_card,enemy_card,attack_order_seed,is_enemy_card_in_atk,attack_type)
        enemy_card_destroyed = is_enemy_card_destroyed(my_card,enemy_card,is_enemy_card_in_atk)
        enemy_LP = update_enemy_LP_after_attack(enemy_LP,my_card,enemy_card,is_enemy_card_in_atk)
      else:
        new_battle_phase_action = create_action_from_my_card_attack_to_enemy_LP(card_index,my_card,attack_order_seed)       
        enemy_LP -= my_card.attack
      attack_order_seed += new_battle_phase_action.seed_index_delta
      attack_combination.append(new_battle_phase_action)
  is_enemy_dead = enemy_LP<=0
  return is_enemy_dead,attack_combination

def print_possible_drops(plays):
  possible_drops = []
  for play in plays:
    possible_drops.append([play.drop_card.cardID,play.drop_card.name,Constants.card_types[play.drop_card.type],play.drop_card.attack,play.drop_card.defense])
  print(tabulate(possible_drops,headers=['drop card id','card name','type','attack','defense']))

def get_play_from_drop_id(plays,drop_id):
  result = None
  for play in plays:
    if play.drop_card.cardID == drop_id:
      result = play
  return result     

def print_play(play):
  actions = []
  action_index = 1
  actions.append([action_index,play.main_phase_action.action_type,play.main_phase_action.description,play.main_phase_action.seed_index])
  for battle_action in play.battle_phase_actions:
    action_index+=1
    actions.append([action_index,battle_action.action_type,battle_action.description,battle_action.current_seed_index])
  actions.append([None,'DROP',play.drop_card.name,play.final_seed_index])    
  print(tabulate(actions,headers=['action#','action type','description','seed index']))  
 