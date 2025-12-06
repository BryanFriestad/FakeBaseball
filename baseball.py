from enum import Enum
import random
from game_state import GameState, PAOutcome

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
    avg = hits / (state.pa_count - state.outcomes[PAOutcome.WALK])
    obp = (hits + state.outcomes[PAOutcome.WALK]) / (state.pa_count)
    print("Batting Avg.: " + formatAsPercent(avg))
    print("On Base Percentage: " + formatAsPercent(obp))


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
    # print_swing_outcomes()
    # return print_pa_outcomes(state)
    hits = state.outcomes[PAOutcome.HR] + state.outcomes[PAOutcome.TRIPLE] + state.outcomes[PAOutcome.DOUBLE] + state.outcomes[PAOutcome.SINGLE]
    avg = hits / (state.pa_count - state.outcomes[PAOutcome.WALK])
    obp = (hits + state.outcomes[PAOutcome.WALK]) / (state.pa_count)
    return avg, obp


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

def middle_only(state: GameState):
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
    pitch_algos = [random_pitch, middle_only, edges_only, top_only, corners_only]
    swing_algos = [top_only]
    illegal = [(middle_only, top_only), (middle_only, corners_only), (edges_only, top_only), (edges_only, corners_only), (top_only, middle_only), (top_only, edges_only), (corners_only, middle_only), (corners_only, edges_only)]
    for pitch_algo in pitch_algos:
        for swing_algo in swing_algos:
            if (pitch_algo, swing_algo) in illegal:
                continue
            print("Simulating " + str(pitch_algo.__name__) + " vs " + str(swing_algo.__name__))
            avg, obp = simulate(pitch_algo, swing_algo, 200000)
            avg = (avg * 1000) // 1
            obp = (obp * 1000) // 1
            print("Avg: " + str('{:.0f}'.format(avg)))
            print("OBP: " + str('{:.0f}'.format(obp)))
            print("\n")
        