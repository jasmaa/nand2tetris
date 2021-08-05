import math

hand_r = 60
pos_min_r = 3
pos_hour_r = 5

for x in range(60):
    rad = 2*math.pi*x/60
    
    print(f'let handYTable[{x}] = {int(hand_r*math.sin(rad-math.pi/2))};')
    print(f'let handXTable[{x}] = {int(hand_r*math.cos(rad-math.pi/2))};')

    print(f'let posMinuteYTable[{x}] = {int(pos_min_r*math.sin(rad))};')
    print(f'let posMinuteXTable[{x}] = {int(pos_min_r*math.cos(rad))};')

    print(f'let posHourYTable[{x}] = {int(pos_hour_r*math.sin(rad))};')
    print(f'let posHourXTable[{x}] = {int(pos_hour_r*math.cos(rad))};')


