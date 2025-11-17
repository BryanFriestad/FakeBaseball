from enum import Enum
import random


sizes = [70, 140, 70, 110, 220, 110, 70, 140, 70]
assert(len(sizes) == 9)
assert(sum(sizes) == 1000)
take_sizes = [28, 49, 28, 30, 0, 30, 28, 49, 28]
zone_boundaries = [(sum(sizes[:i]) + 1, sum(sizes[:i+1])) for i in range(len(sizes))]

contact_neighbors = [[1], [0, 2], [1], [4], [3, 5], [4], [7], [6, 8], [7]]
foul_neighbors = [[3, 4], [3, 4, 5], [4, 5], [0, 1, 6, 7], [0, 1, 2, 6, 7, 8], [1, 2, 7, 8], [3, 4], [3, 4, 5], [4, 5]]

delta_table = {"homerun": 1, "triple": 5, "double": 22, "single": 58, "groundball": 97, "sacfly": 128, "popout": 189, "fielderschoice": 229, "doubleplay": 329}

def find_grid_index(x):
    assert x > 0 and x <= 1000
    for i in range(len(zone_boundaries)):
        if x <= zone_boundaries[i][1]:
            return i
    assert False


def get_zone_boundaries(zone_index):
    assert zone_index >= 0 and zone_index < len(sizes)
    return zone_boundaries[zone_index]


def is_pitch_outside(pitch):
    zone_index = find_grid_index(pitch)
    boundaries = get_zone_boundaries(zone_index)
    take_size = take_sizes[zone_index]
    return pitch < boundaries[0] + take_size or pitch > boundaries[1] - take_size


class PAOutcome(Enum):
    STRIKEOUT = 0
    WALK = 1
    HR = 2
    TRIPLE = 3
    DOUBLE = 4
    SINGLE = 5
    GB = 6
    SF = 7
    DP = 8
    PO = 9
    FC = 10


