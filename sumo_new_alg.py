#!/usr/bin/env python sumo_new_alg.py
# coding: utf-8import numpy as npimport mathimport optparse
from optparse import OptionParserimport tracifrom time import timesumoBinary = "sumo-gui"sumoConfig = ["-c", "grid.port.sumocfg", "-S"]sumoCmd = [sumoBinary, sumoConfig[0], sumoConfig[1], sumoConfig[2]]cmd = ['sumo-gui', '-c', 'grid.port.sumocfg', '--save-configuration', 'debug.grid.xml']# setup global various
simtime = 0debug = 0sec = 5rou = 0.15rou2 = 0.1
threshold = 0.9
mean_veh_gap = 1.0
l_loop = 2
k_shortest = 5
set_cong = []
congested = []
algorithm = 1 # 1:first algorithm, being road weighted and traffic condition, 2: traffic only
usage = "usage: python %prog [options] argument\nFor example: pyhon %prog -a 2 -c f0 -e g0 -d 1 -g 2.5 -l 2 -s 8 -t 0.7"
parser = OptionParser(usage=usage)

parser.add_option("-a", "--algorithm", type="int",
                  dest="algorithm", default="1", metavar="1",
                  help="choose an algorithm, between 1 and 2, default 1")
parser.add_option("-c", "--congested", type="string",
                  dest="road1", default="", metavar="",
                  help="manually add congested road, such f0  g0")
parser.add_option("-e", "--extracongested", type="string",
                  dest="road2", default="", metavar="",
                  help="manually add congested road, such f0  g0")
parser.add_option("-d", "--debug", type="int",
                  dest="debug", default="0", metavar="1",
                  help="debug option, print info on screen, default off")
parser.add_option("-g", "--gap", type="float",
                  dest="mean_veh_gap", default="1.0", metavar="1.0",
                  help="the mean gap between two vehicles, default 1.0 meters")
parser.add_option("-l", "--loop", type="int",
                  dest="l_loop", default="2", metavar="2",
                  help="if congestion happens, vehicle in l_loop upstream of congested road will be re-routing, default 2")
parser.add_option("-s", "--seconds", type="int",
                  dest="sec", default="5", metavar="5",
                  help="how long is the traffic prediction period cycle, default 5 seconds")
parser.add_option("-t", "--threshold", type="float",
                  dest="threshold", default="0.9", metavar="0.9",
                  help="threshold value for traffic prediction, default 0.9")
options, arguments = parser.parse_args()
if options.algorithm:
    algorithm = options.algorithm
if options.debug:
    debug = options.debug
if options.road1:
    set_cong.append(options.road1)
if options.road2:
    set_cong.append(options.road2)
if options.sec:
    sec = options.sec
    if sec >60 or sec <= 4:
        print ("period too low or too high")
        exit()
if options.l_loop:
    l_loop = options.l_loop
    if l_loop > 4 or l_loop <= 1:
        print ("l_loop should between 2 and 4")
        exit()
if options.threshold:
    threshold = options.threshold
    if threshold > 1.0 or threshold < 0.3:
        print ("Threshold too low or too high")
        exit()
if options.mean_veh_gap:
    mean_veh_gap = options.mean_veh_gap
    if mean_veh_gap >= 10.0 or mean_veh_gap <= 0.5:
        print ("Gap too small or too big")
        exit()
