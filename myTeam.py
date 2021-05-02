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
import distanceCalculator
import random, time, util
from game import Directions
import game
from util import nearestPoint

#################
# Team creation #
#################

def createTeam(firstIndex, secondIndex, isRed,
               first = 'OffensiveAgentOne', second = 'DefensiveAgentOne'):
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
class ReflexCaptureAgent(CaptureAgent):
  """
  A base class for reflex agents that chooses score-maximizing actions
  """
 
  def registerInitialState(self, gameState):
    self.start = gameState.getAgentPosition(self.index)
    self.startFood= len(self.getFood(gameState).asList())
    self.startFriendlyFood = len(self.getFoodYouAreDefending(gameState).asList())
    CaptureAgent.registerInitialState(self, gameState)

  def chooseAction(self, gameState):
    """
    Picks among the actions with the highest Q(s,a).
    """
    actions = gameState.getLegalActions(self.index)

    # You can profile your evaluation time by uncommenting these lines
    #start = time.time()
    values = [self.evaluate(gameState, a) for a in actions]
    #print 'eval time for agent %d: %.4f' % (self.index, time.time() - start)

    maxValue = max(values)
    bestActions = [a for a, v in zip(actions, values) if v == maxValue]

    foodLeft = len(self.getFood(gameState).asList())

    if foodLeft <= 2:
      bestDist = 9999
      for action in actions:
        successor = self.getSuccessor(gameState, action)
        pos2 = successor.getAgentPosition(self.index)
        dist = self.getMazeDistance(self.start,pos2)
        if dist < bestDist:
          bestAction = action
          bestDist = dist
      return bestAction

    return random.choice(bestActions)
  def getSuccessor(self, gameState, action):
    """
    Finds the next successor which is a grid position (location tuple).
    """
    successor = gameState.generateSuccessor(self.index, action)
    pos = successor.getAgentState(self.index).getPosition()
    if pos != nearestPoint(pos):
      # Only half a grid position was covered
      return successor.generateSuccessor(self.index, action)
    else:
      return successor

  def evaluate(self, gameState, action):
    """
    Computes a linear combination of features and feature weights
    """
    features = self.getFeatures(gameState, action)
    weights = self.getWeights(gameState, action)
    return features * weights

  def getFeatures(self, gameState, action):
    """
    Returns a counter of features for the state
    """
    features = util.Counter()
    successor = self.getSuccessor(gameState, action)
    features['successorScore'] = self.getScore(successor)
    return features

  def getWeights(self, gameState, action):
    """
    Normally, weights do not depend on the gamestate.  They can be either
    a counter or a dictionary.
    """
    return {'successorScore': 1.0}

class OffensiveAgentOne(ReflexCaptureAgent):
  """
  A reflex agent that seeks food. This is an agent
  we give you to get an idea of what an offensive agent might look like,
  but it is by no means the best or only way to build an offensive agent.
  """
  def getFeatures(self, gameState, action):
    features = util.Counter()
    successor = self.getSuccessor(gameState, action)
    foodList = self.getFood(successor).asList()
    capsuleList = self.getCapsules(successor)
    myPos = successor.getAgentState(self.index).getPosition()
    friendlyFoodList = self.getFoodYouAreDefending(successor).asList()
    features['isPacman'] = 0
    if action == Directions.STOP: features['stop'] = 1
    if successor.getAgentState(self.index).isPacman:
      features['isPacman'] = 1000
    else:
      #just in case, update start food as if we cashed in
      self.startFood = len(foodList)
    features['successorScore'] = -len(foodList)#self.getScore(successor)
    features['currentScore'] = self.getScore(successor)
    foodInStore = self.startFood - len(foodList)
    
    # Compute distance to the nearest food
    

    if len(foodList) > 0: # This should always be True,  but better safe than sorry
      
      minDistance = min([self.getMazeDistance(myPos, food) for food in foodList])
      features['distanceToFood'] = minDistance
      
    # Compute distance back to team's side (using closest friendly food)
    #distanceHome = min([self.getMazeDistance(myPos, food) for food in friendlyFoodList])
    #features['distanceHome'] = distanceHome

    #Compute Distance back to team's side
    sucBound = min(self.getMazeDistance(myPos, b) for b in self.boundary)
    features['distanceHome'] = sucBound
    
    #Look for ghosts and avoid them at all costs if not powered up
    features['enemyDistance'] = 100
    enemies = [successor.getAgentState(i) for i in self.getOpponents(successor)]
    defenders = [a for a in enemies if (not a.isPacman) and a.getPosition() != None]
    #don't worry about scared ghosts
    if len(defenders) > 0 and not enemies[0].scaredTimer > 10:
      dists = [self.getMazeDistance(myPos, a.getPosition()) for a in defenders]
      features['enemyDistance'] = min(dists)
      if min(dists) < 5:
        features['distanceHome'] = 20
        features['enemyDistance'] = 0.5*min(dists)
    if (foodInStore >= .2*self.startFood and foodInStore >= 5) or foodInStore > 30:
      if successor.getAgentState(self.index).isPacman and not enemies[0].scaredTimer > 0:
        features['isPacman'] = 0
      features['distanceHome'] = sucBound * foodInStore
    elif not successor.getAgentState(self.index).isPacman:
      features['distanceHome'] = 0
    else:
      features['distanceHome'] = 1000
    #eat capsules
    if len(capsuleList) > 0:
      capsuleDistance = min([self.getMazeDistance(myPos, cap) for cap in capsuleList])
      features['DistanceToCapsule'] = capsuleDistance
    else:
      features['DistanceToCapsule'] = 0
    features['capsLeft'] = -len(capsuleList)

    #If power up is active, try not to eat a capsule
    if enemies[0].scaredTimer > 10:
        features['capsLeft'] = 0
        if len(capsuleList)>0:
            features['DistanceToCapsule'] = 0
    
    return features



  def getWeights(self, gameState, action):
    successor = self.getSuccessor(gameState, action)
    #when running out of time, get back to our side
    myPos = successor.getAgentState(self.index).getPosition()
    sucBound = min(self.getMazeDistance(myPos, b) for b in self.boundary)
    if successor.data.timeleft <= sucBound*4+8:
          return {'currentScore': 100, 'successorScore': 1000, 'distanceToFood': -1, 'distanceHome': -100, 'enemyDistance': 10, 'isPacman': 0, 'stop': -100, 'DistanceToCapsule': -15, 'capsLeft': 500}
    return {'currentScore': 100, 'successorScore': 1000, 'distanceToFood': -10, 'distanceHome': -1, 'enemyDistance': 5, 'isPacman': 1, 'stop': -100, 'DistanceToCapsule': -15, 'capsLeft': 500}
 

