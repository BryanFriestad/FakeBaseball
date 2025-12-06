import random
import csv
from game_state import GameState, PAOutcome

x_size = 32
y_size = 32
size = x_size * y_size

outcomes = {1: "homerun", 2: "triple", 3: "double", 4: "single", 5: "foul", 6: "sacfly", 7: "popout", 8: "groundball", 9: "fielderschoice", 10: "doubleplay", 11: "strike", 12: "ball"}
outcome_counts = {outcome: 0 for outcome in outcomes}

def parse_outcomes_csv(csv_path):
    """Parse outcomes.csv into the outcomes_table."""
    outcomes_table = []
    with open(csv_path, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            if row:  # Skip empty rows
                # Convert each value to integer
                outcomes_table.append([int(value) for value in row])
    return outcomes_table

def parse_zone_csv(csv_path):
    """Parse zone.csv into a zone table where 1 = inside zone, 0 = outside zone."""
    zone_table = []
    with open(csv_path, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            if row:  # Skip empty rows
                # Convert each value to integer
                zone_table.append([int(value) for value in row])
    return zone_table

# Parse the CSV files and use them
outcome_table = parse_outcomes_csv("FakeBaseball 2/outcomes.csv")
assert len(outcome_table) % 2 == 1 and len(outcome_table[0]) % 2 == 1
outcome_table_center = (len(outcome_table[0]) // 2, len(outcome_table) // 2)

zone_table = parse_zone_csv("FakeBaseball 2/zone.csv")
assert len(zone_table) == x_size and len(zone_table[0]) == y_size

def index_to_position(index):
    assert index > 0 and index <= size
    x = ((index - 1) % x_size) + 1
    y = ((index - 1) // x_size) + 1
    return x, y

def position_to_index(position):
    x, y = position
    return (y-1)*x_size + (x)

def is_outside(index):
    """Check if the given index is outside the zone using zone_table."""
    x, y = index_to_position(index)
    # Convert to 0-based indices for the zone table
    zone_x = x - 1
    zone_y = y - 1
    
    # Check bounds
    assert zone_x >= 0 and zone_x < len(zone_table[0]) and zone_y >= 0 and zone_y < len(zone_table), f"Invalid zone indices: {zone_x}, {zone_y}"
    
    # Return True if zone value is 0 (outside), False if 1 (inside)
    return zone_table[zone_y][zone_x] == 0

def get_outcome(pitch, swing):
    # Handle taken pitch (swing == -1)
    if swing == -1:
        if is_outside(pitch):
            return 12  # ball
        else:
            return 11  # strike
    
    pitch_x, pitch_y = index_to_position(pitch)
    swing_x, swing_y = index_to_position(swing)
    
    outcome_table_position = (pitch_x - swing_x + outcome_table_center[0], pitch_y - swing_y + outcome_table_center[1])
    
    if outcome_table_position[0] < 0 or outcome_table_position[0] >= len(outcome_table[0]) or outcome_table_position[1] < 0 or outcome_table_position[1] >= len(outcome_table):
        return 11
    
    return outcome_table[outcome_table_position[1]][outcome_table_position[0]]
    
def sim_pitch(pitch_algo, swing_algo):
    pitch = pitch_algo()
    swing = swing_algo()
    return get_outcome(pitch, swing)

def adapter_sim_pitch(state: GameState, pitch_algo, swing_algo):
    """
    Adapter function that connects sim_pitch with GameState.
    Takes a GameState object and calls the appropriate method based on the outcome.
    """
    outcome = sim_pitch(pitch_algo, swing_algo)
    
    # Map numeric outcomes to GameState methods
    outcome_mapping = {
        1: state.home_run,
        2: state.triple,
        3: state.double,
        4: state.single,
        5: state.foul,
        6: state.sac_fly,
        7: state.pop_out,
        8: state.ground_ball,
        9: state.fielders_choice,
        10: state.double_play,
        11: state.strike,
        12: state.ball  # taken pitch outside = ball
    }
    
    if outcome in outcome_mapping:
        outcome_mapping[outcome]()
    else:
        raise ValueError(f"Unknown outcome: {outcome}")
    
    return outcome

def sim_plate_appearance(state: GameState, pitch_algo, swing_algo, verbose=False):
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
        
        outcome = adapter_sim_pitch(state, pitch_algo, swing_algo)
        if verbose:
            print(f"Outcome: {outcomes[outcome]}")
        
        # Check if plate appearance ended:
        # - PA count increased (means at-bat completed with hit/out)
        # - Outs increased (means at-bat completed with out)
        # - Balls reset to 0 (means walk occurred)
        # - Strikes reset to 0 (means strikeout occurred)
        # AND it wasn't a foul ball
        if outcome != 5 and (state.pa_count > initial_pa_count or 
                            state.outs > initial_outs or
                            (state.balls < initial_balls) or
                            (state.strikes < initial_strikes)):
            
            # Map numeric outcomes to PAOutcome enum
            outcome_to_paoutcome = {
                1: PAOutcome.HR,
                2: PAOutcome.TRIPLE,
                3: PAOutcome.DOUBLE,
                4: PAOutcome.SINGLE,
                6: PAOutcome.SF,
                7: PAOutcome.PO,
                8: PAOutcome.GB,
                9: PAOutcome.FC,
                10: PAOutcome.DP,
                11: PAOutcome.STRIKEOUT,
                12: PAOutcome.WALK
            }

            if verbose:
                print(f"PAOutcome: {outcome_to_paoutcome[outcome].name}")
            
            return outcome_to_paoutcome[outcome]

def sim_game(pitch_algo=None, swing_algo=None, verbose=False):
    """
    Simulate a full game (9+ innings).
    Uses default algorithms if none provided.
    Ends in the middle of an inning if home team is winning (9th inning or later).
    Continues to extra innings if tied after 9.
    Ends in a tie if still tied after 18 innings.
    """
    if pitch_algo is None:
        pitch_algo = lambda: random.randint(1, size)
    if swing_algo is None:
        swing_algo = swing
    
    state = GameState()
    
    # Sim regular innings
    while state.inning < 10:
        if verbose:
            print(f"Top of {state.inning}")
            print(f"Current score: {state.score}")
        while state.top:
            sim_plate_appearance(state, pitch_algo, swing_algo, verbose)
        if verbose:
            print(f"Bottom of {state.inning}")
            print(f"Current score: {state.score}")
        while not state.top:
            sim_plate_appearance(state, pitch_algo, swing_algo, verbose)
            if state.inning == 9 and state.score[1] > state.score[0]:
                break

    # Sim extra innings
    if state.score[0] == state.score[1]:
        while state.inning <= 18:
            if verbose:
                print(f"Top of {state.inning}")
                print(f"Current score: {state.score}")
            while state.top:
                sim_plate_appearance(state, pitch_algo, swing_algo, verbose)
            if verbose:
                print(f"Bottom of {state.inning}")
                print(f"Current score: {state.score}")
            while not state.top:
                sim_plate_appearance(state, pitch_algo, swing_algo, verbose)
            if state.score[1] > state.score[0]:
                break
        
    # Print game results
    print(f"Plate appearances: {state.pa_count}")
    print(f"Final score: {state.score}")
    print(f"Innings played: {state.inning - 1}")
    
    return state


def sim_games(num_games, pitch_algo=None, swing_algo=None):
    """
    Simulate multiple games and return average runs per team per game.
    """
    if pitch_algo is None:
        pitch_algo = lambda: random.randint(1, size)
    if swing_algo is None:
        swing_algo = swing
    
    total_runs_team1 = 0
    total_runs_team2 = 0
    total_innings_team1 = 0
    total_innings_team2 = 0
    home_wins = 0
    away_wins = 0
    ties = 0
    
    for i in range(num_games):
        state = sim_game(pitch_algo, swing_algo)
        total_runs_team1 += state.score[0]
        total_runs_team2 += state.score[1]
        
        # Track innings played for run normalization
        innings_played = state.inning - 1
        total_innings_team1 += innings_played
        total_innings_team2 += innings_played
        
        # Track wins and ties
        if state.score[0] > state.score[1]:
            away_wins += 1
        elif state.score[1] > state.score[0]:
            home_wins += 1
        else:
            ties += 1
        
        # Print progress every 10 games
        if (i + 1) % 10 == 0:
            print(f"Completed {i + 1}/{num_games} games")
    
    # Calculate runs per 9 innings
    avg_runs_team1_per_9 = (total_runs_team1 / total_innings_team1) * 9 if total_innings_team1 > 0 else 0
    avg_runs_team2_per_9 = (total_runs_team2 / total_innings_team2) * 9 if total_innings_team2 > 0 else 0
    
    # Calculate win rates
    home_win_rate = (home_wins / num_games) * 100
    away_win_rate = (away_wins / num_games) * 100
    tie_rate = (ties / num_games) * 100
    
    print(f"\nResults after {num_games} games:")
    print(f"Average runs per 9 innings - Team 1 (away): {avg_runs_team1_per_9:.2f}")
    print(f"Average runs per 9 innings - Team 2 (home): {avg_runs_team2_per_9:.2f}")
    print(f"Home team win rate: {home_win_rate:.1f}% ({home_wins}/{num_games})")
    print(f"Away team win rate: {away_win_rate:.1f}% ({away_wins}/{num_games})")
    print(f"Tie rate: {tie_rate:.1f}% ({ties}/{num_games})")
    
    return avg_runs_team1_per_9, avg_runs_team2_per_9, home_win_rate, away_win_rate
    

def swing():
    x = random.randint(14, 19)
    y = random.randint(10, 23)
    return position_to_index((x, y))

def player_swing():
    x = input("Swing number?: ")
    return int(x)

if __name__ == "__main__":
    sim_game(pitch_algo=lambda: random.randint(1, size), swing_algo=player_swing, verbose=True)
