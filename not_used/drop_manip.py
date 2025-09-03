from helper_functions import *
from drop_manip_classes_and_constants import *

def last_turn(enemy, initial_seed_index): 
  plays = []
  initial_seed_index,hand,my_cards_in_field,enemy_card,remaining_enemy_LP,battle_rank,is_enemy_card_in_atk,field_type = get_initial_input_values(initial_seed_index)
  Constants.load_dbs_to_memory(initial_seed_index,enemy,battle_rank)

  # Main Phase
  main_phase_actions = generate_main_phase_actions(hand,my_cards_in_field,initial_seed_index,field_type,enemy_card)
  print('number of possible card fusions with different results:', len(main_phase_actions))
  
  #Battle Phase
  attack_types = ['Normal','Quick3D','SPAWN_3D']
  for attack_type in attack_types:
    for i,main_phase_action in enumerate(main_phase_actions):
      possible_battle_phase_actions = generate_atack_combinations_from_cards_in_field(enemy_card,remaining_enemy_LP,main_phase_action,is_enemy_card_in_atk,attack_type)
      for battle_phase_actions in possible_battle_phase_actions:
        new_play = Play(initial_seed_index)
        new_play.main_phase_action = main_phase_action
        new_play.battle_phase_actions = battle_phase_actions    
        new_play.calculate_drop(enemy)
        if new_play not in plays:
          plays.append(new_play)

  plays.sort(key=lambda x: x.drop_card.cardID)
  print_possible_drops(plays)
  while True:
    desired_drop_card_id = int(input('enter desired drop card id from the options above or 0 to go back: ').strip())
    if desired_drop_card_id == 0:
      return 1
    play = get_play_from_drop_id(plays,desired_drop_card_id)
    if play is not None:
      print_play(play)
    else:
      print('no actions found for that card')