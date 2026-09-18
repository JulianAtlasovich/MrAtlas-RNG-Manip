import streamlit as st
import pandas as pd
import sqlite3
from drop_manip_classes_and_constants import *
from helper_functions_seed_tracker import *
from db_queries import *
from datetime import datetime
from streamlit_local_storage import LocalStorage
#import ptvsd


def add_selected_drop_card_ids():
    selected_drop_cards = st.session_state.get('last_turn_desired_drop_cards', [])
    selected_card_ids = [card.split(':', 1)[0] for card in selected_drop_cards]
    typed_card_ids = st.session_state.get('last_turn_desired_drop_card_ids', '').split()
    st.session_state['last_turn_desired_drop_card_ids'] = ' '.join(dict.fromkeys(typed_card_ids + selected_card_ids))

def enable_action_shortcuts():
    st.iframe(
                """
                <script>
                const shortcutButtons = {
                    "Digit1": "Dump (Alt+1)",
                    "Digit2": "Fusion (Alt+2)",
                    "Digit3": "Equip (Alt+3)",
                    "Digit4": "G. Star Anim (Alt+4)",
                    "Digit5": "Attack card in DEF (Alt+5)",
                    "Digit6": "Attack card ATK <1000 (Alt+6)",
                    "Digit7": "Attack card ATK >=1000 (Alt+7)",                    
                    "Digit8": "Attack LP (Alt+8)",
                    "Digit9": "Change Field (Alt+9)",
                    "Digit0": "Trap Triggered (Alt+0)"
                };

                const parentDocument = window.parent.document;
                if (window.parent.atlasActionShortcutHandler) {
                    parentDocument.removeEventListener("keydown", window.parent.atlasActionShortcutHandler, true);
                }

                const shortcutHandler = (event) => {
                    if (!event.altKey || event.ctrlKey || event.metaKey || event.shiftKey || event.repeat) {
                        return;
                    }

                    const shortcutKey = event.code.startsWith("Numpad")
                        ? `Digit${event.code.slice("Numpad".length)}`
                        : event.code;
                    const buttonLabel = shortcutButtons[shortcutKey];
                    if (!buttonLabel) {
                        return;
                    }

                    const button = Array.from(parentDocument.querySelectorAll("button")).find(
                        (candidate) => candidate.innerText.trim() === buttonLabel
                    );
                    if (button) {
                        event.preventDefault();
                        button.click();
                    }
                };
                window.parent.atlasActionShortcutHandler = shortcutHandler;
                parentDocument.addEventListener("keydown", shortcutHandler, true);
                </script>
                """,
                height=1,
        )


def add_event(event_name):
        st.session_state['events_input'] = st.session_state.get('events_input', '') + f" {get_event_id_by_name(event_name)}"


st.set_page_config(layout="wide")
st.title("""The Atlas of RNG Manipulation for YGO Forbidden Memories""")
localS = LocalStorage()
#ptvsd.enable_attach(address=('localhost', 5678), redirect_output=True)
#ptvsd.wait_for_attach()
# Search Bar
with st.expander("Tool Guide"):
    st.video('https://youtu.be/Wbb47rbdSRM')
    st.info("""
    v1.52
    This tool helps you manipulate the RNG (Random Number Generator) in Yu-Gi-Oh! Forbidden Memories.

    Restrictions:
    - You :red[MUST] restart your console before each duel.
    - You must destroy every card the opponent plays on your turn.
    - You must enter each duel using the default ID card sorting.
    - You must play all your monsters face up. (Doesn't apply to magic,traps,equips)
    - You can't use any magic card that is not a field card. No removal cards (e.g. "Dark Hole", "Raigeki", "Dragon Capture Jar")
    - It's recommended to have a highly fusable hand on the last turn. This increases the chances of a successful RNG manipulation.
    """)
    

# Section 1
with st.expander("1: Your Deck"):
    button_text = 'Load sample deck' if localS.getItem('player_deck_input') is None else 'Load your deck'
    if st.button(button_text):
        if localS.getItem('player_deck_input'):
            st.session_state['player_deck_input'] = localS.getItem('player_deck_input')
        else:
            st.session_state['player_deck_input'] = " ".join(map(str, range(1, 41)))
    player_deck = []
    player_card_ids_in_deck_input = st.text_input("Enter Card IDs separated by space in ascending order:",key = 'player_deck_input',placeholder = " ".join(map(str, range(1, 41))))
    if player_card_ids_in_deck_input:
        player_card_ids_in_deck = list(map(int,player_card_ids_in_deck_input.strip().split(" ")))
        if len(player_card_ids_in_deck) != 40:
            st.warning("Please enter exactly 40 card IDs.")
        player_deck_df = get_cards_by_ids(player_card_ids_in_deck)
        player_deck_df.index = pd.RangeIndex(start=1, stop=len(player_deck_df) + 1) #starting count from 1

        player_deck = get_card_data_from_card_ids(sorted(set(player_card_ids_in_deck))) #removing duplicates for dropdowns
        player_deck_with_repetitions = get_card_data_from_card_ids(player_card_ids_in_deck)
        st.dataframe(player_deck_df, row_height = 30,height=250,hide_index = False)
        localS.setItem('player_deck_input', player_card_ids_in_deck_input)


