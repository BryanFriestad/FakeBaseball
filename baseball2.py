import random
import csv
from game_state import GameState, PAOutcome
from PitchOutcomes import PitchOutcome, OutcomeTable, parse_outcomes_csv
from Zone import Zone, parse_zone_csv


def save_as_csv(table, csv_path, header = None):
    """Save a table (list of lists) to a CSV file."""
    with open(csv_path, 'w', newline='') as file:
        writer = csv.writer(file)
        if header: writer.writerow(header)
        for row in table:
            writer.writerow(row)


class TeamStrategy():
    def __init__(self, pitch_algo, swing_algo):
        self.pitch_algo = pitch_algo
        self.swing_algo = swing_algo


class Baseball2PitchAdapter():

    def __init__(self, zone, outcome_table):
        self.zone = zone
        self.outcome_table = outcome_table

    def sim_pitch(self, state: GameState, pitch_algo, swing_algo) -> PitchOutcome:
        pitch = pitch_algo(state)
        swing = swing_algo(state)
        outcome = self.outcome_table.get_outcome(self.zone, pitch, swing)
    
        # Map numeric outcomes to GameState methods
        outcome_mapping = {
            PitchOutcome.HR: state.home_run,
            PitchOutcome.TRIPLE: state.triple,
            PitchOutcome.DOUBLE: state.double,
            PitchOutcome.SINGLE: state.single,
            PitchOutcome.FOUL: state.foul,
            PitchOutcome.SF: state.sac_fly,
            PitchOutcome.PO: state.pop_out,
            PitchOutcome.GB: state.ground_ball,
            PitchOutcome.FC: state.fielders_choice,
            PitchOutcome.DP: state.double_play,
            PitchOutcome.STRIKE: state.strike,
            PitchOutcome.BALL: state.ball
        }
        
        if outcome in outcome_mapping:
            outcome_mapping[outcome]()
        else:
            raise ValueError(f"Unknown outcome: {outcome}")
        
        return outcome


def sim_plate_appearance(sim_pitch_func, state: GameState, pitch_algo, swing_algo, verbose=False):
    """
    Simulate a complete plate appearance (multiple pitches until it ends).
    Returns the PAOutcome of the plate appearance.
    """
    while True:
        # Store the current state to detect if plate appearance ended
        initial_pa_count = state.pa_count
        initial_outs = state.outs
        initial_balls = state.balls
        initial_strikes = state.strikes
        
        outcome = sim_pitch_func(state, pitch_algo, swing_algo)
        
        # Check if plate appearance ended:
        # - PA count increased (means at-bat completed with hit/out)
        # - Outs increased (means at-bat completed with out)
        # - Balls reset to 0 (means walk occurred)
        # - Strikes reset to 0 (means strikeout occurred)
        # AND it wasn't a foul ball
        if outcome != PitchOutcome.FOUL and (state.pa_count > initial_pa_count or 
                            state.outs > initial_outs or
                            (state.balls < initial_balls) or
                            (state.strikes < initial_strikes)):
            
            # Map numeric outcomes to PAOutcome enum
            outcome_to_paoutcome = {
                PitchOutcome.HR: PAOutcome.HR,
                PitchOutcome.TRIPLE: PAOutcome.TRIPLE,
                PitchOutcome.DOUBLE: PAOutcome.DOUBLE,
                PitchOutcome.SINGLE: PAOutcome.SINGLE,
                PitchOutcome.SF: PAOutcome.SF,
                PitchOutcome.PO: PAOutcome.PO,
                PitchOutcome.GB: PAOutcome.GB,
                PitchOutcome.FC: PAOutcome.FC,
                PitchOutcome.DP: PAOutcome.DP,
                PitchOutcome.STRIKE: PAOutcome.STRIKEOUT,
                PitchOutcome.BALL: PAOutcome.WALK
            }

            if verbose:
                print(f"PAOutcome: {outcome_to_paoutcome[outcome].name}")
            
            return outcome_to_paoutcome[outcome]