# the port used for communicating with the sumo instance
traci_port = 56097
# define road network, lane number, length, connections
# data structure:
# road_name[0], lane_number[1], lane_length[2], max_speed[3], t1[4], t2[5], incoming_roads[6], outgoing_roads[7], predicted_t[8], road_weight[9]
road_network = [ ['a0', 1, 200, 0, 0, 0, ['m1','b0','p0'], [], 0, 0],
                 ['a1', 1, 200, 0, 0, 0, [], ['m0','b1','p1'], 0, 0],
                 ['y0',1, 224, 0, 0, 0, ['r1', 'h0', 'u0', 'z1', 'g1'], ['q1', 'b0', 'n0', 'c1'], 0, 0], 
                 ['y1',1, 224, 0, 0, 0, ['q0', 'b1', 'n1', 'c0'], ['r0', 'h1', 'u1', 'z0', 'g0'], 0, 0], 
                 ['b0', 1, 200, 0, 0, 0, ['q0', 'y0', 'c0', 'n1'], ['m0', 'a0', 'p1'], 0, 0], 
                 ['b1', 1, 200, 0, 0, 0, ['m1', 'a1', 'p0'], ['n0', 'c1', 'y1', 'q1'], 0, 0], 
                 ['z0',1, 224, 0, 0, 0, ['g1', 'y1', 'r1', 'h0', 'u0'], ['t0', 'j0', 'w1', 'k1'], 0, 0], 
                 ['z1',1, 224, 0, 0, 0, ['t1', 'j1', 'w0', 'k0'], ['g0', 'y0', 'r0', 'h1', 'u1'], 0, 0],
                 ['c0', 1, 200, 0, 0, 0, ['o1', 'd0', 'r0'], ['n0', 'b0', 'q1', 'y1'], 0, 0], 
                 ['c1', 1, 200, 0, 0, 0, ['n1', 'b1', 'q0', 'y0'], ['o0', 'd1', 'r1'], 0, 0], 
                 ['d0', 1, 200, 0, 0, 0, [], ['o0', 'c0', 'r1'], 0, 0], 
                 ['d1', 1, 200, 0, 0, 0, ['o1', 'c1', 'r0'], [], 0, 0], 
                 ['e0', 2, 200, 0, 0, 0, ['p1', 'f0', 's0'], [], 0, 0], 
                 ['e1', 2, 200, 0, 0, 0, [], ['p0', 'f1', 's1'], 0, 0], 
                 ['f0', 2, 200, 0, 0, 0, ['q1', 'g0', 't0'], ['p0', 'e0', 's1'], 0, 0],
                 ['f1', 2, 200, 0, 0, 0, ['p1', 'e1', 's0'], ['q0', 'g1', 't1'], 0, 0], 
                 ['g0', 2, 200, 0, 0, 0, ['y1', 'r1', 'h0', 'u0', 'z1'], ['q0', 'f0', 't1'], 0, 0], 
                 ['g1', 2, 200, 0, 0, 0, ['q1', 'f1', 't0'], ['y0', 'r0', 'h1', 'u1', 'z0'], 0, 0], 
                 ['h0', 2, 200, 0, 0, 0, [], ['u1', 'z0', 'g0', 'y0', 'r0'], 0, 0], 
                 ['h1', 2, 200, 0, 0, 0, ['u0', 'z1', 'g1', 'y1', 'r1'], [], 0, 0], 
                 ['i0', 3, 200, 0, 0, 0, ['v0', 'j0', 's1'], [], 0, 0], 
                 ['i1', 3, 200, 0, 0, 0, [], ['s0', 'j1', 'v1'], 0, 0],
                 ['j0', 3, 200, 0, 0, 0, ['w0', 'k0', 'z0', 't1'], ['v1', 'i0', 's0'], 0, 0], 
                 ['j1', 3, 200, 0, 0, 0, ['v0', 'i1', 's1'], ['w1', 'k1', 'z1', 't0'], 0, 0], 
                 ['k0', 3, 200, 0, 0, 0, ['x0', 'l0', 'u1'], ['w1', 'j0', 't0', 'z1'], 0, 0], 
                 ['k1', 3, 200, 0, 0, 0, ['w0', 'j1', 't1', 'z0'], ['x1', 'l1', 'u0'], 0, 0], 
                 ['l0', 3, 200, 0, 0, 0, [], ['u0', 'k0', 'x1'], 0, 0], 
                 ['l1', 3, 200, 0, 0, 0, ['u1', 'k1', 'x0'], [], 0, 0], 
                 ['m0', 1, 100, 0, 0, 0, ['a1', 'b0', 'p0'], [], 0, 0],
                 ['m1', 1, 100, 0, 0, 0, [], ['a0', 'b1', 'p1'], 0, 0], 
                 ['n0', 1, 100, 0, 0, 0, ['b1', 'q0', 'c0', 'y0'], [], 0, 0], 
                 ['n1', 1, 100, 0, 0, 0, [], ['b0', 'q1', 'c1', 'y1'], 0, 0], 
                 ['o0', 1, 100, 0, 0, 0, ['c1', 'd0', 'r0'], [], 0, 0], 
                 ['o1', 1, 100, 0, 0, 0, [], ['d1', 'r1', 'c0'], 0, 0], 
                 ['p0', 1, 100, 0, 0, 0, ['e1', 's0', 'f0'], ['a0', 'm0', 'b1'], 0, 0], 
                 ['p1', 1, 100, 0, 0, 0, ['a1', 'm1', 'b0'], ['e0', 's1', 'f1'], 0, 0],
                 ['q0', 1, 100, 0, 0, 0, ['f1', 't0', 'g0'], ['b0', 'n0', 'c1', 'y1'], 0, 0], 
                 ['q1', 1, 100, 0, 0, 0, ['b1', 'n1', 'c0', 'y0'], ['f0', 't1', 'g1'], 0, 0], 
                 ['r0', 1, 100, 0, 0, 0, ['y1', 'g1', 'z1', 'u0', 'h0'], ['c0', 'o0', 'd1'], 0, 0], 
                 ['r1', 1, 100, 0, 0, 0, ['d0', 'o1', 'c1'], ['y0', 'g0', 'z0', 'u1', 'h1'], 0, 0], 
                 ['s0', 1, 100, 0, 0, 0, ['i1', 'v0', 'j0'], ['e0', 'p0', 'f1'], 0, 0], 
                 ['s1', 1, 100, 0, 0, 0, ['f0', 'p1', 'e1'], ['j1', 'i0', 'v1'], 0, 0], 
                 ['t0', 1, 100, 0, 0, 0, ['j1', 'w0', 'k0', 'z0'], ['f0', 'q0', 'g1'], 0, 0],
                 ['t1', 1, 100, 0, 0, 0, ['f1', 'q1', 'g0'], ['z1', 'k1', 'w1', 'j0'], 0, 0], 
                 ['u0', 1, 100, 0, 0, 0, ['k1', 'x0', 'l0'], ['h1', 'r0', 'y0', 'g0', 'z0'], 0, 0], 
                 ['u1', 1, 100, 0, 0, 0, ['h0', 'r1', 'y1', 'g1', 'z1'], ['k0', 'x1', 'l1'], 0, 0], 
                 ['v0', 1, 100, 0, 0, 0, [], ['i0', 's0', 'j1'], 0, 0], 
                 ['v1', 1, 100, 0, 0, 0, ['j0', 's1', 'i1'], [], 0, 0], 
                 ['w0', 1, 100, 0, 0, 0, [], ['j0', 't0', 'z1', 'k1'], 0, 0], 
                 ['w1', 1, 100, 0, 0, 0, ['k0', 'z0', 't1', 'j1'], [], 0, 0],
                 ['x0', 1, 100, 0, 0, 0, [], ['k0', 'u0', 'l1'], 0, 0], 
                 ['x1', 0, 100, 0, 0, 0, ['l0', 'u1', 'k1'], [], 0, 0] ]
