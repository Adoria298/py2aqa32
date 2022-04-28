class NameLocations(dict): #TODO: make into collections.OrderedDict
    "Stores a Python Name's memory location in this block of memory."
    def __init__(self, max_size, name):
        super().__init__(self)
        self.MAX_SIZE = max_size
        self.name = name # name for this block of memory, e.g. registers

    def __setitem__(self, key, value):
        "Set dictionary item. key is variable name; value is position in memory."
        if key not in self and len(self)+ 1 > self.MAX_SIZE:
            raise KeyError(f"{self.name} is full. Please delete keys.")
        super().__setitem__(key, value)

    def find_first_empty_loc(self): # when OrderedDict we can make this a binary search
        for i in range(self.MAX_SIZE):
            if i not in self.values():
                return i
        #TODO: catch the IndexError and move things to memory.
        raise IndexError(f"{self.name} is full.")
        