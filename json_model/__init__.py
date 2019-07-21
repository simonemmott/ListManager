import logging
logger = logging.getLogger(__name__)

def _set_criteria(crit, name, value, criteria):
    if not name:
        raise ValueError(('Invalid syntax in criteria: {crit}'.format(crit=criteria)))
    if len(value) == 0:
        raise ValueError(('Invalid syntax in criteria: {crit}'.format(crit=criteria)))
    try:
        crit[name] = int(value)
    except ValueError:
        try:
            crit[name] = float(value)
        except ValueError:
            if value.lower() == 'true':
                crit[name] = True
            elif value.lower() == 'false':
                crit[name] = False
            else:
                raise ValueError(('Invalid syntax in criteria: {crit}'.format(crit=criteria)))                    

def parse_criteria(criteria):
    crit = {}
    value = ''
    name = None
    quote = None
    expect = None
    for char in criteria:
        logger.debug('name: {name}, value: {value}, expect: {expect}, quote: {quote}, char: {char}'.format(
                name=name,
                value=value,
                expect=expect,
                char=char,
                quote=quote
            ))
        if expect:
            logger.debug('EXPECT')
            if char == expect:
                expect = None
                continue
            raise ValueError(('Invalid syntax in criteria: {crit}'.format(crit=criteria)))
        if quote and char == quote:
            logger.debug('QUOTED and CHAR == QUOTE')
            quote = None
            crit[name] = value
            name = None
            value = ''
            expect = ','
            continue
        if char in ['"',"'"] and not quote:
            logger.debug('CHAR IS QUOTE AND NOT QUOTED')
            if not name:
                raise ValueError(('Invalid syntax in criteria: {crit}'.format(crit=criteria)))
            quote = char
            continue
        if quote:
            logger.debug('QUOTED')
            value = value + char
            continue
        if char == ',':
            logger.debug('COMMA')
            if not name or value == '':
                raise ValueError(('Invalid syntax in criteria: {crit}'.format(crit=criteria)))
            _set_criteria(crit, name, value, criteria)
            name = None
            value = ''
            continue
        if char == '=':
            logger.debug('EQUALS')
            if value == '':
                raise ValueError(('Invalid syntax in criteria: {crit}'.format(crit=criteria)))
            name = value
            value = ''
            continue
        logger.debug('ADD TO VALUE')
        value = value + char
    if quote:
        raise ValueError(('Invalid syntax in criteria: {crit}'.format(crit=criteria)))
    if len(value) > 0 and not name:
        raise ValueError(('Invalid syntax in criteria: {crit}'.format(crit=criteria)))
    if name:
        _set_criteria(crit, name, value, criteria)
    return crit
        

class Expression(object):
    def __init__(self, path):
        if path == None or path == '':
            raise ValueError('You must supply a value for path')
        names = path.split('.')
        self.name = names[0]
        self.criteria = None
        self.index = None
        if '[' in self.name:
            if self.name[-1] != ']':
                raise ValueError('Invalid syntax in path: {path}'.format(path=path))
            criteria = self.name[self.name.index('[')+1:-1]
            self.name = self.name[:self.name.index('[')]
            try:
                self.index = int(criteria)
            except ValueError:
                if '=' not in criteria:
                    self.index = criteria
                else:
                    self.criteria = parse_criteria(criteria)
        self.next = None
        if len(names) > 1:
            self.next = Expression('.'.join(names[1:]))
            
    def evaluate(self, obj):
        if not hasattr(obj, self.name):
            raise AttributeError('The object of type: {type} does not have an attribute: {attr}'.format(
                    type = type(obj),
                    attr = self.name
                ))
        value = getattr(obj, self.name)
        if isinstance(value, EmbeddedManager):
            logger.debug('Value is an EmbeddedManager')
            if self.criteria:
                logger.debug('EmbeddedManager with criteria: {crit}'.format(crit=self.criteria))
                try:
                    value = value.get(**self.criteria)
                except DoesNotExist:
                    value = None
            elif self.index != None:
                logger.debug('EmbeddedManager with index: {idx}'.format(idx=self.index))
                length = len(value)
                if self.index >= length or self.index < -length:
                    value = None
                else:
                    value = value.all()[self.index]
        elif self.criteria:
            if not matches(value, **self.criteria):
                value = None
        if not value:
            return None
        if not self.next:
            return value
        return self.next.evaluate(value)

class F(Expression):
    pass

class DoesNotExist(Exception):
    pass


