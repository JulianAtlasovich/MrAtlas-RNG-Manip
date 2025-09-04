import streamlit as st
import pandas as pd
import sqlite3
from drop_manip_classes_and_constants import *
from helper_functions_seed_tracker import *
from db_queries import *
from datetime import datetime
from streamlit_local_storage import LocalStorage

st.set_page_config(layout="wide")
st.title("The Atlas of RNG Manipulation for Yu-Gi-Oh! Forbidden Memories")
localS = LocalStorage()

# Search Bar
with st.expander("Tool Guide"):
    st.info("""
    This tool helps you manipulate the RNG (Random Number Generator) in Yu-Gi-Oh! Forbidden Memories.

    Restrictions:
    - You :red[MUST] restart your console before each duel.
    - You must destroy every card the opponent plays on the next turn.
    - You must leave an empty space in the field for the last turn.
    - You must enter each duel using the default ID card sorting
    - You must play all your monsters face up. (Doesn't apply to magic,traps,equips)
    - You can't use any magic card that is not a field card. No removal cards (e.g. "Dark Hole", "Raigeki", "Dragon Capture Jar")
    - It's recommended to minimize the number of repeated cards in your deck, to identify the seed faster. Otherwise you'll need to input more cards to identify it
    - It's recommended to have one monster with <= 999 ATK in your hand on the last turn. This increases the chances of a successful RNG manipulation.
    - It's recommended to have a highly fusable hand on the last turn. This increases the chances of a successful RNG manipulation.
    """)
    

# Section 1
with st.expander("1 Your Deck"):
    button_text = 'Load sample deck' if localS.getItem('player_deck_input') is None else 'Load your deck'
    if st.button(button_text):
        if localS.getItem('player_deck_input'):
            st.session_state['player_deck_input'] = localS.getItem('player_deck_input')
        else:
            st.session_state['player_deck_input'] = " ".join(map(str, range(1, 41)))
    player_deck = []
    player_card_ids_in_deck_input = st.text_input("Enter Card IDs separated by space in ascending order:",key = 'player_deck_input',placeholder = " ".join(map(str, range(1, 41))))
    if player_card_ids_in_deck_input:
        player_card_ids_in_deck = list(map(int,player_card_ids_in_deck_input.split(" ")))
        if len(player_card_ids_in_deck) != 40:
            st.warning("Please enter exactly 40 card IDs.")
        player_deck_df = get_cards_by_ids(player_card_ids_in_deck)
        player_deck_df.index = pd.RangeIndex(start=1, stop=len(player_deck_df) + 1) #starting count from 1

        player_deck = get_card_data_from_card_ids(sorted(set(player_card_ids_in_deck))) #removing duplicates for dropdowns
        st.dataframe(player_deck_df, row_height = 30,height=250,hide_index = False)
        localS.setItem('player_deck_input', player_card_ids_in_deck_input)


if st.button('Reset duel',key="reset_duel"):
    #section 2 Identify the seed
    st.session_state['num_player_cards_used_to_identify_seed'] = 5
    st.session_state['num_opponent_cards_used_to_identify_seed'] = 1
    for i in range(5):
        st.session_state[f'player_card_{i}'] = None
    st.session_state['opponent_card_0'] = None

    #section 4 Events
    st.session_state['events_input'] = ""
    st.session_state['count_fusions'] = 0
    st.session_state['count_traps'] = 0
    st.session_state['count_effective_attacks'] = 0
    st.session_state['count_equips'] = 0
    st.session_state['count_magics'] = 0

    # section 6 last turn 
    st.session_state['player_last_turn_field_card_0'] = None
    st.session_state['player_last_turn_field_card_1'] = None
    st.session_state['player_last_turn_field_card_2'] = None
    for i in range(5):
        st.session_state[f'player_last_turn_card_{i}'] = None
    st.session_state['last_turn_remaining_opp_cards'] = 0
    st.session_state['last_turn_remaining_lp'] = 0
    st.session_state['last_turn_desired_drop_cards'] = []
    
    
    
    


