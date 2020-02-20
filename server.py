# -*- coding: utf-8 -*- python3
"""
Created on Thu Feb 20 05:53:20 2020

@author: Antiochian
"""

from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.modules import CanvasGrid, ChartModule, TextElement
from mesa.visualization.UserParam import UserSettableParameter

from model import Protest

class HappyElement(TextElement):
    def __init__(self):
        pass
    def render(self,model):
        return "Happy Workers: "+str(model.quiet_no)+"/"+str(model.schedule.get_agent_count())
    
class JailedElement(TextElement):
    def __init__(self):
        pass
    def render(self,model):
        return "Jailed Workers: "+str(model.arrested_no)+"/"+str(model.schedule.get_agent_count())
    
    
def protest_draw(agent):
    if agent is None:
        return
    portrayal = {"Shape": "circle", "Filled": "true"}
    
    if agent.ID == "goon":
        portrayal["Color"] = ["#268bd2", "#268bd2"] #BLUE GOONS
        portrayal["r"] = 0.8
        portrayal["Layer"]=0
    elif agent.ID == "worker":
        portrayal["r"] = 0.4
        portrayal["Layer"]=1
        if agent.state == "quiet":
            portrayal["Color"] = ["#859900","#859900"] #QUIET = GREEN
        elif agent.state == "active":
            portrayal["Color"] = ["#dc322f", "#dc322f"] #ANGRY = RED
        elif agent.state == "arrested":
            portrayal["Color"] = ["#839496", "#839496"] #JAILED = GREY
    return portrayal


#SERVER CODE STARTS HERE   
    
Nx,Ny = 20,20
happy_element = HappyElement()
jailed_element = JailedElement()
canvas_element = CanvasGrid(protest_draw, Nx,Ny,500,500)
grievance_chart = ChartModule([ {"Label":"total_grievance", "Color":"Black"} ])
population_chart = ChartModule([ {"Label":"active_no", "Color":"Red"},{"Label":"arrested_no", "Color":"Grey"},{"Label":"quiet_no", "Color":"Green"}   ])        

model_params = {
    "height": Ny,
    "width": Nx,
    "density" : UserSettableParameter("slider", "Population", 0.8, 0.1, 1.0, 0.1),
    "goon_proportion": UserSettableParameter("slider", "Amount of Goons", 0.05, 0.00, 1.0, 0.01),
    "strike_threshold": UserSettableParameter("slider", "Strike Threshold", 0.1, 0.00, 0.5, 0.01),
    "worker_vision": UserSettableParameter("slider", "Worker Sight Range", 6, 0, 10, 1),
    "goon_vision": UserSettableParameter("slider", "Goon Arrest Range", 6, 0, 10, 1),
    "max_jail_term": UserSettableParameter("slider", "Max Jail Term (turns)", 15, 0, 40, 1),
    "ramp_speed": UserSettableParameter("slider", "Jailtime ramp-up speed", 0.4, 0.0, 1, 0.05)
    }    
    
server = ModularServer(Protest, [canvas_element, happy_element, jailed_element, grievance_chart,population_chart],
                       "Protest", model_params)
            