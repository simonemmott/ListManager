

class DoesNotExist(Exception):
    pass


class ManagedListIterator(object):
    def __init__(self, gen, **kw):
        self.__gen = gen
        self.__length = None
        self.__criteria = kw
        self.__filtered = None
        
    def __iter__(self):
        self.__index = 0
        return self
    
    def __next__(self):
        if self.__index >= self.__len__():
            raise StopIteration       
        item = self.__gen[self.__index]
        self.__index = self.__index + 1
        if self.__criteria:
            if not matches(item, **self.__criteria):
                item = self.__next__()
        return item
    
    def _apply_filter(self):
        count = 0
        self.__filtered = []
        for item in self.__gen:
            if matches(item, **self.__criteria):
                self.__filtered.append(item)
                count = count + 1
        self.__length = count
        return count
    
    def _get_length(self):
        if self.__criteria:
            if self.__filtered:
                return self.__length
            return self._apply_filter()  
        return len(self.__gen)

    def __len__(self):
        self.__length = self.__length if self.__length else self._get_length()
        return self.__length
    
    def __getitem__(self, index):
        if index < 0 or index >= self.__len__():
            raise IndexError('Index [{index}] out of range'.format(index=index))
        if self.__criteria:
            if not self.__filtered:
                self._apply_filter()
            return self.__filtered[index]
        return self.__gen[index]

def matches(item, **kw):
    for key, value in kw.items():
        if hasattr(item, key):
            if value != getattr(item, key):
                return False
        else:
            raise AttributeError('The object of type: {type} has no attribute {attr}'.format(
                    type = type(item),
                    attr = key
                ))
    return True

class ListManager(object):
    
    def __init__(self, data, **kw):
        self.__data = data
        self.__type = kw.get('type', None)
        self.__length = None
        
    def _get_length(self):
        return len(self.__data)

    def __len__(self):
        self.__length = self.__length if self.__length else self._get_length()
        return self.__length
        
    def all(self):
        return ManagedListIterator(self.__data)
    
    def get(self, item=None, **kw):
        if item:
            for i in self.__data:
                if item == i:
                    return i
            raise DoesNotExist('The item: {item} does not exist in the supplied generator'.format(item=item))
        else:
            for i in self.__data:
                if matches(i, **kw):
                    return i
            raise DoesNotExist('The supplied generator does not include an item with keys {keys}'.format(
                    keys = kw
                ))
               
    def filter(self, **kw):
        return ManagedListIterator(self.__data, **kw)
    
    def append(self, item):
        self.__data.append(item)
        if self.__length:
            self.__length = self.__length + 1
        return item
        
    def create(self, *args, **kw):
        if not self.__type:
            raise TypeError('No type defined for ListManager')
        new = self.__type(*args, **kw)
        return self.append(new)
            
            
            