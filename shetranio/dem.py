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
        self.cell_size = int(float(lines[4].split()[1]))
        self.x_coordinates = np.array([self.x_lower_left - self.cell_size + self.cell_size/2 + i * self.cell_size
                                       for i in range(self.number_of_columns + 2)])
        self.y_coordinates = np.flip(np.array([self.y_lower_left - self.cell_size + self.cell_size/2 + i * self.cell_size
                                               for i in range(self.number_of_rows + 2)]), axis=0)

    def get_index(self, x, y):

        x_location = list(self.x_coordinates[np.abs(self.x_coordinates - x) == np.min(np.abs(self.x_coordinates - x))])[0]
        y_location = list(self.y_coordinates[np.abs(self.y_coordinates - y) == np.min(np.abs(self.y_coordinates - y))])[0]

        return int(np.where(self.x_coordinates == x_location)[0]), int(np.where(self.y_coordinates == y_location)[0])
