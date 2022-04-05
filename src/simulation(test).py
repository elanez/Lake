import traci


sumoCmd = ["sumo-gui", "-c", "../sumo_files/trial_osm.sumocfg"]
traci.start(sumoCmd)


vehiclesIDCount = traci.vehicle.getIDCount()
trafficlights=traci.trafficlight.getIDList()
tlsList = []
lanes = traci.lane.getIDList()
edges = traci.edge.getIDList()
trafficlights=traci.trafficlight.getIDList()
tl_lanes = ['bottom_in_0', 'bottom_in_1', 'bottom_in_2','left_in_0', 'left_in_1', 'left_in_2', 'right_in_0', 'right_in_1', 'right_in_2', 'top_in_0', 'top_in_1', 'top_in_2',]

def getCarNumber():
  for k in range(0, len(tl_lanes)):
    checker = tl_lanes[k]
    print("Car count: ", traci.lane.getLastStepVehicleNumber(checker), "in lane: ", checker)
    

def getCarNumberRed():
    for q in range(0, len(trafficlights)): 
        if(traci.trafficlight.getPhase(trafficlights[q]) == 1):
            for k in range(0, len(tl_lanes)):
                checker = tl_lanes[k]
                print("Car count: ", traci.lane.getLastStepVehicleNumber(checker), "in lane: ", checker, "vehicle ID",traci.lane.getLastStepVehicleIDs(checker))
        elif(traci.trafficlight.getPhase(trafficlights[q]) == 3):
            for k in range(0, len(tl_lanes)):
                checker = tl_lanes[k]
                print("Car count: ", traci.lane.getLastStepVehicleNumber(checker), "in lane: ", checker,  "vehicle ID",traci.lane.getLastStepVehicleIDs(checker))


                
def getVehicleInfo():
    vehicles=traci.vehicle.getIDList()
    for i in range(0,len(vehicles)):
        print(traci.vehicle.getLaneID(vehicles[i]), " in lenght: ", traci.vehicle.getLanePosition(vehicles[i]), "Speed: ", traci.vehicle.getSpeed(vehicles[i]))

        #Other details
        vehid = vehicles[i]
        x, y = traci.vehicle.getPosition(vehicles[i])
        coord = [x, y]
        lon, lat = traci.simulation.convertGeo(x, y)
        gpscoord = [lon, lat]
        spd = round(traci.vehicle.getSpeed(vehicles[i])*3.6,2)
        edge = traci.vehicle.getRoadID(vehicles[i])
        lane = traci.vehicle.getLaneID(vehicles[i])
        displacement = round(traci.vehicle.getDistance(vehicles[i]),2)
        turnAngle = round(traci.vehicle.getAngle(vehicles[i]),2)
        nextTLS = traci.vehicle.getNextTLS(vehicles[i])

def getTLInfo():
    for q in range(0, len(trafficlights)): 
        print("Phase", traci.trafficlight.getPhase(trafficlights[q]) , " Phase Duration:" , traci.trafficlight.getPhaseDuration(trafficlights[q]) , " State:" , traci.trafficlight.getRedYellowGreenState(trafficlights[q]))


while traci.simulation.getMinExpectedNumber() > 0:
    traci.simulationStep()

    getCarNumberRed()


traci.close