# Section 2
with st.expander("2 Identify the seed"):
    duelists = get_list_of_opponent_names()
    opponent_name = st.selectbox("Select the opponent:",options=duelists)
    opponent_id = get_opponent_id_by_name(opponent_name)

    no_field_type = True # default field type is None, but mages have a field type in campaign when duel starts
    if opponent_id in Constants.opponents_with_special_field_type.keys():
        duel_option = st.selectbox(label = 'Select where duel is taking place',options=['Free duel','Campaign'],key='duel_option')
        no_field_type = True if duel_option == 'Free duel' else False
    if opponent_name != "Duel Master K":
        opp_pool = read_pool(opponent_name, 'Deck')
        opp_pool_cards = get_card_data_from_card_ids(sorted(set(opp_pool)))    
    else:
        opp_pool = None # Duel master K uses the players deck
        opp_pool_cards = player_deck

    # Players cards after shuffle
    st.number_input("Number of player cards used to identify the seed ", min_value=5, max_value=30, key='num_player_cards_used_to_identify_seed')
    selected_player_cards = []
    first_5_columns = st.columns(5)
    if len(player_deck) > 0:
        for i in range(5):
            selected_card = first_5_columns[i].selectbox(label = ' ',label_visibility='collapsed',options=[f"{card.cardID}: {card.name}" for card in player_deck],key=f"player_card_{i}",index=None,placeholder=f"Player card {i+1}")
            if selected_card:
                selected_player_cards.append(int(selected_card.split(":")[0]))
    if len(selected_player_cards)>=5:
        st.write(':blue[Best starting fusion: ',make_best_fusion_from_hand(selected_player_cards),']')
    if st.session_state['num_player_cards_used_to_identify_seed'] > 5:
        second_set_of_columns = st.columns(st.session_state['num_player_cards_used_to_identify_seed']-5)
        for i in range(st.session_state['num_player_cards_used_to_identify_seed']-5):
            selected_card = second_set_of_columns[i].selectbox(label = ' ',label_visibility='collapsed',options=[f"{card.cardID}: {card.name}" for card in player_deck],key=f"player_card_{i+5}",index=None,placeholder=f"Player card {i+6}")
            if selected_card:
                selected_player_cards.append(int(selected_card.split(":")[0]))

    # Opponent cards after shuffle
    st.number_input("Number of opponent cards used to identify the seed ", min_value=0, max_value=30, key='num_opponent_cards_used_to_identify_seed')
    selected_opponent_cards = []
    if st.session_state['num_opponent_cards_used_to_identify_seed'] > 0:
        opp_card_columns_columns = st.columns(st.session_state['num_opponent_cards_used_to_identify_seed'])
        for i in range(st.session_state['num_opponent_cards_used_to_identify_seed']):
            selected_card = opp_card_columns_columns[i].selectbox(label = ' ',label_visibility='collapsed',options=[f"{card.cardID}: {card.name}" for card in opp_pool_cards],key=f"opponent_card_{i}",index=None,placeholder=f"Opponent card {i+1}")
            if selected_card:
                selected_opponent_cards.append(int(selected_card.split(":")[0]))

    # First guess at possible seed indexes   
    possible_seed_indexes = []
    if len(selected_player_cards)>=5:
        possible_seed_indexes = get_initial_possible_seeds(player_card_ids_in_deck,selected_player_cards)                
    if len(possible_seed_indexes) > 0:        
        # Iterate over possible seed indexes and discard them based on the opponent cards
        for possible_seed_index in possible_seed_indexes[:]: #iterate over a copy of the list to allow removal during iteration
            (poss_opp_deck, _) = create_opponent_deck(opp_pool, possible_seed_index,opponent_name,player_card_ids_in_deck)            
            opp_cards_to_play_order = generate_opponents_cards_to_play_order(opponent_id,poss_opp_deck,no_field_type) 
            for i,enemy_card in enumerate(selected_opponent_cards):
                if enemy_card != opp_cards_to_play_order[i].cardID:
                    possible_seed_indexes.remove(possible_seed_index)
                    break
    
    if len(possible_seed_indexes)==0 and len(selected_player_cards)>=5:
        st.write(':red[No possible seed indexes found with that shuffling order. Review your card selection. Remember to reset your console before each duel]')
    if len(possible_seed_indexes)>1:
        st.write('add more player or opponent cards to identify the initial seed index uniquely')
        st.write('possible seed indexes: ',','.join(list(map(str,possible_seed_indexes))))

    initial_seed_index = None
    if possible_seed_indexes is not None and len(possible_seed_indexes)==1:
        initial_seed_index = possible_seed_indexes[0]
        st.write('initial seed index: ',initial_seed_index)