if st.button('Reset duel',key="reset_duel"):    
    #section 2 Identify the seed
    #st.session_state['initial_seed'] = None
    st.session_state['num_player_cards_used_to_identify_seed'] = 5
    st.session_state['num_opponent_cards_used_to_identify_seed'] = 0
    st.session_state['opponent_card_0'] = None
    st.session_state['first_card_index_in_player_deck_with_multiple_options'] = None  
    st.session_state['list_of_possible_player_decks'] = []
    st.session_state['first_card_index_in_opp_deck_with_multiple_options'] = None  
    st.session_state['list_of_possible_opp_decks'] = []
    for i in range(5):
        st.session_state[f'player_card_{i}'] = None

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
    st.session_state['player_last_turn_field_card_3'] = None
    for i in range(5):
        st.session_state[f'player_last_turn_card_{i}'] = None
    st.session_state['last_turn_standard_remaining_opp_cards'] = 33
    st.session_state['last_turn_simplified_remaining_opp_cards'] = 33
    st.session_state['last_turn_standard_enemy_card_position'] = 'Defense'
    st.session_state['last_turn_simplified_enemy_card_position'] = 'Defense'
    st.session_state['last_turn_remaining_lp'] = 0
    st.session_state['last_turn_desired_drop_cards'] = []
    st.session_state['show_first_opponent_card'] = False
    
    
    
    


