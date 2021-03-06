import mysql.connector
from mysql.connector import errorcode, Error
from ConfigParser import ConfigParser
import json
 
DB_CONFIG_LOCATION = './db.config'

tableColumns = ['gameID', 'game_type', 'result', 'playerHero', 'playerTakedowns',
    'playerDeaths', 'playerHeroDamage', 'playerHealing', 'playerSiegeDamage',
    'playerStructureDamage', 'playerMinionDamage', 'playerSelfHealing',
    'playerDamageTaken', 'playerDamageSoaked', 'playerExperience', 'map',
    'talentChoice1', 'talentChoice2', 'talentChoice3', 'talentChoice4',
    'talentChoice5', 'talentChoice6', 'talentChoice7', 'alliedHero1',
    'alliedHero2', 'alliedHero3', 'alliedHero4', 'enemyHero1', 'enemyHero2',
    'enemyHero3', 'enemyHero4', 'enemyHero5']

class PlayerHeroGameData:
    
    def __init__(self):
        self._gameID = 0
        self.gameType = ''
        self.gameTimeUTC = ''
        self.result = ''
        self.map = ''
        self.playerHero = ''
        self.playerTakedowns = 0
        self.playerTakedowns = 0
        self.playerDeaths = 0
        self.playerHeroDamage = 0
        self.playerHealing = 0
        self.playerSiegeDamage = 0
        self.playerStructureDamage = 0
        self.playerMinionDamage = 0
        self.playerSelfHealing = 0
        self.playerDamageTaken = 0
        self.playerDamageSoaked = 0
        self.playerExperience = 0
        self.talentChoices = []
        self.alliedHeroes = []
        self.enemyHeroes = []
        
        
#TODO: sanitize the add statements based on the type limitations
createTableCommand = (
"CREATE TABLE `{}` ("
"   `gameID` INT AUTO_INCREMENT,"
"   `gameType` enum('Unranked', 'HeroLeague', 'TeamLeague', 'QuickMatch')," #will need to test these
"   `gameTimeUTC` DATETIME,"
"   `result` enum('W', 'L') NOT NULL,"
"    `map` VARCHAR(15),"
"   `playerHero` CHAR(20),"
"   `playerTakedowns` SMALLINT UNSIGNED,"
"    `playerDeaths` SMALLINT UNSIGNED,"
"    `playerHeroDamage` MEDIUMINT UNSIGNED,"
"    `playerHealing` MEDIUMINT UNSIGNED,"
"    `playerSiegeDamage` MEDIUMINT UNSIGNED,"
"    `playerStructureDamage` MEDIUMINT UNSIGNED,"
"    `playerMinionDamage` MEDIUMINT UNSIGNED,"
"    `playerSelfHealing` MEDIUMINT UNSIGNED,"
"    `playerDamageTaken` MEDIUMINT UNSIGNED,"
"    `playerDamageSoaked` MEDIUMINT UNSIGNED,"
"    `playerExperience` MEDIUMINT UNSIGNED,"
"    `talentChoice1` VARCHAR(40),"
"    `talentChoice2` VARCHAR(40),"
"    `talentChoice3` VARCHAR(40),"
"    `talentChoice4` VARCHAR(40),"
"    `talentChoice5` VARCHAR(40),"
"    `talentChoice6` VARCHAR(40),"
"    `talentChoice7` VARCHAR(40),"
"    `alliedHero1` CHAR(20),"
"    `alliedHero2` CHAR(20),"
"    `alliedHero3` CHAR(20),"
"    `alliedHero4` CHAR(20),"
"    `enemyHero1` CHAR(20),"
"    `enemyHero2` CHAR(20),"
"    `enemyHero3` CHAR(20),"
"    `enemyHero4` CHAR(20),"
"    `enemyHero5` CHAR(20),"
"   PRIMARY KEY (`gameID`)) ENGINE=InnoDB")

add_game = ("INSERT INTO `{}` "
            "(result, playerHero, playerTakedowns,"
            "playerDeaths, playerHeroDamage, playerHealing, playerSiegeDamage, playerStructureDamage,"
            "playerMinionDamage, playerSelfHealing, playerDamageTaken,"
            "playerDamageSoaked, playerExperience) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)")