G = {} ##grid
for items in road_network:
    aa = items[0]
    bb = items[7]
    G[aa] = bb
tlc_actions = ['GGG','yyy','rrr']
class MyQUEUE: # just an implementation of a queue
    def __init__(self):
        self.holder = []
    def enqueue(self,val):
        self.holder.append(val)
    def dequeue(self):
        val = None
        try:
            val = self.holder[0]
            if len(self.holder) == 1:
                self.holder = []
            else:
                self.holder = self.holder[1:]   
        except:
            pass
        return val  
    def IsEmpty(self):
        result = False
        if len(self.holder) == 0:
            result = True
        return result
def BFS(graph, start, end, q, max_path_num):
    paths = []
    temp_path = [start]
    q.enqueue(temp_path)
    while q.IsEmpty() == False:
        tmp_path = q.dequeue()
        last_node = tmp_path[len(tmp_path)-1]
        #print tmp_path
        if last_node == end:
            max_path_num -= 1
            if max_path_num>0:
                paths.append(tmp_path)
                if debug:
                    print ("FOUND A VALID_PATH : {}".format(tmp_path))
            else:
                return paths
        for link_node in graph[last_node]:
            if link_node not in tmp_path:
                new_path = []
                new_path = tmp_path + [link_node]
                q.enqueue(new_path)