# Section 2
with st.expander("2: Identify the seed"):
    duelists = get_list_of_opponent_names_st()
    min_seed_index, max_seed_index,load_sample_deck_order = st.columns([1.5,1.5,1], vertical_alignment="bottom")
    load_sample_deck_order = load_sample_deck_order.checkbox("Load Sample Deck Order")
    min_seed_index = min_seed_index.number_input("Minimum seed index to consider", min_value=0, value=0, key='min_seed_index')
    max_seed_index = max_seed_index.number_input("Max seed to consider (0 for no limit)", min_value=0, value=0, key='max_seed_index')
    opponent_name,opponent_data,_ = st.columns([1.5,1.5,1], vertical_alignment="top")
    opponent_name = opponent_name.selectbox("Select the opponent:",options=duelists)
    opponent_id = get_opponent_id_by_name(opponent_name)
    opponent_data = opponent_data.text(f'{Constants.opponents_strongest_card_description.get(opponent_id,"N/A")}')

    opponent_id = get_opponent_id_by_name(opponent_name)
    initial_seed_index = None
    
    if 'first_card_index_in_player_deck_with_multiple_options' not in st.session_state:
        st.session_state['first_card_index_in_player_deck_with_multiple_options'] = None  
    if 'list_of_possible_player_decks' not in st.session_state:
        st.session_state['list_of_possible_player_decks'] = []
    if 'first_card_index_in_opp_deck_with_multiple_options' not in st.session_state:
        st.session_state['first_card_index_in_opp_deck_with_multiple_options'] = None  
    if 'list_of_possible_opp_decks' not in st.session_state:
        st.session_state['list_of_possible_opp_decks'] = []
    #if 'initial_seed' not in st.session_state:
    combined_opp_deck = []    
    combined_player_deck = []     
    possible_seed_indexes = []
    should_show_first_opponent_card = False

    no_field_type = True # default field type is None, but mages have a field type in campaign when duel starts
    if opponent_id in Constants.opponents_with_special_field_type.keys():
        duel_option = st.selectbox(label = 'Select where duel is taking place',options=['Free duel','Campaign'],key='duel_option')
        no_field_type = True if duel_option == 'Free duel' else False
    if opponent_name != "Duel Master K":
        opp_pool = st_read_pool(opponent_name, 'Deck')
        opp_pool_cards = get_card_data_from_card_ids(sorted(set(opp_pool)))    
    else:
        opp_pool = None # Duel master K uses the players deck
        opp_pool_cards = player_deck

    # Players cards after shuffle    
    st.number_input("Number of player cards used to identify the seed ", min_value=5, max_value=15, key='num_player_cards_used_to_identify_seed')
    selected_player_cards = []
    sample_deck_order = [0,1,6,10,20]  # one sample order that identifies the seed
   
    if load_sample_deck_order and len(player_deck) > 0:
        for i, sample_index in enumerate(sample_deck_order):
            card = player_deck_with_repetitions[sample_index]
            st.session_state[f"player_card_{i}"] = f"{card.cardID}: {card.name}"
    
    # first row of columns
    first_5_columns = st.columns(5)
    if len(player_deck) > 0:
        for i in range(5):
            selected_card = first_5_columns[i].selectbox(label = ' ',label_visibility='collapsed',options=[f"{card.cardID}: {card.name}" for card in player_deck],key=f"player_card_{i}",index=None,placeholder=f"Player card {i+1}")
            if selected_card:
                selected_player_cards.append(int(selected_card.split(":")[0]))
    if len(selected_player_cards)>=5:
        st.write(':blue[Best starting fusion: ',make_best_fusion_from_hand(selected_player_cards),']')
    
    # second row of columns
    if st.session_state['num_player_cards_used_to_identify_seed'] > 5:
        second_set_of_columns = st.columns(5)        
        for i in range(min(st.session_state['num_player_cards_used_to_identify_seed']-5, 5)): # how many cards in second row
            pos = i+5
            ids_at_position = sorted(set(deck[pos] for deck in st.session_state['list_of_possible_player_decks']))  # Collect IDs at this position
            cards_at_position = get_card_data_from_card_ids(ids_at_position)            
            if len(cards_at_position) == 1:
                selected_card = second_set_of_columns[i].selectbox(label = ' ',label_visibility='collapsed',options=[f"{card.cardID}: {card.name}" for card in cards_at_position],key=f"player_card_{pos+1}",disabled=True,placeholder=f"Player card {pos+1}")
            else:
                selected_card = second_set_of_columns[i].selectbox(label = ' ',label_visibility='collapsed',options=[f"{card.cardID}: {card.name}" for card in cards_at_position],key=f"player_card_{pos+1}",index=None,placeholder=f"Player card {pos+1}")
            if selected_card:
                selected_player_cards.append(int(selected_card.split(":")[0]))
    # third row of columns
    if st.session_state['num_player_cards_used_to_identify_seed'] > 10:
        third_set_of_columns = st.columns(5)
        for i in range(min(st.session_state['num_player_cards_used_to_identify_seed']-10, 5)):  # how many cards in third row
            pos = i+10
            ids_at_position = sorted(set(deck[pos] for deck in st.session_state['list_of_possible_player_decks']))  # Collect IDs at this position
            cards_at_position = get_card_data_from_card_ids(ids_at_position)            
            if len(cards_at_position) == 1:
                selected_card = third_set_of_columns[i].selectbox(label = ' ',label_visibility='collapsed',options=[f"{card.cardID}: {card.name}" for card in cards_at_position],key=f"player_card_{pos+1}",disabled=True,placeholder=f"Player card {pos+1}")
            else:
                selected_card = third_set_of_columns[i].selectbox(label = ' ',label_visibility='collapsed',options=[f"{card.cardID}: {card.name}" for card in cards_at_position],key=f"player_card_{pos+1}",index=None,placeholder=f"Player card {pos+1}")
            if selected_card:
                selected_player_cards.append(int(selected_card.split(":")[0]))

    # Opponent cards after shuffle
    if st.session_state.get('show_first_opponent_card', False):
        st.session_state['num_opponent_cards_used_to_identify_seed'] = 1
        st.session_state['show_first_opponent_card'] = False
    st.number_input("Number of opponent cards used to identify the seed ", min_value=0, max_value=15, key='num_opponent_cards_used_to_identify_seed')
    selected_opponent_cards = []
    if st.session_state['num_opponent_cards_used_to_identify_seed'] > 0:
        opp_card_columns_columns = st.columns(st.session_state['num_opponent_cards_used_to_identify_seed'])
        for i in range(st.session_state['num_opponent_cards_used_to_identify_seed']):
            ids_at_position = sorted(set(deck[i] for deck in st.session_state['list_of_possible_opp_decks']))  # Collect IDs at this position
            cards_at_position = get_card_data_from_card_ids(ids_at_position)            
            if len(cards_at_position) == 1:
                selected_card = opp_card_columns_columns[i].selectbox(label = ' ',label_visibility='collapsed',options=[f"{card.cardID}: {card.name} {card.guardian_star.split()[1] if len(card.guardian_star.split()) > 1 else ''}" for card in cards_at_position],key=f"opp_card_{i+1}",disabled=True,placeholder=f"Opponent card {i+1}")
            else:
                selected_card = opp_card_columns_columns[i].selectbox(label = ' ',label_visibility='collapsed',options=[f"{card.cardID}: {card.name} {card.guardian_star.split()[1] if len(card.guardian_star.split()) > 1 else ''}" for card in cards_at_position],key=f"opp_card_{i+1}",index=None,placeholder=f"Opponent card {i+1}")
            if selected_card:
                selected_opponent_cards.append(int(selected_card.split(":")[0]))

    # First guess at possible seed indexes   
   
    if len(selected_player_cards)>=5:
        possible_seed_indexes = get_initial_possible_seeds(player_card_ids_in_deck,selected_player_cards,min_seed_index,max_seed_index) 
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
        st.write(':red[No possible seed indexes found with that shuffling order].\n\n Make sure you enter duel in deck numerical order. Review your card selection. Remember to reset your console before each duel]')
    if len(possible_seed_indexes)>=1:                
        st.session_state['list_of_possible_opp_decks'] = []
        st.session_state['list_of_possible_player_decks'] = []

        if len(possible_seed_indexes) > 1 and st.session_state['num_opponent_cards_used_to_identify_seed'] == 0:
            st.session_state['show_first_opponent_card'] = True
            should_show_first_opponent_card = True

        # Iterate over all possible seed indexes and save all possible opponent decks
        for possible_seed_index in possible_seed_indexes:
            (poss_opp_deck, _) = create_opponent_deck(opp_pool, possible_seed_index,opponent_name,player_card_ids_in_deck)
            opp_cards_to_play_order = generate_opponents_cards_to_play_order(opponent_id, poss_opp_deck, no_field_type)
            st.session_state['list_of_possible_opp_decks'].append([card.cardID for card in opp_cards_to_play_order])
            player_deck_shuffled = create_player_deck(player_card_ids_in_deck, possible_seed_index)
            st.session_state['list_of_possible_player_decks'].append(player_deck_shuffled)

        # Combine all possible player decks into a single list with concatenated IDs for each position        
        st.session_state['first_card_index_in_player_deck_with_multiple_options'] = None
        for i in range(len(st.session_state['list_of_possible_player_decks'][0])):  # Iterate over positions in the deck
            ids_at_position = sorted(set(deck[i] for deck in st.session_state['list_of_possible_player_decks']))  # Collect IDs at this position
            cards_at_position = get_card_data_from_card_ids(ids_at_position)
            st.session_state['first_card_index_in_player_deck_with_multiple_options'] = i+1 if st.session_state['first_card_index_in_player_deck_with_multiple_options'] is None and len(ids_at_position)>1 else st.session_state['first_card_index_in_player_deck_with_multiple_options']
            combined_player_deck.append({'Pos': i+1, 'Card':"  |  ".join(f"{card.cardID}: {card.name} ({card.attack}/{card.defense})" for card in cards_at_position)})  # Concatenate cards with '|'
        
        st.session_state['first_card_index_in_opp_deck_with_multiple_options'] = None     
        for i in range(len(st.session_state['list_of_possible_opp_decks'][0])):  # Iterate over positions in the deck
            ids_at_position = sorted(set(deck[i] for deck in st.session_state['list_of_possible_opp_decks']))  # Collect IDs at this position
            st.session_state['first_card_index_in_opp_deck_with_multiple_options'] = i+1 if st.session_state['first_card_index_in_opp_deck_with_multiple_options'] is None and len(ids_at_position)>1 else st.session_state['first_card_index_in_opp_deck_with_multiple_options']
            cards_at_position = get_card_data_from_card_ids(ids_at_position)
            combined_opp_deck.append({'Pos': i+1, 'Card':"  |  ".join(f"{card.cardID}: {card.name} ({card.attack}/{card.defense}) {card.guardian_star} " for card in cards_at_position)})  # Concatenate cards with '|'

        if len(possible_seed_indexes)>1:
            st.write(f"First card position with multiple options for Player: {st.session_state['first_card_index_in_player_deck_with_multiple_options']}, and Opponent: {st.session_state['first_card_index_in_opp_deck_with_multiple_options']}")
            st.write(f'{len(possible_seed_indexes)} possible seed indexes: ',' / '.join(map(str, possible_seed_indexes)),'. Add more player or opponent cards to identify the initial seed index uniquely')
            st.write()

        if should_show_first_opponent_card:
            st.rerun()
    
    if possible_seed_indexes is not None and len(possible_seed_indexes)==1:
        initial_seed_index = possible_seed_indexes[0]
        st.write('initial seed index: ',initial_seed_index)


