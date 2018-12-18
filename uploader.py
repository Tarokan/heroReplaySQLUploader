import mpyq
from importlib import import_module
from sqlconnector import GameSQLConnector
import sqlconnector
import sys
import argparse
import os
import re
import logging
import time

logDirectory = './logs/'

logging.basicConfig(filename=logDirectory + (str(int(round(time.time() * 1000))) + '.log'), 
                    filemode='w', 
                    format='%(asctime)s - %(levelname)s - %(message)s', 
                    level=logging.DEBUG)
logging.info('Beginning uploading session')

sys.path.insert(0, './heroprotocol')
from hotsparser import *
import protocol67985 as protocol

commandLineArgs = sys.argv[1:]
sanitizeRegex = re.compile('[^a-zA-Z0-9]')

def addPlayerData(replay, playerBattleTag):
    print(str(replay.replayInfo))
    players = replay.players
    player = findPlayer(replay, playerBattleTag) # Player object
    playerSlot = player.id
    print("found player: " + playerBattleTag + " in slot " + str(playerSlot))
    
    heroPlayers = replay.heroList
    #print(replay.heroList)
    heroPlayer = heroPlayers[playerSlot]
    heroPlayerStats = heroPlayer.generalStats
    #print(heroPlayerStats)
    basicData = (convertResult(player.gameResult), 
                player.hero, 
                heroPlayerStats.get('Takedowns', 0), 
                heroPlayerStats.get('Deaths', 0), 
                heroPlayerStats.get('HeroDamage', 0),
                heroPlayerStats.get('Healing', 0), 
                heroPlayerStats.get('SiegeDamage', 0), 
                heroPlayerStats.get('StructureDamage', 0),
                heroPlayerStats.get('MinionDamage', 0), 
                heroPlayerStats.get('SelfHealing', 0), 
                heroPlayerStats.get('DamageTaken', 0),
                heroPlayerStats.get('DamageSoaked', 0), 
                heroPlayerStats.get('ExperienceContribution', 0))
    
    gameSQLConnector = GameSQLConnector()
    try:
        entryid = gameSQLConnector.addHeroData(basicData, playerBattleTag)
        gameSQLConnector.addAlliedHeroes(getTeam(replay, playerBattleTag, True), entryid, playerBattleTag)
        gameSQLConnector.addEnemyHeroes(getTeam(replay, playerBattleTag, False), entryid, playerBattleTag)
        gameSQLConnector.addTalentChoices(getTalentChoices(replay, playerSlot), entryid, playerBattleTag)
        gameSQLConnector.addDateTime(replay.replayInfo.startTime, entryid, playerBattleTag)
        gameSQLConnector.addMap(sanitize(replay.replayInfo.mapName), entryid, playerBattleTag)
        gameSQLConnector.addGameType(sanitize(replay.replayInfo.gameType), entryid, playerBattleTag)
        print("Uploaded data succesfully!")
        log_info("replay data uploaded successfully")
    except Exception as e:
        print("*** exception occurred, check log")
        print(e)
        logging.exception("Exception occurred")
    
def convertResult(gameResult):
    if gameResult == 1: # win condition
        return 1
    if gameResult == 2: # loss condition
        return 2

def getTalentChoices(replay, playerSlot):
    talents = []
    for talent in replay.heroList[playerSlot].generalStats['pickedTalents']:
        talents.append(sanitize(talent['talent_name'][0:40]))
    return talents

# consider using slot instead of player Battle Tag
def getTeam(replay, playerBattleTag, getAllies):
    player = findPlayer(replay, playerBattleTag)
    teammateHeroes = []
    for number in replay.players:
        otherPlayer = replay.players[number]
        if ((player.team == otherPlayer.team) == getAllies) and (player != otherPlayer):
            teammateHeroes.append(sanitize(otherPlayer.hero))
    print(teammateHeroes)
    return teammateHeroes

def sanitize(string):
    return sanitizeRegex.sub('', string)
                 
def findPlayer(replay, playerBattleTag):
    for number in replay.players:
        player = replay.players[number]
        if player.battleTag == playerBattleTag:
            return player
    raise ValueError('couldn\'t find a matching player')

def uploadReplay(replayPath, targetBattleTag):
    
    logging.info('opening replay MPQ at {}'.format(replayPath))
    archive = mpyq.MPQArchive(replayPath)
    import protocol67985 as protocol
    # TODO: catch exceptions
    #Parse the header 
    header = protocol.decode_replay_header(archive.header['user_data_header']['content'])
    build_number = header['m_version']['m_baseBuild']
    logging.info('replay protocol build_number: {}'.format(build_number))

    # Get the actual protocol number
    module_name = 'protocol{}'.format(build_number)
    
    # TODO: catch exception when protocol hasn't been updated yet
    protocol = import_module(module_name)
    
    print(replayPath)
    try:
        log_info("running through the parser")
        replay = processEvents(protocol, archive)
        addPlayerData(replay, targetBattleTag)
    except ValueError:
        pass

# don't fix user input, just report an error
def verifyBattleTag(rawBattleTag):
    '''
    Returns false if it's not alphanumeric (no accents), and first letter is not 0.
    '''
    
    # replace this with bnet oauth battletag in a production environment 
    # this does not allow for accents
    bnetRegex = re.compile('[^a-zA-Z0-9#]')
    return (bnetRegex.sub('', rawBattleTag) == rawBattleTag
        and not rawBattleTag[0].isdigit()
        and len(rawBattleTag.split('#')) == 2
        and rawBattleTag.split('#')[1].isdigit())

def log_info(string):
    logging.info(string)

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser()
    parser.add_argument('playerBattleTag')
    parser.add_argument('inputPath')
    parser.add_argument('-d', '--is-directory', help='Tells the parser to search the directory and upload all replays', action='store_true', default=False)
    parser.add_argument('-f', '--is-replayfile', help='Tells the parser the input path is a replay', action='store_true', default=False)
    parser.add_argument('-r', '--remove-table', help='Tells the parser to drop/remove the table', action='store_true', default=False)
    args = parser.parse_args()
    
    playerBattleTag = args.playerBattleTag;
    if not verifyBattleTag(playerBattleTag):
        print('invalid battletag')
        logging.info('Bad battletag: {}, exiting'.format(playerBattleTag))
        exit(0)
        
    inputPath = args.inputPath
    
    print("Looking for replays with player BattleTag " + playerBattleTag)
    
    if (args.is_replayfile):
        logging.info('file specified: {}'.format(inputPath))
        uploadReplay(inputPath, playerBattleTag)
    elif (args.is_directory):
        logging.info('directory specified: {}'.format(inputPath))
        for file in os.listdir(inputPath):
            if file.endswith('.StormReplay'):
                logging.info('found file: {}'.format(file))
                uploadReplay(inputPath + "\\" + file, playerBattleTag)
            else:
                logging.info('skipped file not ending in .StormReplay: {}'.format(file))
                print("skipping {}.".format(file))
                

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