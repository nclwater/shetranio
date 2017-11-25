import numpy as np

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
        self.x_coordinates = np.array([self.x_lower_left + i * self.cell_size for i in range(self.number_of_columns)])
        self.y_coordinates = np.array([self.y_lower_left + i * self.cell_size for i in range(self.number_of_rows)])

    def get_index(self, x, y):
        x_location = self.x_coordinates[np.abs(self.x_coordinates - x) == np.min(np.abs(self.x_coordinates - x))]
        y_location = self.y_coordinates[np.abs(self.y_coordinates - y) == np.min(np.abs(self.y_coordinates - y))]

        return int(np.where(self.x_coordinates == x_location)[0]), int(np.where(self.y_coordinates == y_location)[0])