# Section 3
with st.expander("Player and Opponent Deck (Informational, no action needed)"):
    if possible_seed_indexes is None or len(possible_seed_indexes) == 0:
        st.write("Please enter your hand to see your's and opponent's shuffled deck.")

    if possible_seed_indexes is not None and len(possible_seed_indexes) > 1:  # Initial seed index not yet identified, multiple options
        st.write('Add more cards to uniquely identify the initial seed index, possible cards at each position will be displayed below.')
        
        with st.expander("Possible Player cards at each position (IDs separated by '|')"):
            st.dataframe(combined_player_deck,hide_index = True, column_config={"Pos": st.column_config.TextColumn(width=1),"Card": st.column_config.TextColumn(width=900)})
        with st.expander("Possible Opponent cards at each position (IDs separated by '|')"):
            st.dataframe(combined_opp_deck,hide_index = True, column_config={"Pos": st.column_config.TextColumn(width=1),"Card": st.column_config.TextColumn(width=900)})

    if initial_seed_index is not None:  # Initial seed index identified
        setup_load_db_to_memory_st(initial_seed_index) # load dbs to memory with variable anim steps for the identified initial seed index
        #Constants.load_dbs_to_memory( initial_seed_index)
        #st.session_state['initial_seed'] = initial_seed_index
        (poss_opp_deck, _) = create_opponent_deck(opp_pool, initial_seed_index,opponent_name,player_card_ids_in_deck)
        opp_cards_to_play_order = generate_opponents_cards_to_play_order(opponent_id, poss_opp_deck, no_field_type)
        player_deck_shuffled = create_player_deck(player_card_ids_in_deck, initial_seed_index)
        player_deck_shuffled = get_card_data_from_card_ids(player_deck_shuffled)
        with st.expander("Player's deck"):
            df_player_deck_shuffled = pd.DataFrame(([o.to_dict() for o in player_deck_shuffled])).drop(columns=["Guardian Star", "Cards left in Opp Deck"])
            df_player_deck_shuffled.index = pd.RangeIndex(start=1, stop=len(df_player_deck_shuffled) + 1, name="Order")
            st.dataframe(df_player_deck_shuffled, width="stretch",row_height = 30,height=250,hide_index = False)

        
        with st.expander("Opponent's deck"):
            df_opp_cards = pd.DataFrame(([o.to_dict() for o in opp_cards_to_play_order])).drop(columns=["Guardian Stars"])
            df_opp_cards.index = pd.RangeIndex(start=1, stop=len(df_opp_cards) + 1, name="Order")
            st.dataframe(df_opp_cards, width="stretch",row_height = 30,height=250,hide_index = False)


