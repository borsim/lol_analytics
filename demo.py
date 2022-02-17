import json
import numpy as np
import matplotlib.pyplot as plt

# The rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of this software
# are only provided through the author's written permission. Please contact the author with any inquiries.
# This code deals with data from a closed, commerical API of bayesesports.com
# While I normally MIT license my other code on GitHub, I would like access to this API beyond the sample I got.


datafile = open('./dump.json', 'r')
jsonData = json.load(datafile)
# Structure: 'events': [{... , 'payload': {urn: 123, 'payload': {..., action:'ANNOUNCE', 'payload':}}   }]
#print(len(jsonData['events']))
#print(jsonData['events'][3000]['payload']['payload']['payload'].keys())
allEvents = jsonData['events']
drakeKillTimes = []
# Dragon center = [9866, 4414]
drakeSpawnTimes = []

typeSortedEvents = {}

def positionDistance(pos1: dict, pos2: dict):
    return np.sqrt(pow(pos2[0] - pos1[0], 2) + pow(pos2[1] - pos1[1], 2))

def msecToDisplayTimestamp(gameTime: int):
    placedAtMinutes = int(np.floor(gameTime / 60000.0))
    placedAtSeconds = int(np.floor((gameTime % 60000.0) / 1000.0))
    if placedAtMinutes < 10:
        placedAtMinutes = '0' + str(placedAtMinutes)
    if placedAtSeconds < 10:
        placedAtSeconds = '0' + str(placedAtSeconds)
    return (str(placedAtMinutes) + ':' + str(placedAtSeconds))



# Not pretty but saves me from remembering keys
def eventKeystoType(eventKeys: str):
    if eventKeys == 'fixture,teams':
        return 'team_fixture'
    elif eventKeys == 'teamUrn,championId':
        return 'team_banning'
    elif eventKeys == 'pickTurn,teamOne,teamTwo,bannedChampions':
        return 'team_picking'
    elif eventKeys == 'playerUrn,teamUrn,championId':
        return 'team_champion'
    elif eventKeys == 'gameTime':
        return 'game_tick'
    elif eventKeys == 'gameTime,teamUrn,towersKilled,championsKilled,totalGold':
        return 'team_global_score_update'
    elif eventKeys == 'gameTime,matchCurrent':
        return 'game_current_match' 
    elif eventKeys == 'gameTime,positions':
        return 'all_positions_update'
    elif eventKeys == 'gameID,esportsGameID,platformID,name,references,gameVersion,playbackId,sequenceIndex,lastUpdateTime,seriesStatus,gameState,gameTime,gameMode,gameOver,paused,winningTeam,winningTeamUrn,teamOne,teamTwo':
        return 'game_paused'
    elif eventKeys == 'gameTime,monsterType,dragonType,spawnGameTime':
        return 'dragon_spawn'
    elif eventKeys == 'gameTime,playerUrn,teamUrn,item':
        return 'item_bought'
    elif eventKeys == 'gameTime,position,wardType,placerUrn,placerTeamUrn':
        return 'ward_placed'
    elif eventKeys == 'gameTime,position,killerTeamUrn,killerUrn,monsterType,dragonType,assistants':
        return 'monster_killed'
    elif eventKeys == 'gameTime,playerUrn,teamUrn,newValue':
        return 'new_player'
    elif eventKeys == 'gameTime,position,killerUrn,killerTeamUrn,victimUrn,victimTeamUrn,assistants':
        return 'champion_killed'
    elif eventKeys == 'gameTime,position,killerTeamUrn,killerUrn,killType,killStreak':
        return 'multikill__or_killstreak'
    elif eventKeys == 'gameTime,position,playerUrn,teamUrn':
        return 'single_position_update'
    elif eventKeys == 'gameTime,monsterType,dragonType':
        return 'dragon_type'
    elif eventKeys == 'gameTime,position,killerUrn,killerTeamUrn,buildingType,buildingTeamUrn,lane,turretTier,assistantss':
        return 'building_killed'
    elif eventKeys == 'gameTime,position,wardType,placerUrn,placerTeamUrn,killerUrn,killerTeamUrn':
        return 'ward_destroyed'
    elif eventKeys == 'gameTime,matchCurrent,winningTeamUrn':
        return 'game_end'

for e in allEvents:
    actualData = e['payload']['payload']['payload']
    currentEventKeys = ','.join(list(actualData.keys()))
    simplifiedKey = eventKeystoType(currentEventKeys)
    if simplifiedKey in typeSortedEvents:
        typeSortedEvents[simplifiedKey].append(actualData)
    else:
        typeSortedEvents[simplifiedKey] = [actualData]

# Track ward placements
wardDestroyedEvents = typeSortedEvents['ward_destroyed']
wardPlacedEvents = typeSortedEvents['ward_placed']
for e in wardPlacedEvents:
    wardType = e['wardType'] + '\t' if len(e['wardType']) < 8 else e['wardType']
    #print('{} \tward placed at {} \tin position {}'.format(wardType, msecToDisplayTimestamp(e['gameTime']), e['position']))

