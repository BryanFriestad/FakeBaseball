from enum import Enum
from Zone import Zone
import csv

class PitchOutcome(Enum):
    HR = 1
    TRIPLE = 2
    DOUBLE = 3
    SINGLE = 4
    FOUL = 5
    SF = 6
    PO = 7
    GB = 8
    FC = 9
    DP = 10
    STRIKE = 11
    BALL = 12

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

class OutcomeTable:

    def __init__(self, outcome_table):
        self.outcome_table = outcome_table
        assert len(self.outcome_table) % 2 == 1 and len(self.outcome_table[0]) % 2 == 1
        self.outcome_table_center = (len(self.outcome_table[0]) // 2, len(self.outcome_table) // 2)

    def get_outcome(self, zone: Zone, pitch, swing) -> PitchOutcome:
        # Handle taken pitch (swing == -1)
        if swing == -1:
            if zone.is_outside(pitch):
                return PitchOutcome.BALL
            else:
                return PitchOutcome.STRIKE
        
        pitch_x, pitch_y = zone.index_to_position(pitch)
        swing_x, swing_y = zone.index_to_position(swing)
        
        outcome_table_position = (pitch_x - swing_x + self.outcome_table_center[0], pitch_y - swing_y + self.outcome_table_center[1])
        
        if outcome_table_position[0] < 0 or outcome_table_position[0] >= len(self.outcome_table[0]) or \
           outcome_table_position[1] < 0 or outcome_table_position[1] >= len(self.outcome_table):
            return PitchOutcome.STRIKE
        
        return PitchOutcome(self.outcome_table[outcome_table_position[1]][outcome_table_position[0]])