# Section 4
with st.expander("3: Add actions"):
    if 'count_fusions' not in st.session_state:
        st.session_state['count_fusions'] = 0
    if 'count_traps' not in st.session_state:
        st.session_state['count_traps'] = 0
    if 'count_effective_attacks' not in st.session_state:
        st.session_state['count_effective_attacks'] = 0
    if 'count_equips' not in st.session_state:
        st.session_state['count_equips'] = 0
    if 'count_magics' not in st.session_state:
        st.session_state['count_magics'] = 0
    event_history = []

    enable_action_shortcuts()

    col1, col2, col3, col4 = st.columns(4)
    add_dump = col1.button('Dump (Alt+1)', key='action_add_btn_1', width='stretch')
    add_fusion = col2.button('Fusion (Alt+2)', key='action_add_btn_2', width='stretch')
    add_equip = col3.button('Equip (Alt+3)', key='action_add_btn_3', width='stretch')
    add_gs_animation = col4.button('G. Star Anim (Alt+4)', key='action_add_btn_4', width='stretch')
    if add_equip:
        add_event('EQUIP')
        st.session_state['count_equips'] += 1
    if add_dump:
        add_event('DUMP')
    if add_fusion:
        add_event('FUSION')
        st.session_state['count_fusions'] += 1
    if add_gs_animation:
        add_event('GS_ANIM')
    col1, col2, col3, col4 = st.columns(4, vertical_alignment='bottom')
    add_attack_def = col1.button('Attack card in DEF (Alt+5)', key='action_add_btn_5', width='stretch')
    was_def_card_destroyed = col2.selectbox('Attacked Card destroyed?', options=['Yes', 'No'], key='action_def_card_destroyed')
    if was_def_card_destroyed == 'No':
        def_attack_damage_to_lp = col3.selectbox('Damage to LP', options=['<1000', '>=1000', '0'], key='action_def_damage_to_lp')

    if add_attack_def:
        if was_def_card_destroyed == 'Yes':
            add_event('SWIPE_DEF')
            add_event('BURN')
        else:
            add_event('LOSE_ATTACK')
            if def_attack_damage_to_lp == '<1000':
                add_event('DIRECT_LOW')
            elif def_attack_damage_to_lp == '>=1000':
                add_event('DIRECT_HIGH')

    col1, col2, col3, col4 = st.columns(4, vertical_alignment='bottom')
    add_attack_atk_low = col1.button('Attack card ATK <1000 (Alt+6)', key='action_add_btn_6', width='stretch')
    add_attack_atk_high = col2.button('Attack card ATK >=1000 (Alt+7)', key='action_add_btn_7', width='stretch')
    was_atk_card_destroyed = col3.selectbox('Attacked Card destroyed?', options=['Yes', 'No'], key='action_atk_card_destroyed')
    add_attack_atk_tie = col4.button('Attack card ATK tie', key='action_add_btn_atk_tie', help='Attack card in ATK: tie (0 damage)', width='stretch')

    if add_attack_atk_high or add_attack_atk_low:
        attack_event = 'SWIPE_ATK_HIGH' if add_attack_atk_high else 'SWIPE_ATK_LOW'
        if was_atk_card_destroyed == 'No':
            add_event('LOSE_ATTACK')
        else:
            st.session_state['count_effective_attacks'] += 1
        add_event(attack_event)
        add_event('BURN')

    if add_attack_atk_tie:
        add_event('SWIPE_DEF')
        add_event('BURN')
        add_event('SWIPE_DEF')
        add_event('BURN')

    col1, col2, col3, col4 = st.columns(4, vertical_alignment='bottom')
    add_attack_lp = col1.button('Attack LP (Alt+8)', key='action_add_btn_8', width='stretch')
    direct_attack_damage = col2.selectbox('Direct attack damage', options=['>= 1000', '< 1000'], key='action_direct_attack_damage')

    col1, col2, col3, col4 = st.columns(4, vertical_alignment='bottom')
    
    add_change_field = col1.button('Change Field (Alt+9)', key='action_add_btn_9', width='stretch')
    field_type_selected = col2.selectbox('Field Type', options=['Mountain', 'Yami', 'Other'], key='action_change_field')
    trap_triggered = col3.button('Trap Triggered (Alt+0)', key='action_add_btn_10', width='stretch')

    

    if trap_triggered:
            add_event('TRAP_TRIGGERED')
            add_event('BURN')
            st.session_state['count_traps'] += 1    
    if add_attack_lp:
        add_event('DIRECT_HIGH' if direct_attack_damage == '>= 1000' else 'DIRECT_LOW')
    if add_change_field:
        st.session_state['count_magics'] += 1
        add_event({'Mountain': 'FIELD_MOUNT', 'Yami': 'FIELD_YAMI', 'Other': 'FIELD_USUAL'}[field_type_selected])
    
    events_input = st.text_input(" ",label_visibility='collapsed',placeholder="Use the buttons above to populate the events", key = "events_input")
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
    
    # Display history of events
    with st.expander("Event History"):
        if len(event_history) > 0 and initial_seed_index is not None:
            df_event_history = pd.DataFrame([{
                "Event ID": event.event_id,
                "Name": event.name,
                "Initial Seed Index": event.initial_seed_index,
                "New Seed Index": event.new_seed_index
            } for event in event_history])
            st.dataframe(df_event_history, width="stretch",hide_index = True)

        if len(event_history) > 0 and initial_seed_index is None:
            df_event_history = pd.DataFrame([{
                "Event ID": event.event_id,
                "Name": event.name
            } for event in event_history])
            st.dataframe(df_event_history, width="stretch",hide_index = True)


# Section 5
# with st.expander("Duel Rank calculator (optional)"):

