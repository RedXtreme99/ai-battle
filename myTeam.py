# myTeam.py
# ---------
# Licensing Information:  You are free to use or extend these projects for
# educational purposes provided that (1) you do not distribute or publish
# solutions, (2) you retain this notice, and (3) you provide clear
# attribution to UC Berkeley, including a link to http://ai.berkeley.edu.
# 
# Attribution Information: The Pacman AI projects were developed at UC Berkeley.
# The core projects and autograders were primarily created by John DeNero
# (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# Student side autograding was added by Brad Miller, Nick Hay, and
# Pieter Abbeel (pabbeel@cs.berkeley.edu).


from captureAgents import CaptureAgent
import random, time, util
from game import Directions
import game
from util import nearestPoint
from game import Grid

#################
# Team creation #
#################

def createTeam(firstIndex, secondIndex, isRed,
               first = 'DefensiveAgent', second = 'DefensiveAgent'):
  """
  This function should return a list of two agents that will form the
  team, initialized using firstIndex and secondIndex as their agent
  index numbers.  isRed is True if the red team is being created, and
  will be False if the blue team is being created.

  As a potentially helpful development aid, this function can take
  additional string-valued keyword arguments ("first" and "second" are
  such arguments in the case of this function), which will come from
  the --redOpts and --blueOpts command-line arguments to capture.py.
  For the nightly contest, however, your team will be created without
  any extra arguments, so you should make sure that the default
  behavior is what you want for the nightly contest.
  """

  # The following line is an example only; feel free to change it.
  return [eval(first)(firstIndex), eval(second)(secondIndex)]

##########
# Agents #
##########

class DummyAgent(CaptureAgent):
  """
  A Dummy agent to serve as an example of the necessary agent structure.
  You should look at baselineTeam.py for more details about how to
  create an agent as this is the bare minimum.
  """

  def registerInitialState(self, gameState):
    """
    This method handles the initial setup of the
    agent to populate useful fields (such as what team
    we're on).

    A distanceCalculator instance caches the maze distances
    between each pair of positions, so your agents can use:
    self.distancer.getDistance(p1, p2)

    IMPORTANT: This method may run for at most 15 seconds.
    """

    '''
    Make sure you do not delete the following line. If you would like to
    use Manhattan distances instead of maze distances in order to save
    on initialization time, please take a look at
    CaptureAgent.registerInitialState in captureAgents.py.
    '''
    CaptureAgent.registerInitialState(self, gameState)

    '''
    Your initialization code goes here, if you need any.
    '''


  def chooseAction(self, gameState):
    """
    Picks among actions randomly.
    """
    actions = gameState.getLegalActions(self.index)

    '''
    You should change this in your own agent.
    '''

    return random.choice(actions)


class DefensiveAgent(CaptureAgent):
 
    def registerInitialState(self, gameState):
        CaptureAgent.registerInitialState(self, gameState)
        self.myAgents = CaptureAgent.getTeam(self, gameState)
        self.opAgents = CaptureAgent.getOpponents(self, gameState)
        self.myFoods = CaptureAgent.getFood(self, gameState).asList()
        self.opFoods = CaptureAgent.getFoodYouAreDefending(self, gameState).asList()
        self.start = gameState.getAgentPosition(self.index)
        self.teamStart = [gameState.getInitialAgentPosition(i) for i in self.myAgents]
        self.opsStart = [gameState.getInitialAgentPosition(i) for i in self.opAgents]

        self.walls = gameState.getWalls()
        corner = self.walls.asList()[-1]
        self.width = corner[0] + 1
        self.height = corner[1] + 1
        if self.red:
            half = self.width // 2 - 1
        else:
            half = self.width // 2
        self.borderPoints = []
        for i in range(self.height):
            if not self.walls[half][i]:
                self.borderPoints.append((half, i))

    def getSuccessor(self, gameState, action):
        successor = gameState.generateSuccessor(self.index, action)
        pos = successor.getAgentState(self.index).getPosition()
        if pos != nearestPoint(pos):
            return successor.generateSuccessor(self.index, action)
        return successor

    def getFeatures(self, gameState, action):
        features = util.Counter()
        successor = self.getSuccessor(gameState, action)
        state = successor.getAgentState(self.index)
        pos = state.getPosition()

        features['onDefense'] = 1
        if state.isPacman:
            features['onDefense'] = 0
        distsToBorder = [self.getMazeDistance(pos, x) for x in self.borderPoints]
        features['borderDistance'] = sum(distsToBorder)

        return features

    def getWeights(self, gameState, action):
        return {'onDefense': 50000, 'borderDistance' : -100}

    def evaluate(self, gameState, action):
        features = self.getFeatures(gameState, action)
        weights = self.getWeights(gameState, action)
        return features * weights
        
    def chooseAction(self, gameState):
        agentPos = gameState.getAgentPosition(self.index)
        actions = gameState.getLegalActions(self.index)

        values = [self.evaluate(gameState, a) for a in actions]
        maxValue = max(values)
        bestActions = [a for a, v in zip(actions, values) if v == maxValue]

        return random.choice(actions)