#try:
#    traci.init(traci_port)
#except:
#    print("SUMO server is not running")
#    print("Please run sumo-gui -c <filename.sumocfg> first")
#    exit()
traci.start(sumoCmd)
def get_weight_para(lane):
    if lane==1:
        return 1.5
    elif lane==2:
        return 1.1
    elif lane==3:
        return 1.0
    elif lane==4:
        return 0.9 ## need to confirm
    else:
        return 0.0
def get_weight(lane, length, speed):
    # for now 
    return get_weight_para(lane)*length/speed
def init_network():
    tlc_network  = [['jj1', 30],
                    ['jj2', 30],
                    ['jj3', 30],
                    ['jj6', 30],
                    ['jj7', 30],
                    ['jj8', 30],
                    ['jj11', 30],
                    ['jj12', 30],
                    ['jj13', 30]]
    ## obtain road info, lane, length
    road_list = traci.edge.getIDList()
    road_list = [xxx for xxx in road_list if not ':' in xxx] # remove junctions
    # make a new road_list to match the road_network
    new_road_list = []
    for road in road_network:
        a = road[0]
        if findit(a, road_list)>=0:
            new_road_list.append(a)
    road_list = new_road_list
    # update road_network with correct lane number
    for road in road_list:
        num_lane = traci.edge.getLaneNumber(road)
        if debug:
            print("road {} has {} lanes".format(road,num_lane))
        a = findit(road, road_network)
        if a>=0:
            road_network[a][1]=num_lane
    # update road_network with correct length
    lanes = traci.lane.getIDList()
    lanes = [xxx for xxx in lanes if not ':' in xxx] # remove junction lanes
    for lane in lanes:
        lane_length = traci.lane.getLength(lane)
        max_speed = traci.lane.getMaxSpeed(lane)
        if debug:
            print("lane {} is {} meter in length and max speed is {}".format(lane, lane_length,max_speed))
        a = lane[0:lane.index('_')]
        a = findit(a, road_network)
        if a>=0:
            road_network[a][2]=lane_length
            road_network[a][3]=max_speed
    # update weight for each roads [0]name [1]lane [2]lengh [3]speed [9]weight 
    for road in road_network:
        road[9] = get_weight(road[1], road[2], road[3])
        if debug:
            print ("{} weight = {}".format(road[0],road[9]))
    if debug:
        print(road_network)
    ## obtain tlc info
    tlc_list = traci.trafficlight.getIDList()
    tlc_count = traci.trafficlight.getIDCount()
    if debug:
        print(tlc_list)
    for i in range(len(tlc_list)):
        #print(traci.trafficlight.getCompleteRedYellowGreenDefinition(tlc_list[i]))
        timing = traci.trafficlight.getPhaseDuration(tlc_list[i])
        if debug:
            #print(traci.trafficlight.getRedYellowGreenState(tlc_list[i]))
            print(timing)
        a = findit(tlc_list[i], tlc_network)
        if a>=0:
            tlc_network[a][1] = timing
    return road_list, tlc_network
## getCogested function return all congested road if great than the threshold
def getCongested():
    for bbbbbb,road in enumerate(road_list):
        if road_network[bbbbbb][8] > threshold:
            # it's congested
            # if already insert, skip
            if findit(road, congested)==-1:
                print ("        @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ Road {} is congested/blocked now @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@".format(road))
                congested.append(road)
                #continue
        else: # maybe cleared, try to remove if exist
            if findit(road, congested) != -1: # yes
                #delete it
                congested.remove(road)
# get the upstream roads of all cogested roads
def getUpstream2():
    uploop = []
    for road in congested:
        if findit(road, road_network)>=0:
            l1 = road_network[findit(road, road_network)][6] # road that vehicle coming in
            if len(l1)>0:
                for m in l1:
                    if findit(m,uploop)==-1:
                        uploop.append(m)
                    if findit(m, road_network)>=0:
                        l2 = road_network[findit(m, road_network)][6]
                        for n in l2:
                            if findit(n, uploop)==-1:
                                uploop.append(n)
    return uploop
def getUpstream3():
    uploop = []
    return uploop
def getUpstream4():
    uploop = []
    return uploop
