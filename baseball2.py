import random
import csv

x_size = 32
y_size = 32
size = x_size * y_size

outside_rings = 5

outcomes = {1: "homerun", 2: "triple", 3: "double", 4: "single", 5: "foul", 6: "sacfly", 7: "popout", 8: "groundball", 9: "doubleplay", 10: "strike"}
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

# Parse the CSV file and use it as the outcome table
outcome_table = parse_outcomes_csv("FakeBaseball 2/outcomes.csv")
assert len(outcome_table) % 2 == 1 and len(outcome_table[0]) % 2 == 1

outcome_table_center = (len(outcome_table[0]) // 2, len(outcome_table) // 2)
print(outcome_table_center)

def index_to_position(index):
    assert index > 0 and index <= size
    x = (index - 1) % x_size
    y = (index - 1) // x_size
    return x, y

def position_to_index(position):
    x, y = position
    return (y-1)*x_size + (x)

def is_outside(index):
    x, y = index_to_position(index)
    return x <= outside_rings or x >= x_size - outside_rings or y <= outside_rings or y >= y_size - outside_rings

def get_outcome(pitch, swing):
    pitch_x, pitch_y = index_to_position(pitch)
    swing_x, swing_y = index_to_position(swing)
    
    outcome_table_position = (pitch_x - swing_x + outcome_table_center[0], pitch_y - swing_y + outcome_table_center[1])
    
    if outcome_table_position[0] < 0 or outcome_table_position[0] >= len(outcome_table[0]) or outcome_table_position[1] < 0 or outcome_table_position[1] >= len(outcome_table):
        return 10
    
    return outcome_table[outcome_table_position[1]][outcome_table_position[0]]
    
def sim_pitch(pitch_algo, swing_algo):
    pitch = pitch_algo()
    swing = swing_algo()
    return get_outcome(pitch, swing)

def swing():
    x = random.randint(15, 18)
    y = random.randint(10, 23)
    return position_to_index((x, y))

if __name__ == "__main__":
    num_sims = size * size * 4

    for i in range(num_sims):
        outcome = sim_pitch(lambda: random.randint(1, size), swing)
        outcome_counts[outcome] += 1
    print("Outcome, Count, Percentage")
    for outcome in outcomes:
        print(f"{outcomes[outcome]}, {outcome_counts[outcome]}, {outcome_counts[outcome] / num_sims}")
