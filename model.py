# -*- coding: utf-8 -*- python3
"""
Created on Thu Feb 20 03:47:16 2020

@author: Antiochian
"""
from mesa import Agent, Model
from mesa.time import RandomActivation
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector
import math
import numpy as np
#WORKER REVOLT SIMULATION

class Worker(Agent):
    #average worker
    def __init__(self,pos,model,ID,vision,wage,risk_aversion,mobility):
        #WAGE and RA should be normally distributed
        super().__init__(pos,model)
        self.ID = "worker"
        self.vision = vision
        self.wage = wage
        self.risk_aversion = risk_aversion
        self.mobility = mobility
        
        self.curr_grievance = 0
        self.state = "quiet"
        self.arrest_timer = 0
        self.prev_arrests = 0
    
    def worker_move(self): #move to a nearby EMPTY square
        neighborhood = self.model.grid.get_neighborhood(self.pos, moore=False, include_center=False, radius=1)
        move_options = []
        for cell in neighborhood:
            if self.model.grid.is_cell_empty(cell):
                move_options.append(cell)
        if move_options != []:
            move_target = self.random.choice(move_options)
            self.model.grid.move_agent(self,move_target)
        return
    
    def step(self):
        if self.state == "arrested": #chill and dont move
            if self.arrest_timer <= 0:
                self.state = "quiet" #recover from arrest, then continue
                self.arrest_timer = 0
            else:
                self.arrest_timer -= 1 #tick down on arrest clock, do nothing
                self.model.arrested_no += 1
                return
        
        #MOVE or not
        if self.random.random() < self.mobility:
            self.worker_move()
            
        #DECIDE to strike or not
        G = self.evaluate_grievance()
        self.model.total_grievance += G #for measurement purposes
        NR = self.evaluate_risk()
        if G - NR > self.model.strike_threshold:
            self.state = "active"
            self.model.active_no += 1
            return
        else:
            self.state = "quiet" #simmer down if grievance has lowered
            self.model.quiet_no += 1
            return
        
    def evaluate_risk(self):
        k = 2.3 #hardcoded, pull this out later?
        #<TODO>: Get goon/worker ratio
        neighbors = self.model.grid.get_neighbors(self.pos, moore=False, include_center=False, radius=self.vision)
        goons = 0
        workers = 0
        for agent in neighbors:
            if agent.ID == "worker":
                workers += 1
            elif agent.ID == "goon":
                goons += 1
        
        goon_presence = int(goons/(workers+1)) #floor this value
        estimated_arrest_probability = 1 - math.exp(-k*goon_presence)
        net_risk = self.risk_aversion * estimated_arrest_probability
        return net_risk
        
    def evaluate_grievance(self):
        neighbors = self.model.grid.get_neighbors(self.pos, moore=False, include_center=False, radius=self.vision)
        local_wage_total = 0
        counter = 0
        for agent in neighbors:
            if agent.ID == "worker": 
                local_wage_total += agent.wage
                counter += 1
        avg_wage = local_wage_total/counter
        
        wage_diff = avg_wage - self.wage
        y = -1 + 2/(1+math.exp(-wage_diff))  #greviance function
        return max(y,0)
    
class Goon(Agent):
    #"Policeman" equivalent, who 
    def __init__(self,pos,model,ID,vision,mobility):
        #WAGE and RA should be normally distributed
        super().__init__(pos,model)
        self.ID = "goon"
        self.vision = vision
        self.mobility = mobility

    def goon_move(self): #move to a nearby empty square
        neighborhood = self.model.grid.get_neighborhood(self.pos, moore=False, include_center=False, radius=1)
        move_target = self.random.choice(neighborhood)
        self.model.grid.move_agent(self,move_target)
        return
    
    def step(self):
        #MOVE or not
        if self.random.random() < self.mobility:
            #move to empty square at random
            self.goon_move()
        
        #LOOK FOR NEARBY ACTIVE AGENTS
        neighbors = self.model.grid.get_neighbors(self.pos, moore=False, include_center=False, radius=self.vision)
        target_list = []
        for agent in neighbors:
            if agent.ID == "worker" and agent.state == "active":
                target_list.append(agent)
                
        #ARREST THEM
        if target_list != []: #if there is at least one valid target
            target = self.random.choice(target_list)
            target.state = "arrested"
            target.arrest_timer = 20 #CHANGE THIS LATER TO DEPEND ON PREV ARRESTS
            target.prev_arrests += 1
            
        return
    
    def choose_sentence(self,target):
        prev_arrests = target.prev_arrests
        sentence = self.model.max_jail_term * (2/(math.exp(-prev_arrests*self.model.ramp_speed)+1) - 1)
        return max(2,math.ceil(sentence))
    

class Protest(Model):
    def __init__(self, height=20, width=20, density=0.4, goon_proportion=0.05,
                 mobility=0.5,strike_threshold=0.1,worker_mobility=0.5,
                 goon_mobility=0.5,worker_vision=6,goon_vision=6,ramp_speed=0.4, max_jail_term=10):

        self.height = height
        self.width = width
        self.density = density
        self.goon_proportion = goon_proportion
        self.mobility = mobility
        self.strike_threshold = strike_threshold
        self.worker_mobility, self.goon_mobility = worker_mobility, goon_mobility
        self.worker_vision, self.goon_vision  = worker_vision, goon_vision
        self.ramp_speed = ramp_speed
        self.max_jail_term = max_jail_term
        
        self.schedule = RandomActivation(self)
        self.grid = MultiGrid(width, height, torus=True) #wraparound grid with single occupancy
        
        self.active_no = 0
        self.arrested_no = 0
        self.quiet_no = 0
        self.total_grievance = 0
        self.num_of_workers = 0
        self.num_of_goons = 1

        self.datacollector = DataCollector(
            {"quiet_no": "quiet_no",  # Model-level count
            "active_no": "active_no",
            "arrested_no": "arrested_no",
            "total_grievance":"total_grievance"})

        #make agents
        for cell in self.grid.coord_iter():
            x,y = cell[1],cell[2]
            if self.random.random() < self.density:
                #choose ID:
                agent_ID = np.random.choice(["worker","goon"], p=[1-self.goon_proportion, self.goon_proportion])
                if agent_ID == "worker":
                    #CHOOSE WAGE AND RISK AVERSION FROM NORMAL DISTRIBUTION
                    wage = np.random.normal(1,0.334) #slightly wider dist for wage
                    risk_aversion = np.random.normal(0.5,0.167) #narrow dist
                    agent = Worker((x,y),self,agent_ID,self.worker_vision,wage,risk_aversion,self.worker_mobility)
                    self.num_of_workers += 1
                elif agent_ID == "goon":
                    agent = Goon((x,y),self,agent_ID,self.goon_vision,self.goon_mobility)
                    self.num_of_goons += 1
                self.grid.place_agent(agent, (x,y))
                self.schedule.add(agent) #add to ticker lists
                
        
        self.running = True
        #self.datacollector.collect(self)
        
    def step(self):
        self.active_no = 0
        self.arrested_no = 0
        self.quiet_no = 0
        self.total_grievance = 0
        
        self.schedule.step()
        self.datacollector.collect(self)
        
#         print("Active = ",self.active_no)
#         print("Quiet = ",self.quiet_no)
#         print("Arrested = ",self.arrested_no)
#         print("Active = ",self.active_no)
#         print("Average Grievance = ",self.total_grievance)
        
        
        
        
# master = Protest()
# print("Goons: ",master.num_of_goons)
# print("Workers: ",master.num_of_workers)
# master.step()
# print("---------")
# master.step()
# print("---------")
# master.step()
        
        
        
        