def getUpstream(l_loop):
    if l_loop == 2:
        return getUpstream2()
    elif l_loop == 3:
        return getUpstream2()
    elif l_loop == 4:
        return getUpstream2()
    else:
        return []
def get_Phase(tlc_id):
    phase = traci.trafficlight.getPhase(tlc_id)
    return phase
def set_phase(tlc_id, phase):
    traci.trafficlight.setPhase(tlc,phase)
def get_state(tlc_id):
    state = traci.trafficlight.getRedYellowGreenState(tlc_id)
    return state
def set_state(tlc_id,state_no):
    state_old = list(traci.trafficlight.getRedYellowGreenState(tlc_id))
    traci.trafficlight.setRedYellowGreenState(tlc_id, state_no)
def random_phase(tlc_id):
    phase =  get_Phase(tlc_id)
    a = random.chooee(phase)
    return a
def findit(a, b):
    m = -1
    for i in range(len(b)):
        if a in b[i]:
            m = i
            break
    return m
def show_t_values(): # road_network[][8]
    print("----------------------------------------------------------------------------------------------------")
    print ("       m0:{:f}   m1:{:f}       n0:{:f}   n1:{:f}       o0:{:f}   o1:{:f}".format(road_network[28][8],road_network[29][8],road_network[30][8],road_network[31][8],road_network[32][8],road_network[33][8]))
    print("----------------------------------------------------------------------------------------------------")
    print ("a1:{:f}                 b1:{:f}                c1:{:f}                d1:{:f}".format(road_network[1][8],road_network[5][8],road_network[9][8],road_network[11][8]))
    print ("a0:{:f}                 b0:{:f}                c0:{:f}                d0:{:f}".format(road_network[0][8],road_network[4][8],road_network[8][8],road_network[10][8]))    print("----------------------------------------------------------------------------------------------------")    print ("       p0:{:f}   p1:{:f}       q0:{:f}   q1:{:f}      y0:{:f}  y1:{:f}       r0:{:f}   r1:{:f}".format(road_network[34][8],road_network[35][8],road_network[36][8],road_network[37][8],road_network[2][8],road_network[3][8],road_network[38][8],road_network[39][8]))    print("----------------------------------------------------------------------------------------------------")    print ("e1:{:f}                 f1:{:f}                g1:{:f}                h1:{:f}".format(road_network[13][8],road_network[15][8],road_network[17][8],road_network[19][8]))    print ("e0:{:f}                 f0:{:f}                g0:{:f}                h0:{:f}".format(road_network[12][8],road_network[14][8],road_network[16][8],road_network[18][8]))    print("----------------------------------------------------------------------------------------------------")    print ("       s0:{:f}   s1:{:f}       t0:{:f}   t1:{:f}      z1:{:f}  z0:{:f}       u0:{:f}   u1:{:f}".format(road_network[40][8],road_network[41][8],road_network[42][8],road_network[43][8],road_network[7][8],road_network[6][8],road_network[44][8],road_network[45][8]))    print("----------------------------------------------------------------------------------------------------")    print ("i1:{:f}                 j1:{:f}                k1:{:f}                l1:{:f}".format(road_network[21][8],road_network[23][8],road_network[25][8],road_network[27][8]))    print ("i0:{:f}                 j0:{:f}                k0:{:f}                l0:{:f}".format(road_network[20][8],road_network[22][8],road_network[24][8],road_network[26][8]))    print("----------------------------------------------------------------------------------------------------")    print ("       v0:{:f}   v1:{:f}       w0:{:f}   w1:{:f}       x0:{:f}   x1:{:f}".format(road_network[46][8],road_network[47][8],road_network[48][8],road_network[49][8],road_network[50][8],road_network[51][8]))    print("----------------------------------------------------------------------------------------------------")    print("----------------------------------------------------------------------------------------------------")