class GameState:
    def __init__(self):
        self.inning = 1
        self.top = True
        self.score = [0, 0]
        self.outs = 0
        self.strikes = 0
        self.balls = 0
        self.bases = [False, False, False]
        self.outcomes = {outcome: 0 for outcome in PAOutcome}
        self.pa_count = 0

    def _change_inning(self):
        self.bases = [False, False, False]
        self.outs = 0
        if self.top:
            self.top = False
        else:
            self.top = True
            self.inning += 1

    def _end_pa(self, outcome: PAOutcome):
        self.strikes = 0
        self.balls = 0
        self.outcomes[outcome] += 1
        self.pa_count += 1

    def _strikeout(self):
        self.outs += 1
        if self.outs == 3:
            self._change_inning()
        self._end_pa(PAOutcome.STRIKEOUT)

    def strike(self):
        self.strikes += 1
        if self.strikes == 3:
            self._strikeout()

    def ball(self):
        self.balls += 1
        if self.balls == 4:
            self._walk()

    def foul(self):
        if self.strikes < 2:
            self.strikes += 1

    def _walk(self):
        self._advance_forced_runners()
        self.bases[0] = True
        self._end_pa(PAOutcome.WALK)

    def _num_on_base(self):
        return sum(self.bases)

    def _leading_runner_position(self):
        if self.bases[2]:
            return 2
        if self.bases[1]:
            return 1
        if self.bases[0]:
            return 0
        return -1

    def _forced_runner_positions(self):
        '''
        Returns a list of forced runner positions in order from least to most advanced
        '''
        positions = []
        if self.bases[0]:
            positions.append(0)
            if self.bases[1]:
                positions.append(1)
                if self.bases[2]:
                    positions.append(2)
        return positions

    def _leading_forced_runner_position(self):
        forced_runners = self._forced_runner_positions()
        if len(forced_runners) == 0:
            return -1
        return max(forced_runners)

    def _advance_forced_runners(self):
        forced_runners = self._forced_runner_positions()
        for runner in forced_runners:
            self.bases[runner] = False
            if runner == 2:
                self.score[0 if self.top else 1] += 1
            else:
                self.bases[runner + 1] = True

    def home_run(self):
        self.score[0 if self.top else 1] += (self._num_on_base() + 1)
        self.bases = [False, False, False]
        self._end_pa(PAOutcome.HR)

    def triple(self):
        self.score[0 if self.top else 1] += self._num_on_base()
        self.bases = [False, False, True]
        self._end_pa(PAOutcome.TRIPLE)

    def double(self):
        '''
        Runners on second and third score, runner on first moves to third, batter at second
        '''
        runners_home = self.bases[1] + self.bases[2]
        self.bases[2] = self.bases[0]
        self.bases[1] = True
        self.bases[0] = False
        self.score[0 if self.top else 1] += runners_home
        self._end_pa(PAOutcome.DOUBLE)

    def single(self):
        '''
        Anyone on third base scores. 
        Anyone on second base moves to third base. 
        Anyone on first base moves to second base. 
        The batter is placed on first base.
        '''
        runners_home = self.bases[2]
        self.bases[2] = self.bases[1]
        self.bases[1] = self.bases[0]
        self.bases[0] = True
        self.score[0 if self.top else 1] += runners_home
        self._end_pa(PAOutcome.SINGLE)

    def ground_ball(self):
        '''
        Batter is out.
        Any forced runners advance one base.
        '''
        self.outs += 1
        if self.outs == 3:
            self._end_pa(PAOutcome.GB)
            self._change_inning()
            return
        self._advance_forced_runners()
        self._end_pa(PAOutcome.GB)

    def sac_fly(self):
        '''
        Batter is out.
        Any runner on third base scores.
        All other runners hold.
        '''
        self.outs += 1
        if self.outs == 3:
            self._end_pa(PAOutcome.SF)
            self._change_inning()
            return
        if self.bases[2]:
            self.score[0 if self.top else 1] += 1
            self.bases[2] = False
        self._end_pa(PAOutcome.SF)

    def double_play(self):
        '''
        Batter is out.
        If there are less than three outs, the leading forced runner is out.
        All other forced runners advance one base.
        All other runners hold.
        '''
        self.outs += 1
        if self.outs == 3:
            self._end_pa(PAOutcome.DP)
            self._change_inning()
            return

        #  the leading forced runner is out
        lead_forced_runner = self._leading_forced_runner_position()
        if lead_forced_runner != -1:
            self.bases[lead_forced_runner] = False
            self.outs += 1
            if self.outs == 3:
                self._end_pa(PAOutcome.DP)
                self._change_inning()
                return
        
        # all other forced runners advance one base
        self._advance_forced_runners()
        self._end_pa(PAOutcome.DP)

    def pop_out(self):
        '''
        Batter is out. All runners hold.
        '''
        self.outs += 1
        if self.outs == 3:
            self._end_pa(PAOutcome.PO)
            self._change_inning()
            return
        self._end_pa(PAOutcome.PO)

    def fielders_choice(self):
        '''
        If there are no runners on base, the batter is out.
        Otherwise, the lead runner is out, all forced runners advance one base, and the batter is placed on first base.
        '''
        lead_runner = self._leading_runner_position()
        if lead_runner == -1: # there are no baserunners, instead the batter is out
            self.outs += 1
            if self.outs == 3:
                self._change_inning()
            self._end_pa(PAOutcome.FC)
            return # return early if there are no baserunners
            
        # go for lead runner
        self.bases[lead_runner] = False
        self.outs += 1
        if self.outs == 3:
            self._end_pa(PAOutcome.FC)
            self._change_inning()
            return

        self._advance_forced_runners()
        self.bases[0] = True
        self._end_pa(PAOutcome.FC)

swing_outcomes = ["whiff", "foul", "hr", "triple", "double", "single", "gb", "sf", "po", "fc", "dp"]
swing_outcome_counts = [0 for _ in range(len(swing_outcomes))]

diffs = []

outside_count = 0