#     st.info('''
# • Defensive wins: Player's card in Def mode is attacked and not destroyed.\n
# • Effective Attacks: Opponent card in atk mode is destroyed.\n
# • The checkbox freezes the value, so the reset button doesn't reset it.\n
# • The numbers after the labels are the values that change the duel rank points.'''        
#     )
#     # Initialize session_state only if not present
#     for k in Constants.duel_rank_keys:
#         if k not in st.session_state:
#             st.session_state[k] = Constants.duel_rank_defaults[k]
#         # Add a keep checkbox for each input
#         keep_key = f'keep_{k}'
#         if keep_key not in st.session_state:
#             st.session_state[keep_key] = False

#     reset_rank_calculator = st.button('reset', key='reset_rank_calculator')
#     if reset_rank_calculator:
#         for k in Constants.duel_rank_keys:
#             keep_key = f'keep_{k}'
#             if not st.session_state[keep_key]:
#                 st.session_state[k] = Constants.duel_rank_defaults[k]

#     with st.form("duel_rank_calculator_form",enter_to_submit=False,border=False):
#         col1, col2 = st.columns(2)
#         with col1:
#             cb, inp = st.columns([1, 30])
#             cb.write(" ")  # spacer for alignment
#             cb.write(" ")
#             cb.checkbox(" ", key='keep_num_fusions', label_visibility='collapsed')
#             inp.number_input("Fusions (1,5,10,15)", min_value=0, key='num_fusions')
#             cb, inp = st.columns([1, 30])
#             cb.write(" ")
#             cb.write(" ")
#             cb.checkbox(" ", key='keep_num_magics', label_visibility="collapsed")
#             inp.number_input("Magics (1,4,7,10)", min_value=0, key='num_magics')
#             cb, inp = st.columns([1, 30])
#             cb.write(" ")
#             cb.write(" ")
#             cb.checkbox(" ", key='keep_num_equips', label_visibility="collapsed")
#             inp.number_input("Equips (1,5,10,15)", min_value=0, key='num_equips')
#             cb, inp = st.columns([1, 30])
#             cb.write(" ")
#             cb.write(" ")
#             cb.checkbox(" ", key='keep_num_cards_left', label_visibility="collapsed")
#             inp.number_input("Cards left in your deck [complement of cards used] (31,27,7,3)", min_value=0, key='num_cards_left')
#             cb, inp = st.columns([1, 30])
#             cb.write(" ")
#             cb.write(" ")
#             cb.checkbox(" ", key='keep_num_facedowns', label_visibility="collapsed")
#             inp.number_input("Facedowns (1,11,21,31)", min_value=0, key='num_facedowns')
#         with col2:
#             cb, inp = st.columns([1, 30])
#             cb.write(" ")
#             cb.write(" ")
#             cb.checkbox(" ", key='keep_num_traps', label_visibility="collapsed")
#             inp.number_input("Traps (1,3,5,7)", min_value=0, key='num_traps')
#             cb, inp = st.columns([1, 30])
#             cb.write(" ")
#             cb.write(" ")
#             cb.checkbox(" ", key='keep_remaining_lp', label_visibility="collapsed")
#             inp.selectbox("Remaining Life Points",options=['8000','7000 - 7999','1000 - 6999','100 - 999','< 100'],key='remaining_lp')
#             cb, inp = st.columns([1, 30])
#             cb.write(" ")
#             cb.write(" ")
#             cb.checkbox(" ", key='keep_num_opp_cards_left', label_visibility="collapsed")
#             inp.number_input("Opponent cards left [complement of num of turns] (31,27,7,3)", min_value=0, key='num_opp_cards_left') # 9 turns equal 27 cards left in opp deck
#             cb, inp = st.columns([1, 30])
#             cb.write(" ")
#             cb.write(" ")
#             cb.checkbox(" ", key='keep_num_defensive_wins', label_visibility="collapsed")
#             inp.number_input("Defensive wins (2,6,10,15) ", min_value=0, key='num_defensive_wins')
#             cb, inp = st.columns([1, 30])
#             cb.write(" ")
#             cb.write(" ")
#             cb.checkbox(" ", key='keep_num_effectives', label_visibility="collapsed")
#             inp.number_input("Effective attacks (2,4,10,20) ", min_value=0, key='num_effectives')

        
#         if st.form_submit_button("Recalculate Duel Rank"):
#             duel_rank_points, duel_rank = calculate_duel_rank(
#                 st.session_state['num_fusions'],
#                 st.session_state['num_effectives'],
#                 st.session_state['num_facedowns'],
#                 st.session_state['num_magics'],
#                 st.session_state['num_equips'],
#                 st.session_state['num_traps'],
#                 40 - st.session_state['num_cards_left'], #To Do: verify this is a correct way to calculate used cards
#                 36 - st.session_state['num_opp_cards_left'], #To Do: verify this is a correct way to calculate number of turns
#                 st.session_state['num_defensive_wins'],
#                 st.session_state['remaining_lp']
#             )
#             st.write("Duel Rank Points:", duel_rank_points)
#             st.write("Duel Rank:", duel_rank)

