from rng_core import *
import sqlite3
from datetime import datetime





def create_table():
  conn = sqlite3.connect('FmDatabase.db')
  c = conn.cursor()

  c.execute('CREATE TABLE DeckOrders (SeedIndex INTEGER, Seed INTEGER, Card0 INTEGER,Card1 INTEGER,Card2 INTEGER,Card3 INTEGER,Card4 INTEGER,Card5 INTEGER,Card6 INTEGER,Card7 INTEGER,Card8 INTEGER,Card9 INTEGER,Card10 INTEGER,Card11 INTEGER,Card12 INTEGER,Card13 INTEGER,Card14 INTEGER,Card15 INTEGER,Card16 INTEGER,Card17 INTEGER,Card18 INTEGER,Card19 INTEGER,Card20 INTEGER,Card21 INTEGER,Card22 INTEGER,Card23 INTEGER,Card24 INTEGER,Card25 INTEGER,Card26 INTEGER,Card27 INTEGER,Card28 INTEGER,Card29 INTEGER,Card30 INTEGER,Card31 INTEGER,Card32 INTEGER,Card33 INTEGER,Card34 INTEGER,Card35 INTEGER,Card36 INTEGER,Card37 INTEGER,Card38 INTEGER,Card39 INTEGER)')

  conn.commit()
  conn.close()

#create_table()


def insert_db():
  deck = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39]
  queries = []
  seeds_to_insert = 300000
  conn = sqlite3.connect('FmDatabase.db')
  c = conn.cursor()

  with open('seeds_list.txt') as f:
      lines = f.read().splitlines()
  print('done reading file')
  for i in range(seeds_to_insert):
    
    if i % (seeds_to_insert/100) == 0:
      now = datetime.now()
      current_time = now.strftime("%H:%M:%S")
      print(str(i/(seeds_to_insert/100))+'%',current_time)
    
    seed = int(lines[i])
    shuffled_deck = shuffle_copy(deck,seed)
    queries.append([i,seed,shuffled_deck[0],shuffled_deck[1],shuffled_deck[2],shuffled_deck[3],shuffled_deck[4],shuffled_deck[5],shuffled_deck[6],shuffled_deck[7],shuffled_deck[8],shuffled_deck[9],shuffled_deck[10],shuffled_deck[11],shuffled_deck[12],shuffled_deck[13],shuffled_deck[14],shuffled_deck[15],shuffled_deck[16],shuffled_deck[17],shuffled_deck[18],shuffled_deck[19],shuffled_deck[20],shuffled_deck[21],shuffled_deck[22],shuffled_deck[23],shuffled_deck[24],shuffled_deck[25],shuffled_deck[26],shuffled_deck[27],shuffled_deck[28],shuffled_deck[29],shuffled_deck[30],shuffled_deck[31],shuffled_deck[32],shuffled_deck[33],shuffled_deck[34],shuffled_deck[35],shuffled_deck[36],shuffled_deck[37],shuffled_deck[38],shuffled_deck[39]])


  c.executemany('INSERT INTO DeckOrders VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',queries)

  conn.commit()
  conn.close()

  print('done')  




# create_table()
# insert_db()