def sim_game(sim_pitch_func, strategyA: TeamStrategy, strategyB: TeamStrategy, aHome: bool = True, verbose=False):
    """
    Simulate a full game (9+ innings).
    Uses default algorithms if none provided.
    Ends in the middle of an inning if home team is winning (9th inning or later).
    Continues to extra innings if tied after 9.
    Ends in a tie if still tied after 18 innings.
    """

    homeStrategy = strategyA if aHome else strategyB
    awayStrategy = strategyB if aHome else strategyA
    
    state = GameState()
    
    # Sim regular innings
    while state.inning < 10:
        if verbose:
            print(f"Top of {state.inning}")
            print(f"Current score: {state.score}")
        while state.top:
            sim_plate_appearance(sim_pitch_func, state, homeStrategy.pitch_algo, awayStrategy.swing_algo, verbose)

        if verbose:
            print(f"Bottom of {state.inning}")
            print(f"Current score: {state.score}")
        while not state.top:
            sim_plate_appearance(sim_pitch_func, state, awayStrategy.pitch_algo, homeStrategy.swing_algo, verbose)
            if state.inning == 9 and state.score[1] > state.score[0]:
                break

    # Sim extra innings
    if state.score[0] == state.score[1]:
        while state.inning <= 18:
            if verbose:
                print(f"Top of {state.inning}")
                print(f"Current score: {state.score}")
            while state.top:
                sim_plate_appearance(sim_pitch_func, state, homeStrategy.pitch_algo, awayStrategy.swing_algo, verbose)

            if verbose:
                print(f"Bottom of {state.inning}")
                print(f"Current score: {state.score}")
            while not state.top:
                sim_plate_appearance(sim_pitch_func, state, awayStrategy.pitch_algo, homeStrategy.swing_algo, verbose)
            if state.score[1] > state.score[0]:
                break
        
    # Print game results
    if verbose:
        print(f"Plate appearances: {state.pa_count}")
        print(f"Final score: {state.score}")
        print(f"Innings played: {state.inning - 1}")
    
    return state


def sim_games(num_games, strategyA: TeamStrategy, strategyB: TeamStrategy):
    """
    Simulate multiple games and return average runs per team per game.
    """    
    total_runs_teamA = 0
    total_runs_teamB = 0
    a_wins = 0
    b_wins = 0
    ties = 0
    
    for i in range(num_games):
        a_home = random.random() > 0.5
        state = sim_game(strategyA, strategyB, a_home)
        a_score = state.score[1] if a_home else state.score[0]
        b_score = state.score[0] if a_home else state.score[1]
        
        # Track wins and ties
        if a_score > b_score:
            a_wins += 1
        elif b_score > a_score:
            b_wins += 1
        else:
            ties += 1

        total_runs_teamA += a_score
        total_runs_teamB += b_score
        
        # Print progress every 100 games
        if (i + 1) % 100 == 0:
            print(f"Completed {i + 1}/{num_games} games")

    # Calculate runs per 9 innings
    # avg_runs_team1_per_9 = (total_runs_team1 / total_innings_team1) * 9 if total_innings_team1 > 0 else 0
    # avg_runs_team2_per_9 = (total_runs_team2 / total_innings_team2) * 9 if total_innings_team2 > 0 else 0

    # Calculate win rates
    a_win_rate = (a_wins / num_games) * 100
    b_win_rate = (b_wins / num_games) * 100
    tie_rate = (ties / num_games) * 100

    print(f"\nResults after {num_games} games:")
    # print(f"Average runs per 9 innings - Team 1 (away): {avg_runs_team1_per_9:.2f}")
    # print(f"Average runs per 9 innings - Team 2 (home): {avg_runs_team2_per_9:.2f}")
    print(f"Team A win rate: {a_win_rate:.1f}% ({a_wins}/{num_games})")
    print(f"Team B win rate: {b_win_rate:.1f}% ({b_wins}/{num_games})")
    print(f"Tie rate: {tie_rate:.1f}% ({ties}/{num_games})")


def pa_stats(sim_pitch_func, pitch_algo, swing_algo, sims = 10000):
    counts = {outcome: 0 for outcome in PAOutcome}
    for _ in range(sims):
        counts[sim_plate_appearance(sim_pitch_func, GameState(), pitch_algo=pitch_algo, swing_algo=swing_algo)] += 1
    
    for outcome, num in counts.items():
        rate = 100 * (num / sims)
        print(f'Outcome - {outcome} - {rate:.1f}%')

