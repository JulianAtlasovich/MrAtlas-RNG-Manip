from tabulate import tabulate
from helper_functions_seed_tracker import *
from drop_manip import *

def seed_tracker():
  player_deck_shuffled = []
  opp_deck = []
  pos_seed_indexes = []
  opp_cards_to_play_order = []

  print_opponents()
  opponent_id = int(input('enter opponent id: ')) 
  opponent_name = get_opponent_name_by_id(opponent_id)
  opp_pool = read_pool(opponent_name, PoolType.DECK.value)
  
  seed_index_input = input('enter seed index if you are in the last turn or press enter if you are not: ')
  if seed_index_input.isnumeric():
    last_turn(opponent_name,int(seed_index_input))
    return

  my_deck,hand = read_deck_and_hand()
  
  no_field_type = True
  if opponent_id in Constants.opponents_with_special_field_type.keys():
    print(tabulate([['1','Free duel (no field type)'],['2','Campaing (special field type)']],headers=['duel option','description']))
    no_field_type = int(input('enter the duel option: ').strip())
    no_field_type = True if no_field_type == 1 else False
  
  possible_seed_indexes_pre_shuffle = get_initial_possible_seeds(my_deck,hand)
  print_remaining_possible_seeds(possible_seed_indexes_pre_shuffle)
  if len(possible_seed_indexes_pre_shuffle) == 0:
    return
  
  for a_seed_index in possible_seed_indexes_pre_shuffle:
    poss_player_deck_shuffled = create_player_deck(my_deck,a_seed_index)
    poss_player_deck_shuffled = get_card_data_from_card_ids(poss_player_deck_shuffled)
    player_deck_shuffled.append(poss_player_deck_shuffled)
    (poss_opp_deck, poss_seed_index) = create_opponent_deck(opp_pool,a_seed_index)
    pos_seed_indexes.append(poss_seed_index)
    opp_deck.append(poss_opp_deck)
    opp_cards_to_play_order.append(generate_opponents_cards_to_play_order(opponent_id,poss_opp_deck,no_field_type))

  initial_setup(pos_seed_indexes[0]) 
  last_advancement = 0
  while True:
    my_input = input('enter an event id or command: ').strip()
    if my_input.isnumeric():
      if my_input != '0':
        event = get_event_by_id(int(my_input))
        for i,a_seed_index in enumerate(pos_seed_indexes):
          pos_seed_indexes[i] += get_seed_advancement(a_seed_index,event)
          last_advancement = get_seed_advancement(a_seed_index,event)
        print_last_event(event.name,pos_seed_indexes)       
      else:
        for i,a_seed_index in enumerate(pos_seed_indexes):
          pos_seed_indexes[i] -= last_advancement
        print_last_event('UNDO',pos_seed_indexes)
    else:
      if my_input=='+p':
        add_player_card(player_deck_shuffled,opp_deck,opp_cards_to_play_order,pos_seed_indexes)       
      if my_input=='+o':
        add_opponent_card(player_deck_shuffled,opp_deck,opp_cards_to_play_order,pos_seed_indexes)
      if my_input=='sp':
        show_player_deck(player_deck_shuffled,pos_seed_indexes)
      if my_input=='so':
        show_opponents_deck(opp_cards_to_play_order,pos_seed_indexes)
      if my_input=='lt':
        returned = last_turn(opponent_name,pos_seed_indexes[0])
        if returned is None:
          break
        print_remaining_possible_seeds(pos_seed_indexes)

if __name__ == '__main__':
  seed_tracker()