# Section 3
with st.expander("3: Player and Opponent Deck (informational, no action needed)"):
    if possible_seed_indexes is None or len(possible_seed_indexes) == 0:
        st.write("Please enter your hand to see your's and opponent's shuffled deck.")

    if possible_seed_indexes is not None and len(possible_seed_indexes) > 1:  # Initial seed index not yet identified, multiple options
        st.write('Add more cards to uniquely identify the initial seed index, possible cards at each position will be displayed below.')
        list_of_possible_opp_decks = []
        list_of_possible_player_decks = []

        # Iterate over all possible seed indexes and save all possible opponent decks
        for possible_seed_index in possible_seed_indexes:
            (poss_opp_deck, _) = create_opponent_deck(opp_pool, possible_seed_index,opponent_name,player_card_ids_in_deck)
            opp_cards_to_play_order = generate_opponents_cards_to_play_order(opponent_id, poss_opp_deck, no_field_type)
            list_of_possible_opp_decks.append([card.cardID for card in opp_cards_to_play_order])
            player_deck_shuffled = create_player_deck(player_card_ids_in_deck, possible_seed_index)
            list_of_possible_player_decks.append(player_deck_shuffled)

        # Combine all possible player decks into a single list with concatenated IDs for each position
        combined_player_deck = []
        
        for i in range(len(list_of_possible_player_decks[0])):  # Iterate over positions in the deck
            ids_at_position = set(deck[i] for deck in list_of_possible_player_decks)  # Collect IDs at this position

            cards_at_position = get_card_data_from_card_ids(ids_at_position)
            combined_player_deck.append({'Pos': i+1, 'Card':"  |  ".join(f"{card.cardID}: {card.name} ({card.attack}/{card.defense})" for card in cards_at_position)})  # Concatenate cards with '|'
        st.write("Possible Player cards at each position (IDs separated by '|'):")
        st.dataframe(combined_player_deck,hide_index = True, column_config={"Pos": st.column_config.TextColumn(width=1),"Card": st.column_config.TextColumn(width=900)})

        combined_opp_deck = []
        for i in range(len(list_of_possible_opp_decks[0])):  # Iterate over positions in the deck
            ids_at_position = set(deck[i] for deck in list_of_possible_opp_decks)  # Collect IDs at this position
            cards_at_position = get_card_data_from_card_ids(ids_at_position)
            combined_opp_deck.append({'Pos': i+1, 'Card':"  |  ".join(f"{card.cardID}: {card.name} ({card.attack}/{card.defense}) {card.guardian_star} " for card in cards_at_position)})  # Concatenate cards with '|'
        st.write("Possible Opponent cards at each position (IDs separated by '|'):")
        st.dataframe(combined_opp_deck,hide_index = True, column_config={"Pos": st.column_config.TextColumn(width=1),"Card": st.column_config.TextColumn(width=900)})

    if initial_seed_index is not None:  # Initial seed index identified
        setup_load_db_to_memory(initial_seed_index) # load dbs to memory with variable anim steps for the identified initial seed index
        (poss_opp_deck, _) = create_opponent_deck(opp_pool, initial_seed_index,opponent_name,player_card_ids_in_deck)
        opp_cards_to_play_order = generate_opponents_cards_to_play_order(opponent_id, poss_opp_deck, no_field_type)
        st.write("Player's deck order:")
        player_deck_shuffled = create_player_deck(player_card_ids_in_deck, initial_seed_index)
        player_deck_shuffled = get_card_data_from_card_ids(player_deck_shuffled)
        df_player_deck_shuffled = pd.DataFrame(([o.to_dict() for o in player_deck_shuffled])).drop(columns=["Guardian Star", "Cards left in Opp Deck"])

        st.dataframe(df_player_deck_shuffled, use_container_width=True,row_height = 30,height=250,hide_index = True)
        #st.dataframe(df_player_deck_shuffled, use_container_width=True)
        st.write("Opponent's deck order:")
        df_opp_cards = pd.DataFrame(([o.to_dict() for o in opp_cards_to_play_order])).drop(columns=["Guardian Stars"])
        st.dataframe(df_opp_cards, use_container_width=True,row_height = 30,height=250,hide_index = True)


