import os

class Plan:
    def __init__(self, path):
        self.path = path
        assert os.path.exists(path), 'No such file'
        self.items = []
        with open(self.path) as f:
            for line in f:
                if line == 'item':
                    print(line)
            # self.lines = [line.strip() for line in f.readlines()]