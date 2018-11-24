import mpyq
import json
from importlib import import_module
from sqlconnector import GameSQLConnector
import sqlconnector
import io
import sys
import argparse

sys.path.insert(0, './heroprotocol')

from hotsparser import *
import protocol67985 as protocol

commandLineArgs = sys.argv[1:]

def addPlayerData(replay, playerBattleTag):
    print(replay.replayInfo.startTime) # TODO: add start time to the database
    print(replay.players)
    players = replay.players
    player = findPlayer(replay, playerBattleTag) # Player object
    playerSlot = player.id
    print("found player: " + playerBattleTag + " in slot " + str(playerSlot))
    
    heroPlayers = replay.heroList
    print(replay.heroList)
    heroPlayer = heroPlayers[playerSlot]
    heroPlayerStats = heroPlayer.generalStats
    basicData = (convertResult(player.gameResult), player.hero, 
                heroPlayerStats['Takedowns'], heroPlayerStats['Deaths'], heroPlayerStats['HeroDamage'],
                heroPlayerStats['Healing'], heroPlayerStats['SiegeDamage'], heroPlayerStats['StructureDamage'],
                heroPlayerStats['MinionDamage'], heroPlayerStats['SelfHealing'], heroPlayerStats['DamageTaken'],
                heroPlayerStats['DamageSoaked'], heroPlayerStats['ExperienceContribution'])
    
    gameSQLConnector = GameSQLConnector()
    gameSQLConnector.addHeroData(basicData, playerBattleTag)
    
def convertResult(gameResult):
    if gameResult == 1: # win condition
        return 1
    if gameResult == 2: # loss condition
        return 2
                 
def findPlayer(replay, playerBattleTag):
    for number in replay.players:
        player = replay.players[number]
        if player.battleTag == playerBattleTag:
            return player
    raise ValueError('couldn\'t find a matching player')
        
if __name__ == "__main__":
    requestedPlayerName = '';
    if len(commandLineArgs) == 3:
        requestedPlayerName = commandLineArgs[0]
        print("Looking for replays with player name " + requestedPlayerName)
        playerName = commandLineArgs[0]
        if commandLineArgs[1] == 'add':
            replayFilePath = commandLineArgs[2]

            archive = mpyq.MPQArchive(replayFilePath)

            #Parse the header
            header = protocol.decode_replay_header(archive.header['user_data_header']['content'])
            build_number = header['m_version']['m_baseBuild']

            # Get the actual protocol number
            module_name = 'protocol{}'.format(build_number)
            protocol = import_module(module_name)

            replay = processEvents(protocol, archive)

            addPlayerData(replay, requestedPlayerName)
        if commandLineArgs[1] == 'poll':
            databaseID = sqlconnector.getPlayerDatabaseID(commandLineArgs[0], commandLineArgs[2])
            gameSQLConnector = GameSQLConnector()
            dictionary = gameSQLConnector.queryData(databaseID, "")
            print(dictionary)
    else:
        print("Please use one of the following commands")
        print("uses: test.py [playername] [add] [replayFilePath]")
        print("uses: test.py [playername] [poll] [id]")


'''
details: 
 timeline stuff:
 team level ups, player deaths, building deaths, camp captures
 
 players:
 battletags, regions and stuff

 team:
 nothing useful

 heroes:
 has the useful stats, but i'll have to filter the stuff for the things I actually want

 units: 
 mostly useless 
'''