class GameSQLConnector:

    def __init__(self, debug=False):
        self.debug = debug
        self.conn = self.connect()
        self.cursor = self.conn.cursor()
        self.setDefaultDatabase()
                
    def execute(self, statement):
        if self.debug:
            print(statement)
        self.cursor.execute(statement)
        self.conn.commit()
        
    def create_database(self):
        try:
            self.cursor.execute("CREATE DATABASE {} DEFAULT CHARACTER SET 'utf8'".format(self.DB_NAME))
        except mysql.connector.Error as err:
            print("Failed creating database: {}".format(err))
            exit(1)

    def createTable(self, table_name):
        table_name = table_name[0:63] # trim to max length 64 characters
        formattedCommand = createTableCommand.format(table_name)
        print("Creating table {}:".format(table_name))
        try:
            self.cursor.execute(formattedCommand)
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_TABLE_EXISTS_ERROR:
                print("already exists.")
            else:
                print(err.msg)
        else:
            print("Success!")

    def close(self):
        self.cursor.close()
        self.conn.close()

    def connect(self):
        try:
            configData = {}
            with open(DB_CONFIG_LOCATION, 'r') as f:
                configData = json.load(f)
            self.conn = mysql.connector.connect(host=configData['host'], database=configData['database'],
                user=configData['user'], password=configData['password'])
            self.DB_NAME = configData['database']
            if self.conn.is_connected():
                print('connected to MySQL database!')
                return self.conn
            else:
                print('connection failed')
                exit(0)
        except Error as e:
            print(e)
            exit(0)

    def setDefaultDatabase(self):
        try:
            self.cursor.execute("USE {}".format(self.DB_NAME))
        except mysql.connector.Error as err:
            print("Database {} does not exists.".format(self.DB_NAME))
            if err.errno == errorcode.ER_BAD_DB_ERROR:
                self.create_database()
                print("Database {} created successfully.".format(self.DB_NAME))
            else:
                print(err)
                exit(1)

    def addHeroData(self, game_data, playerDatabaseID):
        self.createTable(playerDatabaseID)
        print(game_data)
        self.cursor.execute(add_game.format(playerDatabaseID), game_data)
        gameId = self.cursor.lastrowid
        self.conn.commit()
        return gameId
    
    def addDateTime(self, dateTime, gameID, playerDatabaseID):
        addDateTimeStatement = ("UPDATE `{}` SET gameTimeUTC = %s WHERE gameID = %s").format(playerDatabaseID)
        data = (dateTime, gameID)
        self.cursor.execute(addDateTimeStatement, data)
        self.conn.commit()

    def addMap(self, mapName, gameID, playerDatabaseID):
        mapName = mapName[0:15]
        data = (mapName, gameID)
        addMapStatement = ("UPDATE `{}` SET map = %s WHERE gameID = %s").format(playerDatabaseID)
        self.cursor.execute(addMapStatement, data)
        self.conn.commit()
        
    def addGameType(self, gameType, gameID, playerDatabaseID):
        addGameTypeStatement = ("UPDATE `{}` SET gameType = '{}' WHERE gameID = {}").format(playerDatabaseID, gameType, gameID)
        print(addGameTypeStatement)
        self.cursor.execute(addGameTypeStatement)
        self.conn.commit()

    def addTalentChoices(self, talents, gameID, playerDatabaseID):
        if len(talents) == 0:
            return
        baseStatement = ("UPDATE `{}` SET ").format(playerDatabaseID)
        for i in range(0, len(talents)):
            baseStatement = baseStatement + " talentChoice{} = '{} '".format(i + 1, talents[i])
            if i != len(talents) - 1:
                baseStatement = baseStatement + ","
        baseStatement = baseStatement + " WHERE gameID = {}".format(gameID)
        self.cursor.execute(baseStatement)
        self.conn.commit()

    def addAlliedHeroes(self, allyArray, gameID, playerDatabaseID):
        addAlliedHeroesStatement = ("UPDATE `{}` "
            "SET alliedHero1 = '{}', "
            "alliedHero2 = '{}', "
            "alliedHero3 = '{}', "
            "alliedHero4 = '{}' "
            "WHERE gameID = {}").format(playerDatabaseID, allyArray[0], allyArray[1],
            allyArray[2], allyArray[3], gameID)
        print(addAlliedHeroesStatement)
        self.cursor.execute(addAlliedHeroesStatement)
        self.conn.commit()

    def addEnemyHeroes(self, enemyArray, gameID, playerDatabaseID):
        addEnemyHeroesStatement = ("UPDATE `{}` "
            "SET enemyHero1 = '{}', "
            "enemyHero2 = '{}', "
            "enemyHero3 = '{}', "
            "enemyHero4 = '{}', "
            "enemyHero5 = '{}' "
            "WHERE gameID = {}").format(playerDatabaseID, enemyArray[0], enemyArray[1],
            enemyArray[2], enemyArray[3], enemyArray[4], gameID)
        #print(addEnemyHeroesStatement)
        self.cursor.execute(addEnemyHeroesStatement)
        self.conn.commit()

    def queryDataAverage(self, playerDatabaseID, item):
        someStatement = "SELECT AVG({}) 'avgPlayerHeroDamage' FROM heroes.p_midreadias_67731;".format(item)
        self.cursor.execute(someStatement)

        for (avgPlayerHeroDamage) in self.cursor:
            print("this player average hero damage is {}").format(avgPlayerHeroDamage)
            return avgPlayerHeroDamage

    def queryDataAverageForHero(self, playerDatabaseID, item, hero):
        someStatement = "SELECT AVG({}) 'avgPlayerHeroDamage' FROM heroes.p_midreadias_67731 WHERE playerHero = {};".format(item, hero)
        self.cursor.execute(someStatement)

        for (avgPlayerHeroDamage) in self.cursor:
            print("this player average hero damage is {}").format(avgPlayerHeroDamage)
            return avgPlayerHeroDamage