class EmbeddedIterator(object):
    def __init__(self, data, **kw):
        self.__data = data
        self.__length = None
        self.__criteria = kw
        self.__filtered = None
        
    def is_dict(self):
        return isinstance(self.__data, dict)
        
    def is_list(self):
        return isinstance(self.__data, list)
        
    def __iter__(self):
        self.__index = 0
        return self
    
    def __next__(self):
        if self.__index >= self.__len__():
            raise StopIteration
        if self.is_dict():
            item = list(self.__data)[self.__index]
        else:            
            item = self.__data[self.__index]
        self.__index = self.__index + 1
        if self.__criteria:
            if not matches(item, **self.__criteria):
                item = self.__next__()
        return item
    
    def _apply_filter(self):
        count = 0
        if self.is_dict():
            self.__filtered = {}
            for key, value in self.__data.items():
                if matches(value, **self.__criteria):
                    self.__filtered[key] = value
                    count = count + 1
        else:
            self.__filtered = []
            for item in self.__data:
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
        return len(self.__data)

    def __len__(self):
        self.__length = self.__length if self.__length else self._get_length()
        return self.__length
    
    def __getitem__(self, index):
        if self.is_list():
            if index < 0 or index >= self.__len__():
                raise IndexError('Index [{index}] out of range'.format(index=index))
        if self.__criteria:
            if not self.__filtered:
                self._apply_filter()
            return self.__filtered[index]
        return self.__data[index]
    
    def __contains__(self, item):
        return self._invoke_data_method('__contains__', item)
    
    def _invoke_data_method(self, method, *args, **kw):
        if self.__criteria:
            if not self.__filtered:
                self._apply_filter()
            data = self.__filtered
        else:
            data = self.__data
        return getattr(data, method)(*args, **kw)
        
    
    def keys(self):
        return self._invoke_data_method('keys')
        
    def values(self):
        return self._invoke_data_method('values')
    
    def items(self):
        return self._invoke_data_method('items')
    
    def copy(self):
        return self._invoke_data_method('copy')
    
    def get(self, item=None, **kw):
        if self.__criteria:
            if not self.__filtered:
                self._apply_filter()
            data = self.__filtered
        else:
            data = self.__data   
        if item:
            if self.is_dict():
                value = data.get(item, None)
                if value != None:
                    return value
            else:
                for i in data:
                    if item == i:
                        return i
            raise DoesNotExist('The item: {item} does not exist in the embedded data'.format(item=item))
        else:
            if self.is_dict():
                for key, value in data.items():
                    if matches(value, **kw):
                        return value
            else:
                for i in data:
                    if matches(i, **kw):
                        return i
            raise DoesNotExist('The embedded does not include an item with keys {keys}'.format(
                    keys = kw
                ))
               
    def filter(self, **kw):
        criteria = self.__criteria if self.__criteria else {}
        criteria.update(kw)
        return EmbeddedIterator(self.__data, **criteria)

def matches(item, **kw):
    for key, value in kw.items():
        if isinstance(value, F):
            value = value.evaluate(item)
        if hasattr(item, key):
            if value != getattr(item, key):
                return False
        else:
            raise AttributeError('The object of type: {type} has no attribute {attr}'.format(
                    type = type(item),
                    attr = key
                ))
    return True

class EmbeddedManager(object):
    
    def __init__(self, data=[], **kw):
        self.__data = data
        self.__type = kw.get('type', None)
        self.__length = None
        
    def is_dict(self):
        return isinstance(self.__data, dict)
        
    def is_list(self):
        return isinstance(self.__data, list)
        
    def _get_length(self):
        return len(self.__data)

    def __len__(self):
        self.__length = self.__length if self.__length else self._get_length()
        return self.__length
    
    def __contains__(self, item):
        return self.__data.__contains__(item)
        
    def all(self):
        return EmbeddedIterator(self.__data)
    
    def get(self, item=None, **kw):
        if item:
            if isinstance(self.__data, dict):
                i = self.__data.get(item, None)
                if i != None:
                    return i
                raise DoesNotExist('The item: {item} does not exist in the embedded data'.format(item=item))
            else:
                for i in self.__data:
                    if item == i:
                        return i
                raise DoesNotExist('The item: {item} does not exist in the embedded data'.format(item=item))
        else:
            if isinstance(self.__data, dict):
                for key, value in self.__data.items():
                    if matches(value, **kw):
                        return value
                raise DoesNotExist('The embedded data does not include an item with keys {keys}'.format(
                        keys = kw
                    ))
                
            else:
                for i in self.__data:
                    if matches(i, **kw):
                        return i
                raise DoesNotExist('The embedded data does not include an item with keys {keys}'.format(
                        keys = kw
                    ))
               
    def filter(self, **kw):
        return EmbeddedIterator(self.__data, **kw)
    
    def append(self, item):
        self.__data.append(item)
        if self.__length:
            self.__length = self.__length + 1
        return item
    
    def extend(self, iterable):
        self.__data.extend(iterable)
        if self.__length:
            self.__length = self.__length + len(iterable)
    
    def update(self, dct):
        self.__data.update(dct)
        if self.__length:
            self.__length = None
            self.__length = len(self)
            
    def keys(self):
        return self.__data.keys()
        
    def values(self):
        return self.__data.values()
    
    def items(self):
        return self.__data.items()
        
    def copy(self):
        return self.__data.copy()
        
    def create(self, *args, **kw):
        if not self.__type:
            raise TypeError('No type defined for EmbeddedManager')
        if self.is_list():
            return self.append(self.__type(*args, **kw))
        if self.is_dict():
            if len(args) == 0:
                raise ValueError('You must supply a key value to create a item in a dictionary')
            new = self.__type(*args[1:], **kw)
            self.update({args[0]: new})
            return new
    def set(self, data):
        self.__data = data
        self.__length = None
        
    def clear(self):
        self.__data = []
        self.__length = 0
            
            
            