import math

from rlbot.agents.base_agent import BaseAgent, SimpleControllerState
from rlbot.utils.structures.game_data_struct import GameTickPacket

from util.orientation import Orientation
from util.vec import Vec3


class MyBot(BaseAgent):
    kickoff_minimum_boost = 0 #How much boost to save from the kickoff. 
    kickoff_minimum_speed = 2250 #Uses boost if under this speed.

    
    kickoff_initial_jump_hold = 1 #Number of ticks to hold jump for the first jump of the speedflip. Value of 1 indicates tap jump. 
    kickoff_speedflip_delay = 1 #Number of ticks between the first jump and the flip. Value of 1 indicates minimum delay.
    kickoff_speedflip_yaw = -0.1 #sixteenth flip angle (left by default)
    kickoff_flipcancel_duration = 30 #How many ticks to hold flip cancel. Value of 1 indicates a 1-tick flip cancel. 

    kickoff_duration_side = 150 #How many alotted ticks the bot has to execute the kickoff
    kickoff_initial_turn_duration_side = 5 #How long the initial turn is
    kickoff_speedflip_starting_tick_side = 20 #The bot will speedflip on this tick. 
    kickoff_coast_duration_side = 50 #How many ticks to drive before starting flip into ball. 
    kickoff_5050_delay_side = 5 #How many ticks between the jump and the flip into the ball. 

    def initialize_agent(self):
        # This runs once before the bot starts up
        self.controller_state = SimpleControllerState()
        self.tickCounter = 0
        self.scenario = 0 #0 Unknown, 1 left, 2 left mid, 3 mid, 4 right mid, 5 right, 6 post kickoff

    def get_output(self, packet: GameTickPacket) -> SimpleControllerState:
        reset_controller_state(self)

        ball_location = Vec3(packet.game_ball.physics.location)
        my_car = packet.game_cars[self.index]
        car_location = Vec3(my_car.physics.location)

        car_orientation = Orientation(my_car.physics.rotation)
        car_direction = car_orientation.forward

        if(packet.game_info.is_round_active == True and packet.game_info.is_match_ended == False):
            self.tickCounter += 1
        else:
            self.tickCounter = 0

        if(self.tickCounter == 0): #check for the kickoff scenario
            if(my_car.physics.location.x == -2048.0):
                self.scenario = 1
            if(my_car.physics.location.x == -256.0):
                self.scenario = 2
            if(my_car.physics.location.x == 0.0):
                self.scenario = 3
            if(my_car.physics.location.x == 256.0):
                self.scenario = 4
            if(my_car.physics.location.x == 2048.0):
                self.scenario = 5
        
        if(self.tickCounter < MyBot.kickoff_duration_side): #TODO: Fix for other kickoffs
            if(self.scenario == 1):
                execute_scenario_side(self, packet, False)
            if(self.scenario == 2):
                execute_scenario_side(self, packet, False) #TODO: Should call midside, placeholder for testing
            if(self.scenario == 3):
                execute_scenario_mid(self)
            if(self.scenario == 4):
                execute_scenario_side(self, packet, True) #TODO: Should call midside, placeholder for testing
            if(self.scenario == 5):
                execute_scenario_side(self, packet, True)

        self.controller_state.throttle = 0.0


        debug_string = str(self.tickCounter)
        debug_string_2 = "Car position: (x: " + str(my_car.physics.location.x) + ", y: " + str(my_car.physics.location.y) + ")"
        draw_debug_2d(self.renderer, debug_string, debug_string_2, str(self.scenario))
        return self.controller_state



def draw_debug(renderer, car, ball, action_display):
    renderer.begin_rendering()

    # draw a line from the car to the ball
    renderer.draw_line_3d(car.physics.location, ball.physics.location, renderer.white())

    # print the action that the bot is taking
    renderer.draw_string_3d(car.physics.location, 2, 2, action_display, renderer.white())

    renderer.end_rendering()



def draw_debug_2d(renderer, debug_string, debug_string_2, debug_string_3):
    renderer.begin_rendering()

    # print debug string
    renderer.draw_string_2d(10, 10, 1,1, debug_string, renderer.white())
    renderer.draw_string_2d(60, 10, 1,1, debug_string_2, renderer.white())
    renderer.draw_string_2d(10, 40, 1,1, debug_string_3, renderer.white())
    renderer.end_rendering()

def execute_scenario_side(self, packet, right):
    my_car = packet.game_cars[self.index]
    car_location = Vec3(my_car.physics.location)

    #Speed control
    speed = math.sqrt(my_car.physics.velocity.x**2 + my_car.physics.velocity.y**2 + my_car.physics.velocity.z**2)
    if(speed < MyBot.kickoff_minimum_speed):
        self.controller_state.boost = True

    #Initial turn
    if(self.tickCounter < MyBot.kickoff_initial_turn_duration_side):
        self.controller_state.steer = 1.0
        if(right):
            self.controller_state.steer = -1.0
    else:
        self.controller_state.steer = 0.0

    #Jump with hold
    if(self.tickCounter >= MyBot.kickoff_speedflip_starting_tick_side and self.tickCounter < MyBot.kickoff_speedflip_starting_tick_side + MyBot.kickoff_initial_jump_hold):
        self.controller_state.jump = True

    #Hold direction 1 tick before sixteenth flip
    if(self.tickCounter == MyBot.kickoff_speedflip_starting_tick_side + MyBot.kickoff_speedflip_delay):
        self.controller_state.pitch = -1.0
        self.controller_state.yaw = MyBot.kickoff_speedflip_yaw
        if(right):
            self.controller_state.yaw = MyBot.kickoff_speedflip_yaw*-1

    #Sixteenth flip
    if(self.tickCounter == MyBot.kickoff_speedflip_starting_tick_side + MyBot.kickoff_speedflip_delay + 1): # 1 Tick buffer so the initial jump doesn't hold over. 
        self.controller_state.pitch = -1.0
        self.controller_state.yaw = MyBot.kickoff_speedflip_yaw
        if(right):
            self.controller_state.yaw = MyBot.kickoff_speedflip_yaw*-1
        self.controller_state.jump = True

    #Flip cancel
    if(self.tickCounter >= MyBot.kickoff_speedflip_starting_tick_side + MyBot.kickoff_speedflip_delay + 2 and self.tickCounter < MyBot.kickoff_speedflip_starting_tick_side + MyBot.kickoff_speedflip_delay + 2 + MyBot.kickoff_flipcancel_duration): # Immediate flip cancel
        self.controller_state.pitch = 1.0
        self.controller_state.roll = -1.0
        if(right):
            self.controller_state.roll = 1.0
        


    #End


def execute_scenario_midside(self, right):
    self.controller_state.boost = True #Placeholder
    #do stuff

def execute_scenario_mid(self):
    self.controller_state.boost = True #Placeholder
    #do stuff

def reset_controller_state(self):
    self.controller_state.throttle = 0.0
    self.controller_state.steer = 0.0
    self.controller_state.pitch = 0.0
    self.controller_state.yaw = 0.0
    self.controller_state.roll = 0.0
    self.controller_state.jump = False
    self.controller_state.boost = False
    self.controller_state.handbrake = False
    self.controller_state.use_item = False
