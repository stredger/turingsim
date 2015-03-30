#
# Stephen Tredger
#
# A pretty cool turing machine simulator
#

import sys
import traceback



class TMTransition(object):
  """ Transition object to hold parameters for transitioning between states """

  def __init__(self, readsymbol, writesymbol, move, nextstate):
    self.readsymbol = readsymbol
    self.writesymbol = writesymbol
    self.move = int(move)
    self.nextstate = int(nextstate)

  def __str__(self):
    return '%s %s %d %d' % (self.readsymbol, self.writesymbol, self.move, self.nextstate)



class TMState(object):
  """ Turing machine state, holds a state index and a set of transitions. 
  transitions are TMTransition objects indexed by the readsymbol """

  def __init__(self, index):
    self.index = int(index)
    self.transitions = {}

  def addTransition(self, trans):
    if trans.readsymbol in self.transitions.keys():
      print 'transition already added for state %d symbol ' \
        '%s overwriting previous: %s with %s' % (self.index, \
        trans.readsymbol, self.transitions[trans.readsymbol], trans)
    self.transitions[trans.readsymbol] = trans

  def __str__(self):
    s = ''
    for tr in self.transitions.values():
      s += '%d %s\n' % (self.index, str(tr))
    return s



class TuringMachine(object):
  """ The Turing Machine object. Needs the name of a 
  file containing a turing machine. Will read the file and 
  parse into a turing machine """

  def __init__(self, fname):

    self.tape = ''
    self.headpos = 0
    self.state = 0
    self.haltstate = 0
    self.states = {}

    TMfile = open(fname)

    # parse the turing machine from the open file.
    #  this sets up the parameters initialized above and
    #  creates states + transitions
    self.parseTMFile(TMfile)
    TMfile.close()


  def getHeadPosAsTapeIndex(self):
    """ return the head position as an index into the TM's tape 
    this is to avoid two zeros as the zero index of the backwards 
    tape is actually head position -1 """
    return abs(self.headpos) - 1 if self.headpos < 0 else self.headpos


  def addStateRule(self, stateind, readsymbol, writesymbol, direction, nextstateind):
    """ create a transition from a state from a set of parameters, 
    as well as the state itself if i doesn't exist yet """

    # make sure these are integers
    stateind = int(stateind)
    direction = int(direction)
    nextstateind = int(nextstateind)

    # we can only move left (-1) and right (1) or not at all (0)
    if direction not in [-1, 0, 1]:
      raise Exception('Invalid state rule. Attempting to move %d when' \
        ' valid values are -1 0 1' % (direction)) 

    # create a transition for the state
    transition = TMTransition(readsymbol, writesymbol, direction, nextstateind)

    # get the state or create a new one if it doesn't exist
    state = self.states.get(stateind)
    if state is None:
      state = TMState(stateind)
      self.states[stateind] = state

    # add the transition to the state
    state.addTransition(transition)


  def parseTMFile(self, TMfile):
    """ given an open file handle, parse the 
    contents into a turing machine definition """
    
    TMdescription = TMfile.readlines()

    # first 4 lines are parameters for the TM
    self.tape = list(TMdescription[0].strip())
    self.backwardtape = []
    self.headpos = int(TMdescription[1])
    self.stateind = int(TMdescription[2])
    self.haltstates = map(lambda n: int(n), TMdescription[3].split())

    # rest of the lines are the state transitions
    for stateline in TMdescription[4:]:
      stateparts = stateline.strip().split(' ')
      if len(stateparts) != 5:
        # print 'malformed state line: %s' % (stateline)
        raise Exception('malformed state line: %s' % (stateline))
      else:
        self.addStateRule(*stateparts)


  def stringifyTape(self, blanks=True):
    # join the backwards tape backwards to the forwards tape
    #  and remove the leading and training blanks if 'blanks' is False
    s = ''.join(self.backwardtape[::-1] + self.tape)
    return s if blanks else s.strip('-')

  def stringifyTMParameters(self):
    sep = ' '
    return 'tape:%s%s\nhead:%s%d\nstate:%s%d\nhaltstate:%s%d' \
      % (sep, self.stringifyTape(), sep, self.headpos, sep, \
        self.stateind, sep, self.haltstate)

  def stringifyTMStateTable(self):
    s = ''
    for state in self.states.values():
      # wont print sorted as .values() returns whatever the dict order is
      s += '%s' % (str(state))
    return s

  def __str__(self):
    return '%s\n%s' % (self.stringifyTMParameters(), self.stringifyTMStateTable())      


  def run(self):
    """ Runs the turing machine until it (hopefully) halts!
    Execution starts by reading the first symbol under the head and stops when we 
    encounter a halting state (a succsessful execution), or the turing machine
    is missing a rule (unsuccsessful) """

    print 'running turing machine!\nhaltstates: %s' % (self.haltstates)

    ops = 0
    while self.stateind not in self.haltstates:
      ops += 1
      print 'tape: %s head: %d state: %d' \
        % (self.stringifyTape(), self.headpos, self.stateind)

      # the tape can be both directions (-, 0 +), 
      #  so get the correct 'half' of the tape
      tape = self.backwardtape if self.headpos < 0 else self.tape

      try:
        # now read the symbol under the head
        symbolread = tape[self.getHeadPosAsTapeIndex()]
      except IndexError, e:
        # if we don't have anything there we are outside the current tape length
        #  so lets extend it with blanks, then say we read the blank symbol '-'
        tape += ['-'] * (self.getHeadPosAsTapeIndex() - (len(tape) - 1))
        symbolread = '-'

      # get the state and the transition we are performing
      currstate = self.states[self.stateind]
      try: trans = currstate.transitions[symbolread]
      except KeyError, e:
        # if no transition can be found for the symbol check the wildcard
        try: trans = currstate.transitions['*']
        except KeyError, e:
          # if no wildcard then we have a problem!
          raise Exception('Error: no valid transition for state: %d symbol: %s' \
            % (currstate.index, symbolread))

      # overwrite the symbol on the tape if its not the wildcard
      if trans.writesymbol != '*':
        tape[self.getHeadPosAsTapeIndex()] = trans.writesymbol

      # move the head and set the next state
      self.headpos += trans.move
      self.stateind = trans.nextstate

    print 'Machine succesfully halted after %d operations!\n' % (ops)



if __name__ == '__main__':
  try:
    # read input file as 1st command line arg
    tmfile = sys.argv[1]
  except IndexError, e:
    print 'Usage: turing.py <Machine Description>'
    sys.exit(1)

  try:
    # parse the turing machine file into a TuringMachine object
    tm = TuringMachine(tmfile)
    # run the actual turing machine
    tm.run()
  except Exception, e:
    # if we have an exception something went wrong, we still want to 
    #  see it so print the traceback but also exit with non zero code
    print traceback.format_exc(),
    sys.exit(1)

  print 'Tape After Execution'
  print tm.stringifyTape(blanks=False)
  sys.exit(0)
