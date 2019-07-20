

class ManagedListIterator(object):
    def __init__(self, gen):
        self.__gen = gen
        self.__length = len(gen)
        if self.__length is None:
            raise TypeError('The supplied generator {gen} has no len()'.format(gen=gen))
        
    def __iter__(self):
        self.__index = 0
        return self
    
    def __next__(self):
        if self.__index >= self.__length:
            raise StopIteration
        item = self.__gen[self.__index]
        self.__index = self.__index + 1
        return item

    def __len__(self):
        return self.__length
    
    def __getitem__(self, index):
        if index < 0 or index >= self.__length:
            raise IndexError('Index [{index}] out of range'.format(index=index))
        return self.__gen[index]


class ListManager(object):
    
    def __init__(self, data):
        self._data = data
        
    def all(self):
        return ManagedListIterator(self._data)