import streamlit as st
import pandas as pd
import sqlite3
from drop_manip_classes_and_constants import *
from helper_functions_seed_tracker import *
from db_queries import *
st.set_page_config(layout="wide")
st.title("Atlas of RNG Manipulation for Yu-Gi-Oh! Forbidden Memories")

# Search Bar
with st.expander("Card Search"):
    search_query = st.text_input("Search for a card (by name or ID):")
    if search_query:
        try:
            if search_query.isdigit():  # Check if the input is a number
                card_id = int(search_query)
                df_search = get_cards_by_ids([card_id])
            else:  # Otherwise, treat it as a name
                df_search = search_card_by_name(search_query)
                df_search = get_cards_by_ids(df_search['ID'].tolist())
            
            if not df_search.empty:
                st.dataframe(df_search, use_container_width=True)
            else:
                st.write("No results found.")
        except Exception as e:
            st.error(f"An error occurred: {e}")

# Section 1
with st.expander("1 Your Deck"):
    player_card_ids_in_deck_input = st.text_input("Enter comma-separated Card IDs:", value=",".join(map(str, range(1, 41))))
    if player_card_ids_in_deck_input:
        player_card_ids_in_deck = list(map(int,player_card_ids_in_deck_input.split(",")))
        player_deck_df = get_cards_by_ids(player_card_ids_in_deck)
        st.dataframe(player_deck_df, use_container_width=True)

# Section 2
with st.expander("2 Identify the seed"):
    duelists = get_list_of_opponent_names()
    opponent_name = st.selectbox("Select the opponent:",options=duelists)
    hand_input = st.text_input("Enter comma-separated Card IDs of your hand:")
    enemy_cards_input = st.text_input("Enter comma-separated Card IDs of the opponent cards:")
    possible_seed_indexes = None
    opp_pool = read_pool(opponent_name, PoolType.DECK.value)
    hand_ids = []

    if hand_input:
        hand_ids = list(map(int,hand_input.split(",")))
        possible_seed_indexes = get_initial_possible_seeds(player_card_ids_in_deck,hand_ids)                
    opponent_id = get_opponent_id_by_name(opponent_name)
    if enemy_cards_input and possible_seed_indexes is not None and opponent_name is not None:        
        enemy_cards = list(map(int, enemy_cards_input.split(",")))      
        for possible_seed_index in possible_seed_indexes[:]: #iterate over a copy of the list to allow removal during iteration
            (poss_opp_deck, _) = create_opponent_deck(opp_pool, possible_seed_index)            
            opp_cards_to_play_order = generate_opponents_cards_to_play_order(opponent_id,poss_opp_deck,True) #3rd param is no_field_type
            for i,enemy_card in enumerate(enemy_cards):
                if enemy_card != opp_cards_to_play_order[i].cardID:
                    possible_seed_indexes.remove(possible_seed_index)
                    break
    
    if possible_seed_indexes is not None and len(possible_seed_indexes)>1:
        st.write('add more player or opponent cards to identify the initial seed index uniquely')
        st.write('possible seed indexes: ',','.join(list(map(str,possible_seed_indexes))))

    initial_seed_index = None
    if possible_seed_indexes is not None and len(possible_seed_indexes)==1:
        initial_seed_index = possible_seed_indexes[0]
        st.write('initial seed index: ',initial_seed_index)


