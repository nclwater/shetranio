class Dem:
    def __init__(self, path):
        self.path = path
        with open(self.path) as f:
            lines = f.readlines()
        self.number_of_columns = int(lines[0].split()[1])
        self.number_of_rows = int(lines[1].split()[1])
        self.x_lower_left = float(lines[2].split()[1])
        self.y_lower_left = float(lines[3].split()[1])
        self.cell_size = int(lines[4].split()[1])