# Section 6
with st.expander("4: Last Turn"):
    col1,col2,col3,col4 = st.columns([1,1,2,1],vertical_alignment='center')    
    battle_rank = col1.selectbox("Duel battle rank:", options=['SAPow','BCD','SATec'])    
    game_mode = col2.selectbox("Game mode:", options=['Normal (Vanilla)','15 Card Mod'], index=1)
    drop_pool_source = (opponent_name, battle_rank)
    if st.session_state.get('last_turn_drop_pool_source') != drop_pool_source:
        st.session_state['last_turn_drop_pool'] = st_read_pool(opponent_name, battle_rank)
        st.session_state['last_turn_drop_pool_source'] = drop_pool_source
    enemy_drop_pool = st.session_state['last_turn_drop_pool']
    enemy_drop_pool_card_ids = list(set(enemy_drop_pool)) # Unique card IDs in the drop pool
    enemy_drop_pool_card_ids.sort()
    enemy_drop_pool_cards = get_card_data_from_card_ids(enemy_drop_pool_card_ids)
    desired_drop_cards = col3.multiselect("Desired cards dropwdown:",[f"{card.cardID}: {card.name}" for card in enemy_drop_pool_cards],key='last_turn_desired_drop_cards', on_change=add_selected_drop_card_ids)
    desired_drop_card_ids = col4.text_input("Desired card IDs:",key='last_turn_desired_drop_card_ids',help="Enter ids space separated")


    if initial_seed_index is None:
        st.write('Identify initial seed index first, and then use this section for the last turn')

    
    input_method = st.radio("Choose Input Method. Simplified Mode is quicker to use but the search is not exhaustive",["Standard Mode","Simplified Mode"],horizontal = True)

    if initial_seed_index is not None and input_method == "Standard Mode":        
        my_cards_in_field = []
        for i in range(4):
            col1, col2, col3, col4, col5 = st.columns(5)
            selected_card_input = col1.selectbox(label = f'Field card {i + 1}',options=[f"{card['Id']}: {card['Name']}" for card in Constants.card_data if card['Type'] < 20], key=f"player_last_turn_field_card_{i}",index=None)
            if selected_card_input:
                num_equips = col3.number_input(f" Num of equips",min_value=0, max_value=10, key=f"eq_{i}", help="Megamorph adds 2 to the count")
                card = get_card_data_from_card_ids([int(selected_card_input.split(":")[0])])[0]
                guardian_star = col2.selectbox(f"Guardian Star", options=card.guardian_stars, key=f"gs_{i}")
                card.guardian_star = guardian_star
                card = add_equips(card,num_equips)
                my_cards_in_field.append(card)
        

        st.write('Your Hand')
        columns_last_turn_player_hand = st.columns(5)
        last_hand_card_ids = []
        for i in range(5):
            selected_card = columns_last_turn_player_hand[i].selectbox(label = ' ',label_visibility='collapsed', options=[f"{card.cardID}: {card.name}" for card in player_deck], key=f"player_last_turn_card_{i}",index=None,placeholder=f'Card {i + 1}')
            if selected_card:
                last_hand_card_ids.append(int(selected_card.split(":")[0]))
        hand = get_card_data_from_card_ids(last_hand_card_ids)
        
        col1, col2, col3, col4, col5 = st.columns(5, vertical_alignment='bottom')
        field_type = col1.selectbox("Field Type", options=[x[1] for x in Constants.field_types], key="last_turn_field_type")
        remaining_enemy_LP = col2.number_input("Opp Life Points",min_value = 0, max_value = 8000,key='last_turn_remaining_lp')
        field_type_id = [x[0] for x in Constants.field_types if x[1] == field_type][0]        
        standard_enemy_card_position = col3.selectbox("Opp card position", options=["Defense", "Attack"], key='last_turn_standard_enemy_card_position')
        standard_opp_remaining_cards = col4.number_input("Opp cards left", value=33, min_value=1, max_value=35, key='last_turn_standard_remaining_opp_cards')
        is_standard_enemy_card_in_atk = standard_enemy_card_position == "Attack"
        enemy_card = next((card for card in opp_cards_to_play_order if card.cards_left_in_opp_deck == standard_opp_remaining_cards), None)
        if enemy_card:
            st.write(f"Opp card: {enemy_card.name} ({enemy_card.attack}/{enemy_card.defense}) {enemy_card.guardian_star} (👍{Constants.guardian_star_weak_against[enemy_card.guardian_star]} /👎{Constants.guardian_star_strong_against[enemy_card.guardian_star]})")
        
        search = st.button("Search")

        if search and (remaining_enemy_LP == 0 or not enemy_card or not desired_drop_card_ids or len(hand) < 5):
            st.warning("Please provide all required information.")
            

        if search and remaining_enemy_LP > 0 and desired_drop_card_ids and enemy_card and len(hand) == 5:
            seed_index_at_start_of_last_turn = event_history[-1].new_seed_index
            main_phase_actions = generate_main_phase_actions(hand,my_cards_in_field,seed_index_at_start_of_last_turn,field_type_id,enemy_card)
            st.write(len(main_phase_actions), " possible Main Phase actions")
            plays = []
            search_start_time = datetime.now()
            found_drop = False
            
            #for attack_type in attack_types: 
            #    if not found_drop:
            for i,main_phase_action in enumerate(main_phase_actions):
                

                if found_drop:
                    break
                
                possible_battle_phase_actions = generate_attack_combinations_from_cards_in_field(enemy_card,remaining_enemy_LP,main_phase_action,is_standard_enemy_card_in_atk)
                
                for j,battle_phase_actions in enumerate(possible_battle_phase_actions):
                    play = Play(seed_index_at_start_of_last_turn,game_mode)
                    play.main_phase_action = main_phase_action
                    play.battle_phase_actions = battle_phase_actions                                   
                    play.calculate_drop(enemy_drop_pool)
                    #st.write(play)
                    if int(play.drop_card.cardID) in list(map(lambda x: int(x),desired_drop_card_ids.split(" "))):                                     
                        st.write("Found a way to get the desired drop!")
                        found_drop = True
                        break

            if not found_drop:
                st.write("No possible actions found to get the desired drop. Destroy enemy card and try again next turn.")
            else: 
                st.write(play)

    if initial_seed_index is not None and input_method == "Simplified Mode":        
        col1, col2, col3, col4, col5, col6, col7 = st.columns([1, 1, 1, 1.5, 1.2, 1.2, 1.8], vertical_alignment='bottom')
        max_fusions = col1.number_input("How many fusions can you make", min_value=0, max_value = 5,  value=1, key='max_fusions')
        max_equips = col2.number_input("How many equips can you make", min_value=0, max_value = 5,  value=0, key='max_equips')        
        max_drops = col3.number_input("How many drops can you make", min_value=0, max_value = 5,  value=3, key='max_drops')                
        is_gs_animation_possible = col4.selectbox(label = 'Guardian Star animation possible?',options=['No','Yes'],index=0,key='is_gs_animation_possible')
        is_gs_animation_possible = True if is_gs_animation_possible == 'Yes' else False
        simplified_enemy_card_position = col5.selectbox("Opponent's Card Position", options=["Defense", "Attack"], key='last_turn_simplified_enemy_card_position')
        simplified_opp_remaining_cards = col6.number_input("Cards left in Opp's deck", value=33, min_value=1, max_value=35, key='last_turn_simplified_remaining_opp_cards')
        is_simplified_enemy_card_in_atk = simplified_enemy_card_position == "Attack"
        simplified_enemy_card = next((card for card in opp_cards_to_play_order if card.cards_left_in_opp_deck == simplified_opp_remaining_cards), None)
        if simplified_enemy_card:
            col7.write(f"{simplified_enemy_card.name} ({simplified_enemy_card.attack}/{simplified_enemy_card.defense}) {simplified_enemy_card.guardian_star}")
        
        search = st.button('Search')
        if search and desired_drop_card_ids == '':
            st.warning("Please provide desired cards.")
        if search and desired_drop_card_ids != '':
            try:
                desired_drop_ids = [int(card_id) for card_id in desired_drop_card_ids.split()]
            except ValueError:
                st.warning("Please provide desired card IDs separated by spaces.")
            else:
                seed_index_at_start_of_last_turn = event_history[-1].new_seed_index
                plays_by_drop = search_simplified_plays(
                    seed_index_at_start_of_last_turn,
                    game_mode,
                    desired_drop_ids,
                    enemy_drop_pool,
                    max_fusions,
                    max_equips,
                    max_drops,
                    is_simplified_enemy_card_in_atk,
                    is_gs_animation_possible
                )
                total_plays = sum(len(plays) for plays in plays_by_drop.values())
                if total_plays == 0:
                    st.write("No possible actions found to get the desired drop. Destroy enemy card and try again next turn.")
                else:
                    st.write(f"Found {total_plays} possible action(s), with up to 10 options per desired drop.")
                    plays = [play for drop_plays in plays_by_drop.values() for play in drop_plays]
                    plays.sort(key=lambda play: (sum(play.main_phase_action.action_counts), play.main_phase_action.action_counts))
                    for play in plays:
                        num_fusions, num_equips, num_drops = play.main_phase_action.action_counts
                        title = f"Fusions: {num_fusions}, Drops: {num_drops}, Equips: {num_equips} - {play.drop_card.cardID}: {play.drop_card.name}"
                        with st.expander(title):
                            st.text(str(play))