# Track types and times of dragon spawns
# Number of wards placed in the minute before drake spawn up to drake kill
# and number of wards killed in the same period
dragonSpawnEvents = typeSortedEvents['dragon_spawn']
for e in dragonSpawnEvents:
    gameTime = e['gameTime']
    dragonType = e['dragonType']
    spawnGameTime = e['spawnGameTime']
    print('Current time: {}, \t{} dragon is next \tat {}'.format(msecToDisplayTimestamp(gameTime), dragonType, msecToDisplayTimestamp(spawnGameTime)))
    drakeSpawnTimes.append(spawnGameTime)
    teamOneWardsPlacedNearDragon = 0
    teamTwoWardsPlacedNearDragon = 0
    for we in wardPlacedEvents:
        wardType = we['wardType']
        wardDuration = 90000 if wardType == 'yellowTrinket' else 150000
        wardIsInTime = spawnGameTime - we['gameTime'] < wardDuration and spawnGameTime - we['gameTime'] > 0
        wardIsNearPit = positionDistance(we['position'], [9866, 4414]) < 1500
        placedByTeamOne = we['placerTeamUrn'][-3:] == 'one'
        if wardIsInTime and wardIsNearPit:
            if placedByTeamOne:
                teamOneWardsPlacedNearDragon += 1
            else:
                teamTwoWardsPlacedNearDragon += 1
    print('Team One placed \t{}\t wards near the dragon pit vs. Team Two\'s \t{}'.format(teamOneWardsPlacedNearDragon, teamTwoWardsPlacedNearDragon))
    teamOneWardKillsNearDragon = 0
    teamTwoWardKillsNearDragon = 0
    for wde in wardDestroyedEvents:
        wardType = wde['wardType']
        wardDuration = 90000 if wardType == 'yellowTrinket' else 150000
        wardIsInTime = spawnGameTime - wde['gameTime'] < wardDuration and spawnGameTime - wde['gameTime'] > 0
        wardIsNearPit = positionDistance(wde['position'], [9866, 4414]) < 1500
        killedByTeamOne = wde['killerTeamUrn'][-3:] == 'one'
        if wardIsInTime and wardIsNearPit:
            if placedByTeamOne:
                teamOneWardKillsNearDragon += 1
            else:
                teamTwoWardKillsNearDragon += 1
    print('Team One killed \t{}\t wards near the dragon pit vs. Team Two\'s \t{}'.format(teamOneWardKillsNearDragon, teamTwoWardKillsNearDragon))
    print('_____________________________')

allPositionUpdates = typeSortedEvents['all_positions_update']
for e in allPositionUpdates:
    pass

# Track dragon kills to text output
monsterKills = typeSortedEvents['monster_killed']
for e in monsterKills:
    gameTime = e['gameTime']
    monsterPosition = e['position']
    killedByTeam = e['killerTeamUrn'][-3:]
    killedByPlayer = e['killerUrn']
    monsterType = e['monsterType']
    dragonType = e['dragonType']
    assists = e['assistants']
    if monsterType == 'dragon':
        drakeKillTimes.append(gameTime)
        print('time: {}, \tDragon killed by team: {}, \t in position {}'.format(msecToDisplayTimestamp(gameTime), killedByTeam, monsterPosition))

# Plot player positions on a minimap in the 30s before dragon spawns up to dragon kills
for i, (drakeKill, drakeSpawn) in enumerate(zip(drakeKillTimes, drakeSpawnTimes)):
    chartTimespan = [drakeSpawn-30000, drakeKill]
    chartTimeTotal = drakeKill - drakeSpawn + 30000
    bluePlayerXs = []
    bluePlayerYs = []
    redPlayerXs = []
    redPlayerYs = []
    for e in allPositionUpdates:
        if e['gameTime'] > chartTimespan[0] and e['gameTime'] < chartTimespan[1]:
            playerPositions = e['positions']
            for playerPos in playerPositions:
                if playerPos['teamUrn'][-3:] == 'one':
                    bluePlayerXs.append(playerPos['position'][0])
                    bluePlayerYs.append(playerPos['position'][1])
                else:
                    redPlayerXs.append(playerPos['position'][0])
                    redPlayerYs.append(playerPos['position'][1])

    minimapBg = plt.imread("lol_minimap_500_500.png")
    fig, ax = plt.subplots()
    ax.imshow(minimapBg, extent=[0, 15000, 0, 15000])
    red_dots = plt.scatter(redPlayerXs, redPlayerYs, 24, marker='o', c='#ff000030')
    blue_dots = plt.scatter(bluePlayerXs, bluePlayerYs, 24, marker='o', c='#0000ff30')
    plt.title("Champion heatmap 30s before dragon spawn until dragon kill")
    plt.ylim(bottom=0)
    plt.xlim(left=0)
    plt.xticks([])
    plt.yticks([])
    plt.savefig('dragon_' + str(i) +'_heatmap.png')
    