# Section 4
with st.expander("4: Add actions"):
    
    a = """ with st.expander("List of Possible Events:"):
        df_events = pd.DataFrame([{"Event ID": event.event_id, "Name": event.name, "Seed Advancements": event.seed_advancements , "Description": event.description} for event in Constants.events])
        df_events = df_events[df_events["Event ID"] != 0] # Exclude the initial deck shuffling event from display
        st.dataframe(df_events, use_container_width=True,hide_index = True) """
    event_history = []
    a = """ 
    st.write("Add events by clicking below:")
    if 'events_input' not in st.session_state:
        st.session_state['events_input'] = ""
    display_events = [event for event in Constants.events if event.event_id not in [0,6]] # Filter events to display (skip event_id 0 (deck shuffling), 6 (empty), 7 (end of duel))
    third = (len(display_events) + 1) // 3
    row1, row2, row3 = display_events[:third], display_events[third:2*third], display_events[2*third:]
    cols1 = st.columns(len(row1))
    for idx, event in enumerate(row1):
        if cols1[idx].button(f"{event.event_id}: {event.name}", key=f"event_btn_row1_{event.event_id}"):
            st.session_state['events_input'] += f" {event.event_id}"
    cols2 = st.columns(len(row2))
    for idx, event in enumerate(row2):
        if cols2[idx].button(f"{event.event_id}: {event.name}", key=f"event_btn_row2_{event.event_id}"):
            st.session_state['events_input'] += f" {event.event_id}"
    cols3 = st.columns(len(row3))
    for idx, event in enumerate(row3):
        if cols3[idx].button(f"{event.event_id}:  {event.name}", key=f"event_btn_row3_{event.event_id}"):
            st.session_state['events_input'] += f" {event.event_id}"

    st.write('---') """

    for i, action in enumerate(Constants.actions):
        col1, col2, col3, col4, col5, col6 = st.columns(6,vertical_alignment="bottom")
        col1.write(' ')
        add_action = col1.button(f'Add {action.name}', key=f"action_add_btn_{action.action_id}",width ='stretch')

        if action.name in ['Attack Card','Change Field','Fusion','Equip','Trap Triggered']: #not in ["Dump","Attack LP"]:
            who_did_the_action = col2.selectbox('Who did the action?', options=['Player', 'Opponent'], key=f"action_who_{i}")
        
        if action.name == "Attack Card":
            was_card_destroyed = col3.selectbox('Attacked Card destroyed?', options=['Yes', 'No'], key=f"action_attack_destroyed_{i}")
            was_gs_anim = col4.selectbox('GS Animation?', options=['No', 'Yes'], key=f"action_gs_anim_{i}")
            atk_card_mode = col5.selectbox('Attacked Card Mode', options=['DEF','ATK'], key=f"action_attack_type_{i}")
            if atk_card_mode == 'ATK':
                dmg_done = col6.selectbox('Damage done',options=['< 1000','>= 1000','0'], key=f"action_attack_damage_{i}")
            
            # Add events based on selections
            if add_action:
                st.session_state['events_input'] += f" {get_event_id_by_name('GS_ANIM')}" if was_gs_anim == 'Yes' else ''
                if atk_card_mode == 'ATK':
                    st.session_state['events_input'] += f" {get_event_id_by_name('LOSE_ATTACK')}" if was_card_destroyed == 'No' else ''
                    st.session_state['count_effective_attacks'] += 1 if who_did_the_action == 'Player' and was_card_destroyed == 'Yes' else 0
                    if dmg_done != '0':
                        st.session_state['events_input'] += f" {get_event_id_by_name('SWIPE_ATK_LOW')}" if dmg_done == '< 1000' else f" {get_event_id_by_name('SWIPE_ATK_HIGH')}" if dmg_done == '>= 1000' else ''
                        st.session_state['events_input'] += f" {get_event_id_by_name('BURN')}"
                    if dmg_done == '0':
                        st.session_state['events_input'] += f" {get_event_id_by_name('SWIPE_DEF')} {get_event_id_by_name('BURN')} {get_event_id_by_name('SWIPE_DEF')} {get_event_id_by_name('BURN')}"
            
                if atk_card_mode == 'DEF':
                    if was_card_destroyed == 'No':
                        st.session_state['events_input'] += f" {get_event_id_by_name('LOSE_ATTACK')}"                    
                    else:
                        st.session_state['events_input'] += f" {get_event_id_by_name('SWIPE_DEF')}"
                        st.session_state['events_input'] += f" {get_event_id_by_name('BURN')}"
            
            

        if action.name == "Attack LP":
            action_attack_damage = col2.selectbox('Damage done',options=['>= 1000','< 1000'], key=f"action_attack_damage_{i}")
            if add_action:
                match action_attack_damage:
                    case '< 1000':
                        st.session_state['events_input'] += f" {get_event_id_by_name('DIRECT_LOW')}"
                    case '>= 1000':
                        st.session_state['events_input'] += f" {get_event_id_by_name('DIRECT_HIGH')}"               
        
        if action.name == "Change Field":
            field_type_selected = col3.selectbox('Field Type',options=['Mountain','Yami','Other'], key=f"action_change_field_{i}")
            if add_action:
                st.session_state['count_magics'] += 1 if who_did_the_action == 'Player' else 0
                match field_type_selected:
                    case 'Mountain':
                        st.session_state['events_input'] += f" {get_event_id_by_name('FIELD_MOUNT')}"
                    case 'Yami':
                        st.session_state['events_input'] += f" {get_event_id_by_name('FIELD_YAMI')}"
                    case 'Other':
                        st.session_state['events_input'] += f" {get_event_id_by_name('FIELD_USUAL')}"

        if action.name == "Dump" and add_action:
            st.session_state['events_input'] += f" {get_event_id_by_name('DUMP')}" 
        
        if action.name == "Fusion" and add_action:
            st.session_state['events_input'] += f" {get_event_id_by_name('FUSION')}"
            st.session_state['count_fusions'] += 1 if who_did_the_action == 'Player' else 0
        
        if action.name == "Equip" and add_action:
            st.session_state['events_input'] += f" {get_event_id_by_name('EQUIP')}"
            st.session_state['count_equips'] += 1 if who_did_the_action == 'Player' else 0

        if action.name == "Trap Triggered" and add_action:
            st.session_state['events_input'] += f" {get_event_id_by_name('TRAP_TRIGGERED')}"
            st.session_state['count_traps'] += 1 if who_did_the_action == 'Player' else 0

    events_input = st.text_input("Use the buttons above to populate the events", key = "events_input")
    if events_input:
        event_ids = list(map(int, (events_input.strip().split(" "))))
        event_ids.insert(0, 0)  # adding event of decks shuffling, it's always the first event
        
        for i, event_id in enumerate(event_ids):
            selected_event = next((event for event in Constants.events[:] if event.event_id == event_id), None)
            
            # Add initial and new seed index to each event when initial seed index is known
            if initial_seed_index is not None:
                if i == 0: # first event, decks shuffling has special handling
                    selected_event.initial_seed_index = initial_seed_index
                    (shuffled_deck, new_seed_index) = create_opponent_deck(opp_pool, initial_seed_index,opponent_name,player_card_ids_in_deck)  # just to advance the seed internally
                    selected_event.new_seed_index = new_seed_index
                    event_history.append(selected_event)
                    continue 
                
                selected_event.initial_seed_index = event_history[-1].new_seed_index or 0
                selected_event.new_seed_index = selected_event.initial_seed_index + get_adv_steps_from_anim(selected_event.initial_seed_index,selected_event.name)
            event_history.append(copy.deepcopy(selected_event))

    # Display history of events
    with st.expander("Event History"):
        if len(event_history) > 0 and initial_seed_index is not None:
            df_event_history = pd.DataFrame([{
                "Event ID": event.event_id,
                "Name": event.name,
                "Initial Seed Index": event.initial_seed_index,
                "New Seed Index": event.new_seed_index
            } for event in event_history])
            st.dataframe(df_event_history, use_container_width=True,hide_index = True)

        if len(event_history) > 0 and initial_seed_index is None:
            df_event_history = pd.DataFrame([{
                "Event ID": event.event_id,
                "Name": event.name
            } for event in event_history])
            st.dataframe(df_event_history, use_container_width=True,hide_index = True)

    #Display the metrics
    if initial_seed_index is not None or 1==1:
        cols_display_counts = st.columns(6)
        with cols_display_counts[0]:
            st.metric("Fusions", st.session_state['count_fusions'])
        with cols_display_counts[1]:
            st.metric("Traps", st.session_state['count_traps'])
        with cols_display_counts[2]:
            st.metric("Effective Attacks", st.session_state['count_effective_attacks'])
        with cols_display_counts[3]:
            st.metric("Equips", st.session_state['count_equips'])
        with cols_display_counts[4]:
            st.metric("Magics", st.session_state['count_magics'])
        with cols_display_counts[5]:
            st.metric("Seed Index", event_history[-1].new_seed_index if initial_seed_index is not None and len(event_history)>0 else '?')