# update t
def update_road_network(road_list):
    for i,road in enumerate(road_list):
        # find the incoming roads and the vehicle parameters
        inc_road = road_network[i][6]
        inc_total_veh = 0
        inc_mean_veh_length = 0
        inc_mean_veh_speed = 0
        Ipt = 0
        for j in inc_road:
            # find the max_speed of each road and lane length
            a = findit(j,road_network)
            inc_vfp = road_network[a][3]
            inc_lp = road_network[a][2]
            inc_npt = traci.edge.getLastStepVehicleNumber(j)
            inc_fp = inc_vfp * inc_npt / inc_lp
            Ipt += inc_fp*sec*rou
            inc_total_veh += inc_npt
            inc_mean_veh_length += traci.edge.getLastStepLength(j)
            inc_mean_veh_speed += traci.edge.getLastStepMeanSpeed(j)
        if len(inc_road)!=0:
            inc_mean_veh_length = inc_mean_veh_length/len(inc_road)
            inc_mean_veh_speed = inc_mean_veh_speed/len(inc_road)
        # find the outgoing roads
        out_road = road_network[i][7]
        out_total_veh = 0
        out_mean_veh_length = 0
        out_mean_veh_speed = 0
        Opt = 0
        for j in out_road:
            # find the max_speed of each road and lane length
            a = findit(j,road_network)
            out_vfp = road_network[a][3]
            out_lp = road_network[a][2]
            out_npt = traci.edge.getLastStepVehicleNumber(j)
            out_fp = out_vfp * out_npt / out_lp
            Opt += out_fp*sec*rou
            out_total_veh += out_npt
            out_mean_veh_length += traci.edge.getLastStepLength(j)
            out_mean_veh_speed += traci.edge.getLastStepMeanSpeed(j)
        if len(out_road)!=0:
            out_mean_veh_length = out_mean_veh_length/len(out_road)
            out_mean_veh_speed = out_mean_veh_speed/len(out_road)

        # t2
        mean_veh_length = (inc_mean_veh_length+out_mean_veh_length)/2.0 + mean_veh_gap
        t2 = 1.0 * (Ipt - Opt) * mean_veh_length /(road_network[i][1]*road_network[i][2])
        if (t2!=0.0) and debug:
            print ("road {} t2 is {}".format(road, t2))
        road_network[i][5]=t2
        #   last step vehicle number (0x10)
        #	int	The number of vehicles on this edge within the last time step.
        #	getLastStepVehicleNumber
        veh_number = traci.edge.getLastStepVehicleNumber(road)
        #   last step mean speed (0x11)	
        #   double	the mean speed of vehicles that were on the named edge within the last simulation step [m/s]
        #   getLastStepMeanSpeed
        mean_veh_speed = traci.edge.getLastStepMeanSpeed(road)
        #   last step mean vehicle length (0x15)
        #	double	The mean length of vehicles which were on the edge in the last step [m]
        #	getLastStepLength
        mean_veh_length = traci.edge.getLastStepLength(road)
        #   last step halting number (0x14)	
        #   int	Returns the total number of halting vehicles for the last time step on the given edge. 
        #   A speed of less than 0.1 m/s is considered a halt.	
        #   getLastStepHaltingNumber
        halting_veh_number = traci.edge.getLastStepHaltingNumber(road)
        t1 = 1.0*(veh_number * (mean_veh_length + mean_veh_gap))/(road_network[i][1]*road_network[i][2])
        if debug:
            print ("road {} has {} vehicles and t1 is {}".format(road, veh_number,t1))
        road_network[i][4]=t1
        # ept evaporation ratio
        ept = 1.0 * mean_veh_speed / road_network[i][3] / (1.0 + halting_veh_number)
        if debug:
            print ("road {} has mean_veh_speed {} maxspeed {} halting vehicles {} evaporation rate {}".format(road, mean_veh_speed, road_network[i][3], halting_veh_number, ept))
        # predicted t        predicted_t = (1 - ept) * t1 + ept * t2
        if predicted_t<0:
            predicted_t = 0.0
        if debug:
            print ("road {} has a predicted traffic congestion level of {}".format(road, predicted_t))
        #if predicted_t>=0.85:
            #print ("**** NOTICE: road {} has a predicted traffic congestion level of {} that is great than 0.85".format(road, predicted_t))
        road_network[i][8] = predicted_t
    if debug:
        show_t_values()
