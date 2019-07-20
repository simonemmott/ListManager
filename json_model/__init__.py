

class DoesNotExist(Exception):
    pass


class ManagedListIterator(object):
    def __init__(self, gen):
        self.__gen = gen
        self.__length = None
        
    def __iter__(self):
        self.__index = 0
        return self
    
    def __next__(self):
        if self.__index >= self.__len__():
            raise StopIteration
        item = self.__gen[self.__index]
        self.__index = self.__index + 1
        return item
    
    def _get_length(self):
        return len(self.__gen)

    def __len__(self):
        self.__length = self.__length if self.__length else self._get_length()
        return self.__length
    
    def __getitem__(self, index):
        if index < 0 or index >= self.__len__():
            raise IndexError('Index [{index}] out of range'.format(index=index))
        return self.__gen[index]


class ListManager(object):
    
    def __init__(self, gen):
        self.__gen = gen
        
    def all(self):
        return ManagedListIterator(self.__gen)
    
    def get(self, item=None, **kw):
        if item:
            for i in self.__gen:
                if item == i:
                    return i
            raise DoesNotExist('The item: {item} does not exist in the supplied generator'.format(item=item))
        