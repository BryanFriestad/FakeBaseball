import csv

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

class Zone:

    def __init__(self, zone_table):
        self.zone_table = zone_table
        self._x_size = len(zone_table[0])
        self._y_size = len(zone_table)
        self.size = self._x_size * self._y_size

    def index_to_position(self, index):
        assert index > 0 and index <= self.size
        x = ((index - 1) % self._x_size) + 1
        y = ((index - 1) // self._x_size) + 1
        return x, y

    def is_outside(self, index):
        """Check if the given index is outside the zone using zone_table."""
        x, y = self.index_to_position(index)

        # Convert to 0-based indices for the zone table
        zone_x = x - 1
        zone_y = y - 1
        
        # Check bounds
        assert zone_x >= 0 and zone_x < self._x_size and zone_y >= 0 and zone_y < self._y_size, f"Invalid zone indices: {zone_x}, {zone_y}"
        
        # Return True if zone value is 0 (outside), False if 1 (inside)
        return self.zone_table[zone_y][zone_x] == 0

    def position_to_index(self, position):
        x, y = position
        return (y-1)*self._x_size + (x)
    