class DefensiveAgentOne(ReflexCaptureAgent):
  """
  A reflex agent that keeps its side Pacman-free. Again,
  this is to give you an idea of what a defensive agent
  could be like.  It is not the best or only way to make
  such an agent.
  """

  def getFeatures(self, gameState, action):
    features = util.Counter()
    successor = self.getSuccessor(gameState, action)
    foodList = self.getFood(successor).asList()
    friendlyFoodList = self.getFoodYouAreDefending(successor).asList()
    myState = successor.getAgentState(self.index)
    myPos = myState.getPosition()
    features['successorScore'] = -len(foodList)
    # Computes whether we're on defense (1) or offense (0)
    features['onDefense'] = 1
    if myState.isPacman: features['onDefense'] = 0

    if len(foodList) > 0: # This should always be True,  but better safe than sorry
      myPos = successor.getAgentState(self.index).getPosition()
      minDistance = min([self.getMazeDistance(myPos, food) for food in foodList])
      features['distanceToFood'] = minDistance

    # Computes distance to invaders we can see
    enemies = [successor.getAgentState(i) for i in self.getOpponents(successor)]
    invaders = [a for a in enemies if a.isPacman and a.getPosition() != None]
    features['numInvaders'] = len(invaders)
    if len(invaders) > 0:
      dists = [self.getMazeDistance(myPos, a.getPosition()) for a in invaders]
      features['invaderDistance'] = min(dists)
      #dont try to eat when you're a ghost
      if myState.scaredTimer > 0:
        features['numInvaders'] = -len(invaders)
        features['invaderDistance']= -min(dists)

    if action == Directions.STOP: features['stop'] = 1
    rev = Directions.REVERSE[gameState.getAgentState(self.index).configuration.direction]
    if action == rev: features['reverse'] = 1


    
    #if not chasing, station near as many dots as you can
    fooddist = [self.getMazeDistance(myPos, a) for a in friendlyFoodList]
    totaldist = 0
    for i in fooddist:
      totaldist+=i**0.8
    features['foodDistance'] = totaldist


    
    return features

  def getWeights(self, gameState, action):
    successor = self.getSuccessor(gameState, action)
    if successor.data.timeleft < 250 and self.getScore(successor) < 0:
      return {'numInvaders': -0, 'onDefense': 0, 'invaderDistance': 0, 'stop': 0, 'reverse': 0, 'foodDistance': 0, 'successorScore': 100, 'distanceToFood': -1}
    return {'numInvaders': -1000, 'onDefense': 100, 'invaderDistance': -100, 'stop': -100, 'reverse': -2, 'foodDistance': -5, 'successorScore': 0, 'distanceToFood': 0}





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