swing_probabilities = [
    [26.64, 46.62, 49.91],
    [40.54, 53.27, 57.88],
    [39.03, 59.10, 65.68],
    [06.42, 54.72, 73.84]
]

def realistic_take_swing(state: GameState):
    prob = swing_probabilities[state.balls][state.strikes] / 100
    if random.random() < prob:
        return swing(state)
    return -1
    
def swing(state: GameState):
    x = random.randint(9, 24)
    y = random.randint(5, 28)
    return x + ((y-1)*32)

def smart_pitch(state: GameState):
    outside_picks = [1, 2, 33, 34, 16, 17, 48, 49, 31, 31, 63, 64, 481, 482, 513, 514, 511, 512, 543, 544, 961, 962, 993, 994, 976, 977, 1008, 1009, 991, 992, 1023, 1024]
    inside_picks = [137, 152, 873, 888, 489, 504]
    return random.choice(outside_picks + inside_picks)

def rings(state: GameState):
    outer_ring = [x for x in range(1, 33)] + [x for x in range(993, 1025)] + [x for x in range(33, 962, 32)] + [x for x in range(64, 993, 32)]
    inner_ring = [x for x in range(137, 153)] + [x for x in range(873, 889)] + [x for x in range(169, 842, 32)] + [x for x in range(184, 857, 32)]
    return random.choice(outer_ring + inner_ring)

def player_swing(state: GameState):
    x = input("Swing number?: ")
    return int(x)

def middle_swings(state: GameState):
    return random.choice([752, 720, 688, 656, 624, 592, 560, 528, 496, 464, 432, 400, 368, 336, 304, 272])

def count_outcome_table_rates():
    # count outcome table rates
    pitch_algo = rings
    swing_algo = middle_swings
    outcome_table_counts = [[0 for _ in range(len(outcome_table[0]))] for _ in range(len(outcome_table))]
    whiff_count = 0
    num_swings = 10000000
    for x in range(num_swings):
        if x % (num_swings // 10) == 0:
            print(f'Progress - {x*100 // num_swings}%')

        pitch = pitch_algo(None)
        swing = swing_algo(None)

        if swing == -1:
            x -= 1
        
        pitch_x, pitch_y = index_to_position(pitch)
        swing_x, swing_y = index_to_position(swing)
        
        outcome_table_position = (pitch_x - swing_x + outcome_table_center[0], pitch_y - swing_y + outcome_table_center[1])

        if outcome_table_position[0] < 0 or outcome_table_position[0] >= len(outcome_table[0]) or outcome_table_position[1] < 0 or outcome_table_position[1] >= len(outcome_table):
            whiff_count += 1
            continue
        
        outcome_table_counts[outcome_table_position[1]][outcome_table_position[0]] += 1

    outcome_table_rates = [[(count / num_swings) for count in row] for row in outcome_table_counts]
    save_as_csv(outcome_table_rates, "FakeBaseball 2/rings_vs_middle_swings_outcome_table_rates.csv")

if __name__ == "__main__":
    # sim_game(pitch_algo=lambda: random.randint(1, size), swing_algo=swing, verbose=True)
    # sim_plate_appearance(GameState(), pitch_algo=lambda: random.randint(1, size), swing_algo=swing, verbose=True)

    zone = Zone(parse_zone_csv("FakeBaseball 2/zone.csv"))
    outcome_table = OutcomeTable(parse_outcomes_csv("FakeBaseball 2/outcomes.csv"))
    adapter = Baseball2PitchAdapter(zone, outcome_table)
    pa_stats(adapter.sim_pitch, pitch_algo=rings, swing_algo=middle_swings, sims=200000)

    # # Compare gameplay strategies
    # a_strategy = TeamStrategy(lambda state: random.randint(1, 1024), realistic_take_swing)
    # b_strategy = TeamStrategy(rings, swing)
    # sim_games(16000, a_strategy, b_strategy)

    # count_outcome_table_rates()