# Fusion calculator
with st.expander("Fusion calculator (optional utility)"):
    selected_fusion_card_ids = []
    fusion_card_options = [f"{card['Id']}: {card['Name']}" for card in Constants.card_data]
    fusion_card_columns = st.columns(5)

    for index, column in enumerate(fusion_card_columns):
        selected_card = column.selectbox(
            f"Card {index + 1}",
            options=fusion_card_options,
            key=f"fusion_calculator_card_{index}",
            index=None,
            placeholder="Select a card",
        )
        if selected_card:
            selected_fusion_card_ids.append(int(selected_card.split(":", 1)[0]))

    if len(selected_fusion_card_ids) >= 2:
        selected_fusion_cards = get_card_data_from_card_ids(selected_fusion_card_ids)
        fusion_results = get_strongest_fusions_from_hand(selected_fusion_cards)

        if fusion_results:
            for fusion_combination, result in fusion_results:
                input_cards = [selected_fusion_cards[index] for index in fusion_combination]
                fusion_materials = " + ".join(
                    f"{card.cardID}: {card.name}" for card in input_cards
                )
                guardian_stars = " / ".join(result.guardian_stars)
                st.write(
                    f"{fusion_materials} = "
                    f"{result.cardID}: {result.name} ({result.attack}/{result.defense}) {guardian_stars}"
                )
        else:
            st.info("No valid fusions or equips found for the selected cards.")
    else:
        st.info("Select at least two cards to calculate fusions.")

    st.image("guardian_stars.png", width=400)