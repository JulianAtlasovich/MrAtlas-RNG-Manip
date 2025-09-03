import sqlite3
import pandas as pd
from collections import defaultdict

def search_card_by_name(search_query):
    try:
        conn = sqlite3.connect("FmDatabaseWithGS.db")
        query = """
            SELECT CardId as ID, CardName as Name 
            FROM CardInfo 
            WHERE CardName LIKE ?
        """
        df_search = pd.read_sql_query(query, conn, params=(f"%{search_query}%",))        
        return df_search
    except Exception as e:
        raise e
    finally:
        conn.close()


def get_cards_by_ids(card_ids):
    # Handle empty input explicitly
    if not card_ids:
        return pd.DataFrame(columns=["ID", "Name", "Type", "Attack", "Defense"])

    try:
        with sqlite3.connect("FmDatabaseWithGS.db") as conn:
            # Build a VALUES table with (pos, CardId) rows
            values_clause = ",".join(["(?, ?)"] * len(card_ids))
            params = []
            for pos, cid in enumerate(card_ids):
                params.extend([pos, cid])

            query = f"""
                WITH wanted(pos, CardId) AS (
                    VALUES {values_clause}
                )
                SELECT
                    wanted.pos,
                    c.CardId   AS ID,
                    c.CardName AS Name,
                    c.Type,
                    c.Attack,
                    c.Defense
                FROM wanted
                LEFT JOIN CardInfo c ON c.CardId = wanted.CardId
                ORDER BY wanted.pos
            """

            df = pd.read_sql_query(query, conn, params=params)
            return df.drop(columns=["pos"])
    except Exception as e:
        raise

def get_list_of_opponent_names():
    try:
        conn = sqlite3.connect("FmDatabaseWithGS.db")
        query = 'SELECT Duelist FROM DuelistInfo'
        df = pd.read_sql_query(query, conn)
        return df['Duelist'].tolist()  # Convert the 'Duelist' column to a list
    except Exception as e:
        raise e
    finally:
        conn.close()

def get_opponent_id_by_name(name):
    try:
        conn = sqlite3.connect("FmDatabaseWithGS.db")
        query = 'SELECT DuelistId FROM DuelistInfo WHERE Duelist = ?'
        c = conn.cursor()
        c.execute(query, (name,))
        result = c.fetchone()
        if result:
            return result[0]
        else:
            return None
    except Exception as e:
        raise e
    finally:
        conn.close()

def get_variable_anim_steps_from_db(index,anim_id):
    try:
        conn = sqlite3.connect("AnimationDatabase.db")
        query = 'select AdvanceSize from VariableAdvs where AnimationID = ? and InitialSeedIndex = ?'
        c = conn.cursor()
        c.execute(query, (anim_id,index))
        result = c.fetchone()
        if result:
            return result[0]
        else:
            return None
    except Exception as e:
        raise e
    finally:
        conn.close()

def find_fusion_db_old(card1,card2):
    try:
        conn = sqlite3.connect("FmDatabaseWithGS.db")
        query = """
            SELECT Result FROM Fusions
            WHERE (Material_1 = ? AND Material_2 = ?) OR (Material_1 = ? AND Material_2 = ?)
        """
        c = conn.cursor()
        c.execute(query, (card1, card2, card2, card1))
        result = c.fetchone()
        if result:
            return result[0]
        else:
            return None
    except Exception as e:
        raise e
    finally:
        conn.close()    


def find_fusion_db():
    fusion_map = {}
    try:
        conn = sqlite3.connect("FmDatabaseWithGS.db")
        query = "SELECT Material_1, Material_2, Result FROM Fusions"
        c = conn.cursor()
        c.execute(query)
        rows = c.fetchall()

        for m1, m2, result in rows:
            key = tuple(sorted((m1, m2)))  # ensure order doesn’t matter
            fusion_map[key] = result

        return fusion_map

    except Exception as e:
        raise e

    finally:
        conn.close()


def get_equips_db():
    card_equips = defaultdict(lambda: [])
    try:
        conn = sqlite3.connect("FmDatabaseWithGS.db")
        query = "select CardId,EquipId from EquipInfo"
        c = conn.cursor()
        c.execute(query)
        rows = c.fetchall()

        for CardId, EquipId in rows:
            card_equips[CardId].append(EquipId)

        return card_equips

    except Exception as e:
        raise e

    finally:
        conn.close()