def pitch(state: GameState, pitch_func, swing_func) -> bool:
    '''
    Returns true if the pitch ends the plate appearance, false otherwise
    '''
    pitch = pitch_func(state)
    swing = swing_func(state)

    global outside_count
    if is_pitch_outside(pitch):
        outside_count += 1

    # Batter did not swing
    if swing == -1:
        if is_pitch_outside(pitch):
            balls_before = state.balls
            state.ball()
            if balls_before == 3:
                return True
        else:
            strikes_before = state.strikes
            state.strike()
            if strikes_before == 2:
                return True
        return False
    
    pitch_index = find_grid_index(pitch)
    swing_index = find_grid_index(swing)
    
    if pitch_index == swing_index or pitch_index in contact_neighbors[swing_index]:
        diff = abs(pitch - swing)
        diffs.append(diff)
        if diff <= delta_table["homerun"]:
            state.home_run()
            swing_outcome_counts[2] += 1
        elif diff <= delta_table["triple"]:
            state.triple()
            swing_outcome_counts[3] += 1
        elif diff <= delta_table["double"]:
            state.double()
            swing_outcome_counts[4] += 1
        elif diff <= delta_table["single"]:
            state.single()
            swing_outcome_counts[5] += 1
        elif diff <= delta_table["groundball"]:
            state.ground_ball()
            swing_outcome_counts[6] += 1
        elif diff <= delta_table["sacfly"]:
            state.sac_fly()
            swing_outcome_counts[7] += 1
        elif diff <= delta_table["popout"]:
            state.pop_out()
            swing_outcome_counts[8] += 1
        elif diff <= delta_table["fielderschoice"]:
            state.fielders_choice()
            swing_outcome_counts[9] += 1
        elif diff <= delta_table["doubleplay"]:
            state.double_play()
            swing_outcome_counts[10] += 1
        else:
            assert False, "Invalid swing delta" + str(diff)
        return True
    elif pitch_index in foul_neighbors[swing_index]:
        state.foul()
        swing_outcome_counts[1] += 1
        return False
    else:
        strikes_before = state.strikes
        state.strike()
        swing_outcome_counts[0] += 1
        if strikes_before == 2:
            return True
        return False


def formatAsPercent(val):
    return '{:05.3%}'.format(val)


def print_diffs():
    unique_diffs = set(diffs)
    for diff in unique_diffs:
        count = diffs.count(diff)
        print(str(diff) + ": " + formatAsPercent(count / len(diffs)))


def print_swing_outcomes():
    swing_count = sum([v for v in swing_outcome_counts])
    print("Swing count: " + str(swing_count))
    for i in range(len(swing_outcomes)):
        print(swing_outcomes[i] + ": " + formatAsPercent(swing_outcome_counts[i] / swing_count))

def print_pa_outcomes(state: GameState):
    print("PA count: " + str(state.pa_count))
    for k, v in state.outcomes.items():
        print(str(k) + ": " + formatAsPercent(v / state.pa_count))
    hits = state.outcomes[PAOutcome.HR] + state.outcomes[PAOutcome.TRIPLE] + state.outcomes[PAOutcome.DOUBLE] + state.outcomes[PAOutcome.SINGLE]
    print("Batting Avg.: " + formatAsPercent(hits / state.pa_count))


def sim_pa(state: GameState, pitch_func, swing_func):
    pitch_count = 1
    while not pitch(state, pitch_func, swing_func):
        pitch_count += 1
    return pitch_count


def sim_game(pitch_func, swing_func):
    state = GameState()
    pitch_count = 0
    while state.inning < 10:
        pitch_count += sim_pa(state, pitch_func, swing_func)
    print("Pitch count: " + str(pitch_count))
    print_swing_outcomes()    
    print_pa_outcomes(state)
    print(state.score)


def simulate(pitch_func, swing_func, pa_count):
    state = GameState()
    pitch_counts = []
    for i in range(pa_count):
        pitch_counts.append(sim_pa(state, pitch_func, swing_func))
    print_swing_outcomes()
    print_pa_outcomes(state)


def random_pitch(state: GameState):
    return random.randint(1, 1000)

def random_swing(state: GameState):
    if random.random() < 0.53:
        return -1
    return random.randint(1, 1000)

swing_probabilities = [
    [26.64, 46.62, 49.91],
    [40.54, 53.27, 57.88],
    [39.03, 59.10, 65.68],
    [06.42, 54.72, 73.84]
]

def realistic_take_swing(state: GameState):
    prob = swing_probabilities[state.balls][state.strikes] / 100
    if random.random() < prob:
        return random.randint(1, 1000)
    return -1

def random_swing_no_take(state: GameState):
    return random.randint(1, 1000)

r = list(range(117, 164)) + list(range(837, 884))

def test1(state: GameState):
    return random.choice(r)

def inside_only(state: GameState):
    r = list(range(391, 610))
    return random.choice(r)

def edges_only(state: GameState):
    r = list(range(218, 390)) + list(range(611, 720))
    return random.choice(r)

def top_only(state: GameState):
    r = list(range(71, 210)) + list(range(790, 930))
    return random.choice(r)

def corners_only(state: GameState):
    r = list(range(1, 70)) + list(range(211, 280)) + list(range(720, 790)) + list(range(931, 1000))
    return random.choice(r)

if __name__ == "__main__":
    simulate(corners_only, top_only, 200000)
    print("Outside count: " + str(outside_count))
        