# Section 3
with st.expander("3: Player and Opponent Deck"):
    st.write(possible_seed_indexes)
    if possible_seed_indexes is None or len(possible_seed_indexes) == 0:
        st.write("Please enter your hand to see your's and opponent's shuffled deck.")

    if possible_seed_indexes is not None and len(possible_seed_indexes) > 1:  # Initial seed index not yet identified, multiple options
        st.write('Add more cards to uniquely identify the initial seed index, possible cards at each position will be displayed below.')
        list_of_possible_opp_decks = []
        list_of_possible_player_decks = []

        # Iterate over all possible seed indexes and save all possible opponent decks
        for possible_seed_index in possible_seed_indexes:
            (poss_opp_deck, _) = create_opponent_deck(opp_pool, possible_seed_index)
            opp_cards_to_play_order = generate_opponents_cards_to_play_order(opponent_id, poss_opp_deck, True)  # 3rd param is no_field_type
            list_of_possible_opp_decks.append([card.cardID for card in opp_cards_to_play_order])
            player_deck_shuffled = create_player_deck(player_card_ids_in_deck, possible_seed_index)
            list_of_possible_player_decks.append(player_deck_shuffled)

        # Combine all possible player decks into a single list with concatenated IDs for each position
        combined_player_deck = []
        for i in range(len(list_of_possible_player_decks[0])):  # Iterate over positions in the deck
            ids_at_position = set(deck[i] for deck in list_of_possible_player_decks)  # Collect IDs at this position
            combined_player_deck.append(" | ".join(map(str, ids_at_position)))  # Concatenate IDs with '|'
        st.write("Possible Player cards at each position (IDs separated by '|'):")
        df_combined_player_deck = pd.DataFrame(combined_player_deck, columns=["Card IDs"])
        st.dataframe(df_combined_player_deck, use_container_width=True)

        # Combine all possible opponent decks into a single list with concatenated IDs for each position
        combined_opp_deck = []
        for i in range(len(list_of_possible_opp_decks[0])):  # Iterate over positions in the deck
            ids_at_position = set(deck[i] for deck in list_of_possible_opp_decks)  # Collect IDs at this position
            combined_opp_deck.append(" | ".join(map(str, ids_at_position)))  # Concatenate IDs with '|'
        st.write("Possible Opponent cards at each position (IDs separated by '|'):")
        df_combined_opp_deck = pd.DataFrame(combined_opp_deck, columns=["Card IDs"])
        st.dataframe(df_combined_opp_deck, use_container_width=True)

    if initial_seed_index is not None:  # Initial seed index identified
        (poss_opp_deck, _) = create_opponent_deck(opp_pool, initial_seed_index)
        opp_cards_to_play_order = generate_opponents_cards_to_play_order(opponent_id, poss_opp_deck, True)  # 3rd param is no_field_type
        st.write("Player's deck order:")
        player_deck_shuffled = create_player_deck(player_card_ids_in_deck, initial_seed_index)
        df_player_deck_shuffled = get_cards_by_ids(player_deck_shuffled)
        st.dataframe(df_player_deck_shuffled, use_container_width=True)
        st.write("Opponent's deck order:")
        df_opp_deck = get_cards_by_ids([card.cardID for card in opp_cards_to_play_order])
        st.dataframe(df_opp_deck, use_container_width=True)


# Section 4
with st.expander("4: Duel Events"):
    #st.write("List of Possible Events:")
    #df_events = pd.DataFrame([{"Event ID": event.event_id, "Name": event.name, "Seed Advancements": event.seed_advancements , "Description": event.description} for event in Constants.events])
    #df_events = df_events[df_events["Event ID"] != 0] # Exclude the initial deck shuffling event from display
    #st.dataframe(df_events, use_container_width=True)
    event_history = []
    main_phase_actions = [] 
    if len(hand_ids) >= 5:
        hand = get_card_data_from_card_ids(hand_ids)
        main_phase_actions.append(generate_first_main_phase_action(hand[:5], initial_seed_index,opp_pool))    
        main_phase_action_1 = main_phase_actions[0]
        st.write("Actions History:")
       
        df_action_history = pd.DataFrame([{
            "seed_index": main_phase_action_1.seed_index,
            "description": main_phase_action_1.description,
            "seed_index_delta": main_phase_action_1.seed_index_delta,
            "card_result": main_phase_action_1.card_result.name,
            "guardian_star": main_phase_action_1.card_result.guardian_star,
            "action_type": main_phase_action_1.action_type,
            "new_hand": str([card.name for card in main_phase_action_1.new_hand])
        }]) 
        st.dataframe(df_action_history, use_container_width=True)

        #print(main_phase_action_1.events)
    st.write("Event History:")
    event_history = main_phase_action_1.events if len(main_phase_actions)>0 else []
    if len(event_history) > 0 and initial_seed_index is not None:
        
        df_event_history = pd.DataFrame([{
            "Event ID": event.event_id,
            "Name": event.name,
            "Initial Seed Index": event.initial_seed_index,
            "New Seed Index": event.new_seed_index
        } for event in event_history])
        st.dataframe(df_event_history, use_container_width=True)

    if len(event_history) > 0 and initial_seed_index is None:
        df_event_history = pd.DataFrame([{
            "Event ID": event.event_id,
            "Name": event.name
        } for event in event_history])
        st.dataframe(df_event_history, use_container_width=True) 

#Maybe I can add a section here with a Rank Calculator

# Section 5
with st.expander("Last Hand"):
    #initial_seed_index,
    hand_input = st.text_input("Enter Card IDs in your hand:")
    
    #need to check if they have equips and their GS
    my_cards_in_field_input = st.text_input("Enter Card IDs of your cards in the field:"),
    
    #need to check if it's in atk or def
    enemy_card = st.text_input("Card ID of the opponent's card in the field:"),
    
    remaining_enemy_LP = st.text_input("Opponent remaining Life Points:"),
    #is_enemy_card_in_atk,

    #BATTLE_RANK_OPTIONS = {'SA Pow': 1, 'BCD': 2, 'SA Tec': 3}
    #battle_rank = st.selectbox("Select the duel battle rank:", options=BATTLE_RANK_OPTIONS.keys(), format_func=lambda x:BATTLE_RANK_OPTIONS[ x ]),
    
    #field_type = 


    #  main_phase_actions = generate_main_phase_actions(hand,my_cards_in_field,initial_seed_index,field_type,enemy_card)
    #print('number of possible card fusions with different results:', len(main_phase_actions))
    a = """ 
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
            plays.append(new_play) """