# Section 5
with st.expander("Duel Rank calculator (optional)"):

    st.info('''
• Defensive wins: Player's card in Def mode is attacked and not destroyed.\n
• Effective Attacks: Opponent card in atk mode is destroyed.\n
• The checkbox freezes the value, so the reset button doesn't reset it.\n
• The numbers after the labels are the values that change the duel rank points.'''        
    )
    # Initialize session_state only if not present
    for k in Constants.duel_rank_keys:
        if k not in st.session_state:
            st.session_state[k] = Constants.duel_rank_defaults[k]
        # Add a keep checkbox for each input
        keep_key = f'keep_{k}'
        if keep_key not in st.session_state:
            st.session_state[keep_key] = False

    reset_rank_calculator = st.button('reset', key='reset_rank_calculator')
    if reset_rank_calculator:
        for k in Constants.duel_rank_keys:
            keep_key = f'keep_{k}'
            if not st.session_state[keep_key]:
                st.session_state[k] = Constants.duel_rank_defaults[k]

    with st.form("duel_rank_calculator_form",enter_to_submit=False,border=False):
        col1, col2 = st.columns(2)
        with col1:
            cb, inp = st.columns([1, 30])
            cb.write(" ")  # spacer for alignment
            cb.write(" ")
            cb.checkbox(" ", key='keep_num_fusions', label_visibility='collapsed')
            inp.number_input("Fusions (1,5,10,15)", min_value=0, key='num_fusions')
            cb, inp = st.columns([1, 30])
            cb.write(" ")
            cb.write(" ")
            cb.checkbox(" ", key='keep_num_magics', label_visibility="collapsed")
            inp.number_input("Magics (1,4,7,10)", min_value=0, key='num_magics')
            cb, inp = st.columns([1, 30])
            cb.write(" ")
            cb.write(" ")
            cb.checkbox(" ", key='keep_num_equips', label_visibility="collapsed")
            inp.number_input("Equips (1,5,10,15)", min_value=0, key='num_equips')
            cb, inp = st.columns([1, 30])
            cb.write(" ")
            cb.write(" ")
            cb.checkbox(" ", key='keep_num_cards_left', label_visibility="collapsed")
            inp.number_input("Cards left in your deck [complement of cards used] (31,27,7,3)", min_value=0, key='num_cards_left')
            cb, inp = st.columns([1, 30])
            cb.write(" ")
            cb.write(" ")
            cb.checkbox(" ", key='keep_num_facedowns', label_visibility="collapsed")
            inp.number_input("Facedowns (1,11,21,31)", min_value=0, key='num_facedowns')
        with col2:
            cb, inp = st.columns([1, 30])
            cb.write(" ")
            cb.write(" ")
            cb.checkbox(" ", key='keep_num_traps', label_visibility="collapsed")
            inp.number_input("Traps (1,3,5,7)", min_value=0, key='num_traps')
            cb, inp = st.columns([1, 30])
            cb.write(" ")
            cb.write(" ")
            cb.checkbox(" ", key='keep_remaining_lp', label_visibility="collapsed")
            inp.selectbox("Remaining Life Points",options=['8000','7000 - 7999','1000 - 6999','100 - 999','< 100'],key='remaining_lp')
            cb, inp = st.columns([1, 30])
            cb.write(" ")
            cb.write(" ")
            cb.checkbox(" ", key='keep_num_opp_cards_left', label_visibility="collapsed")
            inp.number_input("Opponent cards left [complement of num of turns] (31,27,7,3)", min_value=0, key='num_opp_cards_left') # 9 turns equal 27 cards left in opp deck
            cb, inp = st.columns([1, 30])
            cb.write(" ")
            cb.write(" ")
            cb.checkbox(" ", key='keep_num_defensive_wins', label_visibility="collapsed")
            inp.number_input("Defensive wins (2,6,10,15) ", min_value=0, key='num_defensive_wins')
            cb, inp = st.columns([1, 30])
            cb.write(" ")
            cb.write(" ")
            cb.checkbox(" ", key='keep_num_effectives', label_visibility="collapsed")
            inp.number_input("Effective attacks (2,4,10,20) ", min_value=0, key='num_effectives')

        
        if st.form_submit_button("Recalculate Duel Rank"):
            duel_rank_points, duel_rank = calculate_duel_rank(
                st.session_state['num_fusions'],
                st.session_state['num_effectives'],
                st.session_state['num_facedowns'],
                st.session_state['num_magics'],
                st.session_state['num_equips'],
                st.session_state['num_traps'],
                40 - st.session_state['num_cards_left'], #To Do: verify this is a correct way to calculate used cards
                36 - st.session_state['num_opp_cards_left'], #To Do: verify this is a correct way to calculate number of turns
                st.session_state['num_defensive_wins'],
                st.session_state['remaining_lp']
            )
            st.write("Duel Rank Points:", duel_rank_points)
            st.write("Duel Rank:", duel_rank)