# rerouting
def vehicle_rerouting(uploop):
    # find all vehicles on these rerouting roads
    veh_rerou_tobe = []
    veh_rerou = []
    rerouting_number = 0

    if len(uploop)>0:
        veh_all = traci.vehicle.getIDList()
        #for road in uploop:
        for veh_id in veh_all:
            if debug:
                print("{} - {}".format(veh_id,traci.vehicle.getTypeID(veh_id))) #Color(veh_id)))
            if traci.vehicle.getTypeID(veh_id)=='a': #  (255,0,0,255): # already in rerouting mode
                if debug:
                    print ("----already set---------------- {} -------------------".format(veh_id))
                continue
            x, y = traci.vehicle.getPosition(veh_id)
            edgeID, lanePosition, laneIndex = traci.simulation.convertRoad(x, y)
            org_rou = traci.vehicle.getRoute(veh_id)
            #lane_id = edgeID+"_"+str(laneIndex)
            #if debug:
            #    print("vehicle {} on road {} lane {} outgoing lanes {}\n".format(veh_id, edgeID,laneIndex,traci.lane.getLinks(lane_id)))
            if findit(edgeID, uploop)>=0: #vehicle is on the uploop road
                # find the vehicle routine
                # get routine not finished
                org_rou_todo = org_rou[org_rou.index(edgeID):]
                dest = org_rou_todo[-1]
                org = edgeID # start from?
                if len(org_rou_todo)>1: # only if the destination is longer enough 
                    if debug:
                        print("vehicle {} routine {} route_to_do {}\n".format(veh_id, org_rou, org_rou_todo))
                    # find if the rtd include jamed road
                    for road in congested:
                        if road in org_rou_todo: # include this vechile for re-routing
                            veh_rerou.append([veh_id, org_rou_todo, org, dest])
                            break
        # start to re-routing the selected vehicles
        if len(veh_rerou)>0: # found some vehicle
            if debug:
                print("{} vehicles need to be rerouting {}".format(len(veh_rerou)))
            # find k vehicle paths from org to destination and re-routing only one of the routing not include the jammed roads
            for veh_info in veh_rerou:
                v_id = veh_info[0]
                org_path = veh_info[1] #traci.vehicle.getRoute(veh)
                org = veh_info[2]
                dest = veh_info[3]
                if debug:
                    print ("vehicle {} route {} org {} dest {}".format(v_id, org_path, org, dest))
                # find new path for this vehicle and send away
                path_queue = MyQUEUE() # now we make a queue
                found_path = BFS(G, org, dest, path_queue, 10)
                # delete any path that through congested roads
                useful_path = []
                for path in found_path:
                    aaaa = True
                    for road in congested:
                        if road in path: # road is cogested, the path is not useful
                            aaaa = False
                            break
                    if aaaa:
                        # calc total t value
                        total_t = 0.0
                        total_weight = 0.0
                        for no, node in enumerate(path):
                            if no==0: # do not calc current road
                                continue
                            aaa = findit(node, road_network)
                            total_t += road_network[aaa][8] #t
                            total_weight += road_network[aaa][9] # weight
                        # how to deal with the algortihms?                        if algorithm == 1:                            useful_path.append([path, total_t+total_weight])                        else:                            useful_path.append([path, total_t])                # sort as t+weight                sorted_path = sorted(useful_path, key=lambda x: x[1])
                if debug:                    print("Path is sorted by weight and t values {}".format(sorted_path))

                if algorithm == 1: # current road condition and weighted path
                    if len(sorted_path)>0: # at least a path                        chosed_path = sorted_path[0][0] # chose a less wighted roads                        #if debug:                        print ("vehicle {} old route {}, re-route to {}\n".format(v_id, org_path, chosed_path))                        try:                            traci.vehicle.setRoute(v_id, chosed_path)                        except:                            print ("@@@@@@WARNING: vehicle {} rerouting error, please check ......................".format(v_id))                        traci.vehicle.setType(v_id, 'a')                        rerouting_number +=1                else: # the paper algorthm 2                    useful_path=[]
                    k2=0                    for itm in sorted_path:
                        if k2<k_shortest:                            useful_path.append(itm)                            k2 += 1                    if debug:                        print ("found {} paths as below: {}".format(len(found_path), found_path))                        print("Total of {} path, {} can be used for rerouting".format(len(found_path), len(useful_path)))                        print ("usefule path as below: {}".format(useful_path))                    # delete any path via congested roads, and make sure useful_path is sorted with t values                    # the new path weight is calced according to t values                    # then choose a path if have more than one                    if len(useful_path)>0: # only rerouting if we do have one, or stick to old route                        if debug:                            print ("before calc the weight {}".format(useful_path))                        total_prob = 0                        for ii in useful_path:                            total_prob += math.exp(-1*rou2*ii[1])                        for ii in useful_path:                            ii[1] = 1.0*math.exp(-1*rou2*ii[1])/total_prob                        if debug:                            print ("after calc weight {}".format(useful_path))                        elems = [ii1 for ii1,ii2 in enumerate(useful_path)]                        probs = [ii[1] for ii in useful_path]                        if len(useful_path)==1: # only one route                            chosed_path = useful_path[0][0]                        else:                            chosed_elems = np.random.choice(elems, p=probs) # useful_path[0] # chose a random one? or less congested roads?                            chosed_path = useful_path[chosed_elems][0]                        ###send the vehicle to new route                        #if debug:                        print ("vehicle {} old route {}, re-route to {}\n".format(v_id, org_path, chosed_path))                        try:                            traci.vehicle.setRoute(v_id, chosed_path)                        except:                            print ("@@@@@@WARNING: vehicle {} rerouting error, please check ......................".format(v_id))                        traci.vehicle.setType(v_id, 'a')                        rerouting_number +=1
        if rerouting_number>0 and debug:
            print("{} vehicles have been re-routed in this round".format(rerouting_number))
            print("----------------------------------")
