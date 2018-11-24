import mysql.connector
from mysql.connector import errorcode, Error
from ConfigParser import ConfigParser
 
DB_NAME = 'heroes'
PLAYER_PREFIX = 'P_{}_{}'

tableColumns = ['game_id', 'game_type', 'result', 'playerHero', 'playerTakedowns',
    'playerDeaths', 'playerHeroDamage', 'playerHealing', 'playerSiegeDamage',
    'playerStructureDamage', 'playerMinionDamage', 'playerSelfHealing',
    'playerDamageTaken', 'playerDamageSoaked', 'playerExperience', 'map',
    'talentChoice1', 'talentChoice2', 'talentChoice3', 'talentChoice4',
    'talentChoice5', 'talentChoice6', 'talentChoice7', 'alliedHero1',
    'alliedHero2', 'alliedHero3', 'alliedHero4', 'enemyHero1', 'enemyHero2',
    'enemyHero3', 'enemyHero4', 'enemyHero5']

createTableCommand = (
"CREATE TABLE `{}` ("
"   `game_id` INT AUTO_INCREMENT,"
"   `game_type` enum('HeroLeague', 'QuickPlay', 'TeamLeague', 'Other'),"
"   `result` enum('W', 'L') NOT NULL,"
"   `playerHero` CHAR(20),"
"   `playerTakedowns` SMALLINT UNSIGNED,"
"    `playerDeaths` SMALLINT UNSIGNED,"
"    `playerHeroDamage` SMALLINT UNSIGNED,"
"    `playerHealing` SMALLINT UNSIGNED,"
"    `playerSiegeDamage` MEDIUMINT UNSIGNED,"
"    `playerStructureDamage` MEDIUMINT UNSIGNED,"
"    `playerMinionDamage` MEDIUMINT UNSIGNED,"
"    `playerSelfHealing` MEDIUMINT UNSIGNED,"
"    `playerDamageTaken` MEDIUMINT UNSIGNED,"
"    `playerDamageSoaked` MEDIUMINT UNSIGNED,"
"    `playerExperience` MEDIUMINT UNSIGNED,"
"    `map` VARCHAR(15),"
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
"   PRIMARY KEY (`game_id`)) ENGINE=InnoDB")

add_game = ("INSERT INTO `{}` "
            "(result, playerHero, playerTakedowns,"
            "playerDeaths, playerHeroDamage, playerHealing, playerSiegeDamage, playerStructureDamage,"
            "playerMinionDamage, playerSelfHealing, playerDamageTaken,"
            "playerDamageSoaked, playerExperience) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)")

def getPlayerDatabaseID(player_name, player_id):
    return PLAYER_PREFIX.format(player_name, player_id)

class GameSQLConnector:

    def __init__(self):
        self.conn = self.connect()
        self.cursor = self.conn.cursor()
    
        try:
            self.cursor.execute("USE {}".format(DB_NAME))
        except mysql.connector.Error as err:
            print("Database {} does not exists.".format(DB_NAME))
            if err.errno == errorcode.ER_BAD_DB_ERROR:
                create_database()
                print("Database {} created successfully.".format(DB_NAME))
            else:
                print(err)
                exit(1)
        
    def create_database(self):
        try:
            self.cursor.execute("CREATE DATABASE {} DEFAULT CHARACTER SET 'utf8'".format(DB_NAME))
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
            self.conn = mysql.connector.connect(host='localhost', database='heroes',
                user='root', password='ch1c0b0s')
            if self.conn.is_connected():
                print('connected to MySQL database!')
                return self.conn
            else:
                print('connection failed')
                exit(0)
        except Error as e:
            print(e)
            exit(0)


    def addHeroData(self, game_data, playerDatabaseID):
        self.createTable(playerDatabaseID)
        print(game_data)
        self.cursor.execute(add_game.format(playerDatabaseID), game_data)
        gameId = self.cursor.lastrowid
        self.conn.commit()
        return gameId

    def addMap(self, mapName, game_id, playerDatabaseID):
        addMapStatement = ("UPDATE {}.{} SET map = '{}' WHERE game_id = {}").format(DB_NAME, playerDatabaseID, mapName, game_id)
        self.cursor.execute(addMapStatement)
        self.conn.commit()

    def addTalentChoices(self, talents, game_id, playerDatabaseID):
        if len(talents) == 0:
            return
        baseStatement = ("UPDATE {}.{} SET ").format(DB_NAME, playerDatabaseID)
        for i in range(0, len(talents)):
            baseStatement = baseStatement + " talentChoice{} = '{} '".format(i + 1, talents[i])
            if i != len(talents) - 1:
                baseStatement = baseStatement + ","
        baseStatement = baseStatement + " WHERE game_id = {}".format(game_id);
        self.cursor.execute(baseStatement)
        self.conn.commit()

    def addAlliedHeroes(self, allyArray, game_id, playerDatabaseID):
        addAlliedHeroesStatement = ("UPDATE {}.{} "
            "SET alliedHero1 = '{}', "
            "alliedHero2 = '{}', "
            "alliedHero3 = '{}', "
            "alliedHero4 = '{}' "
            "WHERE game_id = {}").format(DB_NAME, playerDatabaseID, allyArray[0], allyArray[1],
            allyArray[2], allyArray[3], game_id)
        #print(addAlliedHeroesStatement)
        self.cursor.execute(addAlliedHeroesStatement)
        self.conn.commit()

    def addEnemyHeroes(self, enemyArray, game_id, playerDatabaseID):
        addEnemyHeroesStatement = ("UPDATE {}.{} "
            "SET enemyHero1 = '{}', "
            "enemyHero2 = '{}', "
            "enemyHero3 = '{}', "
            "enemyHero4 = '{}', "
            "enemyHero5 = '{}' "
            "WHERE game_id = {}").format(DB_NAME, playerDatabaseID, enemyArray[0], enemyArray[1],
            enemyArray[2], enemyArray[3], enemyArray[4], game_id)
        print(addEnemyHeroesStatement)
        self.cursor.execute(addEnemyHeroesStatement)
        self.conn.commit()

    def queryDataAverage(self, playerDatabaseID, item):
        someStatement = "SELECT AVG({}}) 'avgPlayerHeroDamage' FROM heroes.p_midreadias_67731;".format(item)
        self.cursor.execute(someStatement)

        for (avgPlayerHeroDamage) in self.cursor:
            print("this player average hero damage is {}").format(avgPlayerHeroDamage)
            return avgPlayerHeroDamage

    def queryDataAverageForHero(self, playerDatabaseID, item, hero):
        someStatement = "SELECT AVG({}}) 'avgPlayerHeroDamage' FROM heroes.p_midreadias_67731 WHERE playerHero = {};".format(item, hero)
        self.cursor.execute(someStatement)

        for (avgPlayerHeroDamage) in self.cursor:
            print("this player average hero damage is {}").format(avgPlayerHeroDamage)
            return avgPlayerHeroDamage

#         UPDATE customers
# SET state = 'California',
#     customer_rep = 32
# WHERE customer_id > 100;