# Section 6
with st.expander("Last Turn"):
    my_cards_in_field = []
    if initial_seed_index is None:
        st.write('Identify initial seed index first, and then use this section for the last turn')
    
    if initial_seed_index is not None:
        # Field cards are outside the st.form because the guardian star dropdown depends on the selection of the card
        for i in range(4):
            col1, col2, col3 = st.columns(3)
            selected_card_input = col1.selectbox(label = f'Field card {i + 1}',options=[f"{card['Id']}: {card['Name']}" for card in Constants.card_data if card['Type'] < 20], key=f"player_last_turn_field_card_{i}",index=None)
            if selected_card_input:
                num_equips = col3.number_input(f" Number of equips applied (Megamorph counts as 2)",min_value=0, max_value=10, key=f"eq_{i}")
                card = get_card_data_from_card_ids([int(selected_card_input.split(":")[0])])[0]
                guardian_star = col2.selectbox(f"Guardian Star for {card.name}", options=card.guardian_stars, key=f"gs_{i}")
                card.guardian_star = guardian_star
                card = add_equips(card,num_equips)
                my_cards_in_field.append(card)
        

        with st.form("last_turn_form",enter_to_submit=False,border=False):
            st.write('Your Hand')
            columns_last_turn_player_hand = st.columns(5)
            last_hand_card_ids = []
            for i in range(5):
                selected_card = columns_last_turn_player_hand[i].selectbox(label = ' ',label_visibility='collapsed', options=[f"{card.cardID}: {card.name}" for card in player_deck], key=f"player_last_turn_card_{i}",index=None,placeholder=f'Card {i + 1}')
                if selected_card:
                    last_hand_card_ids.append(int(selected_card.split(":")[0]))
            hand = get_card_data_from_card_ids(last_hand_card_ids)
            
            col1,col2,col3 = st.columns(3)
            opp_remaining_cards = col1.number_input(label = "Num of Cards Remaining in Opponent's deck",min_value = 0, max_value = 35, key = 'last_turn_remaining_opp_cards')
            enemy_card =   [card for card in opp_cards_to_play_order  if card.cards_left_in_opp_deck == opp_remaining_cards][0] if opp_remaining_cards > 0 else None
            enemy_card_position_input = col2.selectbox("Opponent's Card Position",options=["Defense","Attack"],key="is_enemy_card_in_atk")
            is_enemy_card_in_atk = True if enemy_card_position_input == "Attack" else False
            remaining_enemy_LP = col3.number_input("Opponent remaining Life Points:",min_value = 0, max_value = 8000,key='last_turn_remaining_lp')
            
            col1, col2 = st.columns(2)
            battle_rank = col1.selectbox("Select the duel battle rank:", options=['SAPow','BCD','SATec'])
            field_type = col2.selectbox("Field Type", options=[x[1] for x in Constants.field_types], key="last_turn_field_type")
            field_type_id = [x[0] for x in Constants.field_types if x[1] == field_type][0]
            

            enemy_drop_pool = read_pool(opponent_name, battle_rank)
            enemy_drop_pool_card_ids = list(set(enemy_drop_pool)) # Unique card IDs in the drop pool
            enemy_drop_pool_card_ids.sort()
            enemy_drop_pool_cards = get_card_data_from_card_ids(enemy_drop_pool_card_ids)
            desired_drop_cards = st.multiselect("Desired cards:",[f"{card.cardID}: {card.name}" for card in enemy_drop_pool_cards],key='last_turn_desired_drop_cards')
            search = st.form_submit_button("Search")

            if search and (remaining_enemy_LP == 0 or not enemy_card or len(desired_drop_cards) == 0 or len(hand) < 5):
                st.warning("Please provide all required information.")
                

            if search and remaining_enemy_LP > 0 and len(desired_drop_cards) > 0 and enemy_card and len(hand) == 5:
                seed_index_at_start_of_last_turn = event_history[-1].new_seed_index
                main_phase_actions = generate_main_phase_actions(hand,my_cards_in_field,seed_index_at_start_of_last_turn,field_type_id,enemy_card)
                st.write(len(main_phase_actions), " possible Main Phase actions")
                plays = []
                search_start_time = datetime.now()
                found_drop = False
                attack_types = ['Normal','Quick3D','SPAWN_3D']
                for attack_type in attack_types: 
                    if not found_drop:
                        for main_phase_action in main_phase_actions:
                            if not found_drop:
                                possible_battle_phase_actions = generate_attack_combinations_from_cards_in_field(enemy_card,remaining_enemy_LP,main_phase_action,is_enemy_card_in_atk,attack_type)
                                for battle_phase_actions in possible_battle_phase_actions:
                                    play = Play(seed_index_at_start_of_last_turn)
                                    play.main_phase_action = main_phase_action
                                    play.battle_phase_actions = battle_phase_actions    
                                    play.calculate_drop(enemy_drop_pool)
                                    if int(play.drop_card.cardID) in list(map(lambda x: int(x.split(":")[0]),desired_drop_cards)):
                                        st.write("Found a way to get the desired drop!")
                                        found_drop = True
                                        break

                if not found_drop:
                    st.write("No possible actions found to get the desired drop. Destroy enemy card and try again next turn.")
                else: 
                    st.write(play)