### main loop start here
road_list, tlc_network = init_network()
time_start = time()
print("start simulation...")
while traci.simulation.getMinExpectedNumber() > 0:
    simtime = traci.simulation.getTime()
    if simtime % sec == 0:
        aas = traci.vehicle.getIDList() # get a list of current vehicles # ('H0E0.0', 'H0E0.1')
        total_veh = len(aas)
        if total_veh and debug:
            print("Total vehicles: {}".format(total_veh))
        if total_veh != 0:
            #update calc t1,t2 on all road
            update_road_network(road_list)
            # dealing with jam and each vehicle
            getCongested()
            ## for manually adding test congestion
            if len(set_cong)>0:
                for items in set_cong:
                    if items not in congested:
                        congested.append(items)
            ###
            if len(congested)>0:
                if debug:
                    print ("{} roads are cogested now {}".format(len(congested), congested))
                # find vehicles need to be re-routing
                # l_loop of upstream traffic
                #  first find all roads
                uploop = getUpstream(l_loop)
                if debug:
                    print("road {} has {} uploop roads".format(road,uploop))
                # vehicle rerouting
                if len(uploop)>0:
                    vehicle_rerouting(uploop)
                # later maybe re-schedule traffic lights
                #traci.vehicle.rerouteTraveltime(veh_id,True)
                # find current traffic light info
                #for i in range(len(tlc_list)):
                    #print(traci.trafficlight.getCompleteRedYellowGreenDefinition(tlc_list[i]))
                    #if debug:
                        #print(traci.trafficlight.getRedYellowGreenState(tlc_list[i]))
                        #print("traffic light {} timing {}".format(tlc_list[i], traci.trafficlight.getPhaseDuration(tlc_list[i])))
                #positions = [traci.vehicle.getPosition(id) for id in traci.vehicle.getIDList()]
                #state = get_state("6612263335")
                #print(state)
                #random_phase("6612263335")
                #traci.trafficlight.setRedYellowGreenState("6612263335",'rrr')
            else:
                if debug:
                    print ("All roads are smooth running now")
    try:
        traci.simulationStep()
    except:
        traci.close()
        print ("Simulation is closed before the end, please check")
        exit()time_end = time()
print ("total traci time elapsed: {}".format(time_end-time_start))
traci.close()
# note:
#- using TraCI always slows down the simulation
#- using traci.vehicle.rerouteTraveltime(veh_id,True) slows down the simulation a lot (due to updating of the edge weights)
#- if you just want vehicles to pick a better route at insertion, you can simply load the trips and not set device.rerouting.period
#- you can set the rerouting period for each vehicle individually using traci.vehicle.setParameter(vehID, "device.rerouting.period", str(periodInSeconds))