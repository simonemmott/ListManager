from unittest import TestCase
from json_model import EmbeddedManager, DoesNotExist, F, Expression, parse_criteria
from json_model import Finder
import logging
logger = logging.getLogger(__name__)

class Dummy(object):
    def __init__(self, **kw):
        for key, value in kw.items():
            setattr(self, key, value)
            
    def __eq__(self, *args, **kwargs):
        if len(args) == 0:
            return False
        for attr in dir(self):
            if attr[0] != '_':
                if not hasattr(args[0], attr):
                    return False
                lhs = getattr(args[0], attr)
                rhs = getattr(self, attr)
                if lhs == None and rhs != None:
                    return False
                if rhs == None and lhs != None:
                    return False
                if lhs != rhs:
                    return False
        return True
    
    def __str__(self):
        fields = ''
        for name in dir(self):
            if name[0] == '_':
                continue
            attr = getattr(self, name)
            if callable(attr):
                continue
            if len(fields) == 0:
                fields = '{name}={value}'.format(name=name, value=str(attr))
            else:
                fields = '{fields}, {name}={value}'.format(fields=fields, name=name, value=str(attr))
        return '<{fields}>'.format(fields=fields)
    
    def __repr__(self):
        fields = ''
        for name in dir(self):
            if name[0] == '_':
                continue
            attr = getattr(self, name)
            if callable(attr):
                continue
            if len(fields) == 0:
                fields = '{name}={value}'.format(name=name, value=str(attr))
            else:
                fields = '{fields}, {name}={value}'.format(fields=fields, name=name, value=str(attr))
        return '<{cls}: {fields}>'.format(cls=self.__class__.__name__, fields=fields)
    
class FDummy(Dummy, Finder):
    pass
            
            
class ExpressionTests(TestCase):
    
    def test_parse_criteria(self):
        c = parse_criteria('name=0')
        self.assertEqual(1, len(c))
        self.assertEqual(0, c['name'])
        c = parse_criteria('name=0.1')
        self.assertEqual(1, len(c))
        self.assertEqual(0.1, c['name'])
        c = parse_criteria('name=true')
        self.assertEqual(1, len(c))
        self.assertEqual(True, c['name'])
        c = parse_criteria('name=false')
        self.assertEqual(1, len(c))
        self.assertEqual(False, c['name'])

    def test_parse_criteria_exceptions(self):
        with self.assertRaises(ValueError):
            parse_criteria('name')
        with self.assertRaises(ValueError):
            parse_criteria('name=')
    
    def test_parse_criteria_equals_string(self):
        c = parse_criteria('name="value"')
        self.assertEqual(1, len(c))
        self.assertEqual('value', c['name'])
        c = parse_criteria("name='value'")
        self.assertEqual(1, len(c))
        self.assertEqual('value', c['name'])
        
    def test_parse_compound_criteria(self):
        c = parse_criteria('name=0,value=1')
        self.assertEqual(2, len(c))
        self.assertEqual(0, c['name'])
        self.assertEqual(1, c['value'])
        c = parse_criteria('name=0,value="1"')
        self.assertEqual(2, len(c))
        self.assertEqual(0, c['name'])
        self.assertEqual('1', c['value'])
        
    def test_parse_string_criteria_with_special_characters(self):
        c = parse_criteria('name=",[\'"')
        self.assertEqual(1, len(c))
        self.assertEqual(",['", c['name'])
        
    
    def test_none_expression(self):
        with self.assertRaises(ValueError):
            e = Expression(None)

    def test_blank_expression(self):
        with self.assertRaises(ValueError):
            e = Expression('')
            
    def test_simple_expressions(self):
        e = Expression('name')
        self.assertEqual('name', e.name)
        
    def test_path_expressions(self):
        e = Expression('link.obj.name')
        self.assertEqual('link', e.name)
        self.assertTrue(isinstance(e.next, Expression))
        self.assertEqual('obj', e.next.name)
        self.assertTrue(isinstance(e.next.next, Expression))
        self.assertEqual('name', e.next.next.name)
        
    def test_criteria_expressions(self):
        with self.assertRaises(ValueError):
            e = Expression('link[0')
        e = Expression('link[0]')
        self.assertEqual('link', e.name)
        self.assertEqual(0, e.index)
        self.assertEqual(None, e.criteria)
        e = Expression('link[key]')
        self.assertEqual('link', e.name)
        self.assertEqual('key', e.index)
        self.assertEqual(None, e.criteria)
        e = Expression('link[name="NAME"]')
        self.assertEqual('link', e.name)
        self.assertEqual(None, e.index)
        self.assertTrue('name' in e.criteria)
        self.assertEqual('NAME', e.criteria['name'])
        
        
    def test_evaluate(self): 
        obj = Dummy(id=1, 
                    name='NAME_1', 
                    flag=True, 
                    link=Dummy(id=2, name='NAME_2'),
                    objects=EmbeddedManager([
                            Dummy(id=3, name='NAME_3'),
                            Dummy(id=4, name='NAME_4'),
                            Dummy(id=5, name='NAME_5'),
                        ])
                    )
        e_id = Expression('id')
        e_name = Expression('name')
        e_flag = Expression('flag')
        e_link = Expression('link')
        e_link_id = Expression('link.id')
        e_link_name = Expression('link.name')
        e_objects = Expression('objects')
        
        self.assertEqual(1, e_id.evaluate(obj))
        self.assertEqual('NAME_1', e_name.evaluate(obj))
        self.assertEqual(True, e_flag.evaluate(obj))
        self.assertEqual(2, e_link.evaluate(obj).id)
        self.assertEqual('NAME_2', e_link.evaluate(obj).name)
        self.assertEqual(2, e_link_id.evaluate(obj))
        self.assertEqual('NAME_2', e_link_name.evaluate(obj))
        self.assertEqual(3, e_objects.evaluate(obj).all()[0].id)
        self.assertEqual('NAME_3', e_objects.evaluate(obj).all()[0].name)
        self.assertEqual(4, e_objects.evaluate(obj).all()[1].id)
        self.assertEqual('NAME_4', e_objects.evaluate(obj).all()[1].name)
        self.assertEqual(5, e_objects.evaluate(obj).all()[2].id)
        self.assertEqual('NAME_5', e_objects.evaluate(obj).all()[2].name)
        
    def test_evaluate_with_criteria(self): 
        obj = Dummy(id=1, 
                    name='NAME_1', 
                    flag=True, 
                    link=Dummy(id=2, name='NAME_2'),
                    objects=EmbeddedManager([
                            Dummy(id=3, name='NAME_3'),
                            Dummy(id=4, name='NAME_4'),
                            Dummy(id=5, name='NAME_5'),
                        ])
                    )
        e_link_id_eq_2 = Expression('link[id=2]')
        e_link_id_eq_3 = Expression('link[id=3]')
        self.assertEqual(2, e_link_id_eq_2.evaluate(obj).id)
        self.assertIsNone(e_link_id_eq_3.evaluate(obj))
        e_objects_id_eq_4 = Expression('objects[id=4]')
        self.assertEqual(4, e_objects_id_eq_4.evaluate(obj).id)

    def test_evaluate_with_criteria_1(self): 
        obj = Dummy(id=1, 
                    name='NAME_1', 
                    flag=True, 
                    link=Dummy(id=2, name='NAME_2'),
                    objects=EmbeddedManager([
                            Dummy(id=3, name='NAME_3'),
                            Dummy(id=4, name='NAME_4'),
                            Dummy(id=5, name='NAME_5'),
                        ])
                    )
        e_objects_idx_0 = Expression('objects[0]')
        self.assertEqual('objects', e_objects_idx_0.name)
        self.assertEqual(0, e_objects_idx_0.index)
        self.assertIsNone(e_objects_idx_0.criteria)
        self.assertEqual(3, e_objects_idx_0.evaluate(obj).id)
        

class EmbeddedManagerTests(TestCase):

    def test_new_instance(self):
        data = ['a', 'b', 'c']
        lm = EmbeddedManager(data)
        self.assertIsNotNone(lm)
        
    def test_all_is_an_iterator(self):
        data = ['a', 'b', 'c']
        lm = EmbeddedManager(data)
        i=0
        for item in lm.all():
            self.assertEqual(data[i], item)
            i = i + 1
        
    def test_all_is_indexable(self):
        data = ['a', 'b', 'c']
        lm = EmbeddedManager(data)
        i=0
        self.assertEqual('a', lm.all()[0])
        self.assertEqual('b', lm.all()[1])
        self.assertEqual('c', lm.all()[2])
        
    def test_get_item(self):
        data = ['a', 'b', 'c']
        lm = EmbeddedManager(data)
        self.assertEqual('a', lm.get('a'))
        self.assertEqual('b', lm.get('b'))
        self.assertEqual('c', lm.get('c'))
        with self.assertRaises(DoesNotExist):
            lm.get('z')
        
    def test_get_item_from_dict(self):
        data = {'key1': 'a', 'key2': 'b', 'key3': 'c'}
        lm = EmbeddedManager(data)
        self.assertEqual('a', lm.get('key1'))
        self.assertEqual('b', lm.get('key2'))
        self.assertEqual('c', lm.get('key3'))
        with self.assertRaises(DoesNotExist):
            lm.get('key4')
        
    def test_get_with_key(self):
        data = [
            Dummy(id=1, name='NAME_1'),
            Dummy(id=2, name='NAME_2'),
            Dummy(id=3, name='NAME_3')
        ]
        lm = EmbeddedManager(data)
        self.assertTrue(isinstance(lm.get(id=1), Dummy))
        self.assertEqual(1, lm.get(id=1).id)
        self.assertEqual('NAME_1', lm.get(id=1).name)
        self.assertTrue(isinstance(lm.get(id=2), Dummy))
        self.assertEqual(2, lm.get(id=2).id)
        self.assertEqual('NAME_2', lm.get(id=2).name)
        self.assertTrue(isinstance(lm.get(id=3), Dummy))
        self.assertEqual(3, lm.get(id=3).id)
        self.assertEqual('NAME_3', lm.get(id=3).name)
        with self.assertRaises(DoesNotExist):
            lm.get(id=4)
        with self.assertRaises(DoesNotExist):
            lm.get(xxx=1)
        self.assertTrue(isinstance(lm.get(name='NAME_1'), Dummy))
        self.assertEqual(1, lm.get(name='NAME_1').id)
        self.assertEqual('NAME_1', lm.get(name='NAME_1').name)

    def test_get_with_key_from_dict(self):
        data = {
            'key1': Dummy(id=1, name='NAME_1'),
            'key2': Dummy(id=2, name='NAME_2'),
            'key3': Dummy(id=3, name='NAME_3')
        }
        lm = EmbeddedManager(data)
        self.assertTrue(isinstance(lm.get(id=1), Dummy))
        self.assertEqual(1, lm.get(id=1).id)
        self.assertEqual('NAME_1', lm.get(id=1).name)
        self.assertTrue(isinstance(lm.get(id=2), Dummy))
        self.assertEqual(2, lm.get(id=2).id)
        self.assertEqual('NAME_2', lm.get(id=2).name)
        self.assertTrue(isinstance(lm.get(id=3), Dummy))
        self.assertEqual(3, lm.get(id=3).id)
        self.assertEqual('NAME_3', lm.get(id=3).name)
        with self.assertRaises(DoesNotExist):
            lm.get(id=4)
        with self.assertRaises(DoesNotExist):
            lm.get(xxx=1)
        self.assertTrue(isinstance(lm.get(name='NAME_1'), Dummy))
        self.assertEqual(1, lm.get(name='NAME_1').id)
        self.assertEqual('NAME_1', lm.get(name='NAME_1').name)

    def test_get_with_keys(self):
        data = [
            Dummy(id=1, name='NAME_A'),
            Dummy(id=2, name='NAME_A'),
            Dummy(id=3, name='NAME_B'),
            Dummy(id=4, name='NAME_B')
        ]
        lm = EmbeddedManager(data)
        self.assertTrue(isinstance(lm.get(id=1, name='NAME_A'), Dummy))
        self.assertEqual(1, lm.get(id=1, name='NAME_A').id)
        self.assertEqual('NAME_A', lm.get(id=1, name='NAME_A').name)
        with self.assertRaises(DoesNotExist):
            lm.get(id=3, name='NAME_A')

    def test_get_with_keys_from_dict(self):
        data = {
            'key1': Dummy(id=1, name='NAME_A'),
            'key2': Dummy(id=2, name='NAME_A'),
            'key3': Dummy(id=3, name='NAME_B'),
            'key4': Dummy(id=4, name='NAME_B')
        }
        lm = EmbeddedManager(data)
        self.assertTrue(isinstance(lm.get(id=1, name='NAME_A'), Dummy))
        self.assertEqual(1, lm.get(id=1, name='NAME_A').id)
        self.assertEqual('NAME_A', lm.get(id=1, name='NAME_A').name)
        with self.assertRaises(DoesNotExist):
            lm.get(id=3, name='NAME_A')

    def test_filter_with_keys(self):
        data = [
            Dummy(id=1, name='NAME_A'),
            Dummy(id=2, name='NAME_A'),
            Dummy(id=3, name='NAME_B'),
            Dummy(id=4, name='NAME_B')
        ]
        lm = EmbeddedManager(data)
        
        self.assertEqual(1, len(lm.filter(id=1, name='NAME_A')))
        self.assertTrue(isinstance(lm.filter(id=1, name='NAME_A')[0], Dummy))
        self.assertEqual(1, lm.filter(id=1, name='NAME_A')[0].id)
        self.assertEqual('NAME_A', lm.filter(id=1, name='NAME_A')[0].name)

        self.assertEqual(2, len(lm.filter(name='NAME_A')))
        self.assertTrue(isinstance(lm.filter(name='NAME_A')[0], Dummy))
        self.assertEqual(1, lm.filter(name='NAME_A')[0].id)
        self.assertEqual('NAME_A', lm.filter(name='NAME_A')[0].name)
        self.assertTrue(isinstance(lm.filter(name='NAME_A')[1], Dummy))
        self.assertEqual(2, lm.filter(name='NAME_A')[1].id)
        self.assertEqual('NAME_A', lm.filter(name='NAME_A')[1].name)
        
    def test_filter_with_keys_from_dict(self):
        data = {
            'key1': Dummy(id=1, name='NAME_A'),
            'key2': Dummy(id=2, name='NAME_A'),
            'key3': Dummy(id=3, name='NAME_B'),
            'key4': Dummy(id=4, name='NAME_B')
        }
        lm = EmbeddedManager(data)
        
        self.assertEqual(1, len(lm.filter(id=1, name='NAME_A')))
        self.assertTrue(isinstance(lm.filter(id=1, name='NAME_A')['key1'], Dummy))
        self.assertEqual(1, lm.filter(id=1, name='NAME_A')['key1'].id)
        self.assertEqual('NAME_A', lm.filter(id=1, name='NAME_A')['key1'].name)

        self.assertEqual(2, len(lm.filter(name='NAME_A')))
        self.assertTrue(isinstance(lm.filter(name='NAME_A')['key1'], Dummy))
        self.assertEqual(1, lm.filter(name='NAME_A')['key1'].id)
        self.assertEqual('NAME_A', lm.filter(name='NAME_A')['key1'].name)
        self.assertTrue(isinstance(lm.filter(name='NAME_A')['key2'], Dummy))
        self.assertEqual(2, lm.filter(name='NAME_A')['key2'].id)
        self.assertEqual('NAME_A', lm.filter(name='NAME_A')['key2'].name)
        
    def test_length(self):
        data = [
            Dummy(id=1, name='NAME_A'),
            Dummy(id=2, name='NAME_A'),
            Dummy(id=3, name='NAME_B'),
            Dummy(id=4, name='NAME_B')
        ]
        lm = EmbeddedManager(data)
        self.assertEqual(4, len(lm))
        
    def test_length_of_dict(self):
        data = {
            'key1': Dummy(id=1, name='NAME_A'),
            'key2': Dummy(id=2, name='NAME_A'),
            'key3': Dummy(id=3, name='NAME_B'),
            'key4': Dummy(id=4, name='NAME_B')
        }
        lm = EmbeddedManager(data)
        self.assertEqual(4, len(lm))
        

    def test_append(self):
        data = [
            Dummy(id=1, name='NAME_A'),
            Dummy(id=2, name='NAME_A'),
            Dummy(id=3, name='NAME_B'),
            Dummy(id=4, name='NAME_B')
        ]
        lm = EmbeddedManager(data)
        lm.append(Dummy(id=5, name='NAME_C'))
        self.assertEqual(5, len(lm))
        self.assertEqual(5, lm.get(id=5).id)
        self.assertEqual('NAME_C', lm.get(id=5).name)
        self.assertEqual(1, len(lm.filter(name='NAME_C')))
        self.assertEqual(5, lm.filter(name='NAME_C')[0].id)
        self.assertEqual('NAME_C', lm.filter(name='NAME_C')[0].name)
        
    def test_extend(self):
        data = [
            Dummy(id=1, name='NAME_A'),
            Dummy(id=2, name='NAME_A'),
            Dummy(id=3, name='NAME_B'),
            Dummy(id=4, name='NAME_B')
        ]
        lm = EmbeddedManager(data)
        lm.extend([
            Dummy(id=5, name='NAME_C'),
            Dummy(id=6, name='NAME_C'),
            ])
        self.assertEqual(6, len(lm))
        self.assertEqual(5, lm.get(id=5).id)
        self.assertEqual('NAME_C', lm.get(id=5).name)
        self.assertEqual(6, lm.get(id=6).id)
        self.assertEqual('NAME_C', lm.get(id=6).name)
        self.assertEqual(2, len(lm.filter(name='NAME_C')))
        self.assertEqual(5, lm.filter(name='NAME_C')[0].id)
        self.assertEqual('NAME_C', lm.filter(name='NAME_C')[0].name)
        self.assertEqual(6, lm.filter(name='NAME_C')[1].id)
        self.assertEqual('NAME_C', lm.filter(name='NAME_C')[1].name)
        
    def test_update(self):
        data = {
            'key1': Dummy(id=1, name='NAME_A'),
            'key2': Dummy(id=2, name='NAME_A'),
            'key3': Dummy(id=3, name='NAME_B'),
            'key4': Dummy(id=4, name='NAME_B')
        }
        lm = EmbeddedManager(data)
        lm.update({
            'key4': Dummy(id=5, name='NAME_C'),
            'key5': Dummy(id=6, name='NAME_C'),
            })
        self.assertEqual(5, len(lm))
        self.assertEqual(5, lm.get('key4').id)
        self.assertEqual('NAME_C', lm.get('key4').name)
        self.assertEqual(6, lm.get(id=6).id)
        self.assertEqual('NAME_C', lm.get('key5').name)
        self.assertEqual(2, len(lm.filter(name='NAME_C')))
        self.assertEqual(5, lm.filter(name='NAME_C')['key4'].id)
        self.assertEqual('NAME_C', lm.filter(name='NAME_C')['key4'].name)
        self.assertEqual(6, lm.filter(name='NAME_C')['key5'].id)
        self.assertEqual('NAME_C', lm.filter(name='NAME_C')['key5'].name)
        
    def test_keys(self):
        data = {
            'key1': Dummy(id=1, name='NAME_A'),
            'key2': Dummy(id=2, name='NAME_A'),
            'key3': Dummy(id=3, name='NAME_B'),
            'key4': Dummy(id=4, name='NAME_B')
        }
        lm = EmbeddedManager(data)
        self.assertTrue('key1' in lm.keys())
        self.assertTrue('key2' in lm.keys())
        self.assertTrue('key3' in lm.keys())
        self.assertTrue('key4' in lm.keys())
        self.assertEqual(4, len(lm.keys()))
        
    def test_values(self):
        data = {
            'key1': Dummy(id=1, name='NAME_A'),
            'key2': Dummy(id=2, name='NAME_A'),
            'key3': Dummy(id=3, name='NAME_B'),
            'key4': Dummy(id=4, name='NAME_B')
        }
        lm = EmbeddedManager(data)
        self.assertTrue(data['key1'] in lm.values())
        self.assertTrue(data['key2'] in lm.values())
        self.assertTrue(Dummy(id=3, name='NAME_B') in lm.values())
        self.assertTrue(Dummy(id=4, name='NAME_B') in lm.values())
        self.assertEqual(4, len(lm.values()))
        
    def test_items(self):
        data = {
            'key1': Dummy(id=1, name='NAME_A'),
            'key2': Dummy(id=2, name='NAME_A'),
            'key3': Dummy(id=3, name='NAME_B'),
            'key4': Dummy(id=4, name='NAME_B')
        }
        lm = EmbeddedManager(data)
        for key, value in lm.items():
            self.assertEqual(data[key], value)
        
    def test_copy_with_dict(self):
        data = {
            'key1': Dummy(id=1, name='NAME_A'),
            'key2': Dummy(id=2, name='NAME_A'),
            'key3': Dummy(id=3, name='NAME_B'),
            'key4': Dummy(id=4, name='NAME_B')
        }
        lm = EmbeddedManager(data)
        self.assertEqual(data, lm.copy())
        
    def test_copy_with_list(self):
        data = [
            Dummy(id=1, name='NAME_A'),
            Dummy(id=2, name='NAME_A'),
            Dummy(id=3, name='NAME_B'),
            Dummy(id=4, name='NAME_B')
        ]
        lm = EmbeddedManager(data)
        self.assertEqual(data, lm.copy())

    def test_create_with_no_type(self):
        data = [
            Dummy(id=1, name='NAME_A'),
            Dummy(id=2, name='NAME_A'),
            Dummy(id=3, name='NAME_B'),
            Dummy(id=4, name='NAME_B')
        ]
        lm = EmbeddedManager(data)
        with self.assertRaisesRegex(TypeError, 'No type defined for EmbeddedManager'):
            lm.create(id=5, name='CREATED')

    def test_in_filtered_list(self):
        data = [
            Dummy(id=1, name='NAME_A'),
            Dummy(id=2, name='NAME_A'),
            Dummy(id=3, name='NAME_B'),
            Dummy(id=4, name='NAME_B')
        ]
        lm = EmbeddedManager(data)
        self.assertTrue(Dummy(id=3, name='NAME_B') in lm.filter(name='NAME_B'))
        self.assertTrue(Dummy(id=4, name='NAME_B') in lm.filter(name='NAME_B'))

    def test_in_filtered_dict(self):
        data = {
            'key1': Dummy(id=1, name='NAME_A'),
            'key2': Dummy(id=2, name='NAME_A'),
            'key3': Dummy(id=3, name='NAME_B'),
            'key4': Dummy(id=4, name='NAME_B')
        }
        lm = EmbeddedManager(data)
        self.assertEqual(2, len(lm.filter(name='NAME_B')))
        self.assertTrue('key3' in lm.filter(name='NAME_B'))
        self.assertTrue('key4' in lm.filter(name='NAME_B'))

    def test_keys_in_filtered_dict(self):
        data = {
            'key1': Dummy(id=1, name='NAME_A'),
            'key2': Dummy(id=2, name='NAME_A'),
            'key3': Dummy(id=3, name='NAME_B'),
            'key4': Dummy(id=4, name='NAME_B')
        }
        lm = EmbeddedManager(data)
        self.assertEqual(2, len(lm.filter(name='NAME_B').keys()))
        self.assertTrue('key3' in lm.filter(name='NAME_B').keys())
        self.assertTrue('key4' in lm.filter(name='NAME_B').keys())

    def test_values_in_filtered_dict(self):
        data = {
            'key1': Dummy(id=1, name='NAME_A'),
            'key2': Dummy(id=2, name='NAME_A'),
            'key3': Dummy(id=3, name='NAME_B'),
            'key4': Dummy(id=4, name='NAME_B')
        }
        lm = EmbeddedManager(data)
        self.assertEqual(2, len(lm.filter(name='NAME_B').values()))
        self.assertTrue(Dummy(id=3, name='NAME_B') in lm.filter(name='NAME_B').values())
        self.assertTrue(Dummy(id=4, name='NAME_B') in lm.filter(name='NAME_B').values())

    def test_items_in_filtered_dict(self):
        data = {
            'key1': Dummy(id=1, name='NAME_A'),
            'key2': Dummy(id=2, name='NAME_A'),
            'key3': Dummy(id=3, name='NAME_B'),
            'key4': Dummy(id=4, name='NAME_B')
        }
        lm = EmbeddedManager(data)
        self.assertEqual(2, len(lm.filter(name='NAME_B').items()))
        self.assertTrue(('key3', Dummy(id=3, name='NAME_B')) in lm.filter(name='NAME_B').items())
        self.assertTrue(('key4', Dummy(id=4, name='NAME_B')) in lm.filter(name='NAME_B').items())

    def test_copy_with_filtered_list(self):
        data = [
            Dummy(id=1, name='NAME_A'),
            Dummy(id=2, name='NAME_A'),
            Dummy(id=3, name='NAME_B'),
            Dummy(id=4, name='NAME_B')
        ]
        lm = EmbeddedManager(data, type=Dummy)
        self.assertEqual([
                Dummy(id=3, name='NAME_B'),
                Dummy(id=4, name='NAME_B')
            ],
            lm.filter(name='NAME_B').copy()
        )

    def test_copy_with_filtered_dict(self):
        data = {
            'key1': Dummy(id=1, name='NAME_A'),
            'key2': Dummy(id=2, name='NAME_A'),
            'key3': Dummy(id=3, name='NAME_B'),
            'key4': Dummy(id=4, name='NAME_B')
        }
        lm = EmbeddedManager(data, type=Dummy)
        self.assertEqual({
                'key3': Dummy(id=3, name='NAME_B'),
                'key4': Dummy(id=4, name='NAME_B')
            }
            ,
            lm.filter(name='NAME_B').copy()
        )

    def test_create_with_type(self):
        data = [
            Dummy(id=1, name='NAME_A'),
            Dummy(id=2, name='NAME_A'),
            Dummy(id=3, name='NAME_B'),
            Dummy(id=4, name='NAME_B')
        ]
        lm = EmbeddedManager(data, type=Dummy)
        created = lm.create(id=5, name='CREATED')
        self.assertIsNotNone(created)
        self.assertTrue(isinstance(created, Dummy))
        self.assertEqual(5, created.id)
        self.assertEqual('CREATED', created.name)
        self.assertEqual(5, len(lm))
        got = lm.get(id=5)
        self.assertEqual(5, got.id)
        self.assertEqual('CREATED', got.name)

    def test_create_with_no_key_in_dict_with_type(self):
        data = {
            'key1': Dummy(id=1, name='NAME_A'),
            'key2': Dummy(id=2, name='NAME_A'),
            'key3': Dummy(id=3, name='NAME_B'),
            'key4': Dummy(id=4, name='NAME_B')
        }
        lm = EmbeddedManager(data, type=Dummy)
        with self.assertRaises(ValueError):
            created = lm.create(id=5, name='CREATED')

    def test_create_with_key_in_dict_with_type(self):
        data = {
            'key1': Dummy(id=1, name='NAME_A'),
            'key2': Dummy(id=2, name='NAME_A'),
            'key3': Dummy(id=3, name='NAME_B'),
            'key4': Dummy(id=4, name='NAME_B')
        }
        lm = EmbeddedManager(data, type=Dummy)
        created = lm.create('key5', id=5, name='CREATED')
        self.assertIsNotNone(created)
        self.assertTrue(isinstance(created, Dummy))
        self.assertEqual(5, created.id)
        self.assertEqual('CREATED', created.name)
        self.assertEqual(5, len(lm))
        got = lm.get('key5')
        self.assertEqual(5, got.id)
        self.assertEqual('CREATED', got.name)

    def test_chained_filter(self):
        data = [
            Dummy(id=1, name='NAME_A', flag='A'),
            Dummy(id=2, name='NAME_A', flag='B'),
            Dummy(id=3, name='NAME_B', flag='C'),
            Dummy(id=4, name='NAME_B', flag='A'),
            Dummy(id=5, name='NAME_B', flag='B'),
            Dummy(id=6, name='NAME_B', flag='C')
        ]
        lm = EmbeddedManager(data, type=Dummy)
        self.assertEqual(1, len(lm.filter(name='NAME_B').filter(flag='B')))
        self.assertEqual(5, lm.filter(name='NAME_B').filter(flag='B')[0].id)
        self.assertEqual('NAME_B', lm.filter(name='NAME_B').filter(flag='B')[0].name)
        self.assertEqual('B', lm.filter(name='NAME_B').filter(flag='B')[0].flag)
        
    def test_chained_filter_with_dict(self):
        data = {
            'key1': Dummy(id=1, name='NAME_A', flag='A'),
            'key2': Dummy(id=2, name='NAME_A', flag='B'),
            'key3': Dummy(id=3, name='NAME_B', flag='C'),
            'key4': Dummy(id=4, name='NAME_B', flag='A'),
            'key5': Dummy(id=5, name='NAME_B', flag='B'),
            'key6': Dummy(id=6, name='NAME_B', flag='C')
        }
        lm = EmbeddedManager(data, type=Dummy)
        self.assertEqual(1, len(lm.filter(name='NAME_B').filter(flag='B')))
        self.assertEqual(5, lm.filter(name='NAME_B').filter(flag='B')['key5'].id)
        self.assertEqual('NAME_B', lm.filter(name='NAME_B').filter(flag='B')['key5'].name)
        self.assertEqual('B', lm.filter(name='NAME_B').filter(flag='B')['key5'].flag)
        
    def test_filter_get(self):
        data = [
            Dummy(id=1, name='NAME_A', flag='A'),
            Dummy(id=2, name='NAME_A', flag='B'),
            Dummy(id=3, name='NAME_B', flag='C'),
            Dummy(id=4, name='NAME_B', flag='A'),
            Dummy(id=5, name='NAME_B', flag='B'),
            Dummy(id=6, name='NAME_B', flag='C')
        ]
        lm = EmbeddedManager(data, type=Dummy)
        self.assertEqual(5, lm.filter(name='NAME_B').get(flag='B').id)
        self.assertEqual('NAME_B', lm.filter(name='NAME_B').get(flag='B').name)
        self.assertEqual('B', lm.filter(name='NAME_B').get(flag='B').flag)
        with self.assertRaises(DoesNotExist):
            lm.filter(name='NAME_A').get(flag='C')
        
    def test_filter_get_with_dict(self):
        data = {
            'key1': Dummy(id=1, name='NAME_A', flag='A'),
            'key2': Dummy(id=2, name='NAME_A', flag='B'),
            'key3': Dummy(id=3, name='NAME_B', flag='C'),
            'key4': Dummy(id=4, name='NAME_B', flag='A'),
            'key5': Dummy(id=5, name='NAME_B', flag='B'),
            'key6': Dummy(id=6, name='NAME_B', flag='C')
        }
        lm = EmbeddedManager(data, type=Dummy)
        self.assertEqual(5, lm.filter(name='NAME_B').get(flag='B').id)
        self.assertEqual('NAME_B', lm.filter(name='NAME_B').get(flag='B').name)
        self.assertEqual('B', lm.filter(name='NAME_B').get(flag='B').flag)
        with self.assertRaises(DoesNotExist):
            lm.filter(name='NAME_A').get(flag='C')
        
    def test_get_with_field(self):
        data = [
            Dummy(id=1, name='NAME_A', check='NAME_X'),
            Dummy(id=2, name='NAME_A', check='NAME_A'),
            Dummy(id=3, name='NAME_B', check='NAME_X'),
            Dummy(id=4, name='NAME_B', check='NAME_X'),
            Dummy(id=5, name='NAME_B', check='NAME_B'),
            Dummy(id=6, name='NAME_B', check='NAME_B')
        ]
        lm = EmbeddedManager(data, type=Dummy)
        self.assertEqual(2, lm.get(name=F('check')).id)
        
    def test_get_from_dict_with_field(self):
        data = {
            'key1': Dummy(id=1, name='NAME_A', check='NAME_X'),
            'key2': Dummy(id=2, name='NAME_A', check='NAME_A'),
            'key3': Dummy(id=3, name='NAME_B', check='NAME_X'),
            'key4': Dummy(id=4, name='NAME_B', check='NAME_X'),
            'key5': Dummy(id=5, name='NAME_B', check='NAME_B'),
            'key6': Dummy(id=6, name='NAME_B', check='NAME_B')
        }
        lm = EmbeddedManager(data, type=Dummy)
        self.assertEqual(2, lm.get(name=F('check')).id)
        
    def test_filter_with_field(self):
        data = [
            Dummy(id=1, name='NAME_A', check='NAME_X'),
            Dummy(id=2, name='NAME_A', check='NAME_A'),
            Dummy(id=3, name='NAME_B', check='NAME_X'),
            Dummy(id=4, name='NAME_B', check='NAME_X'),
            Dummy(id=5, name='NAME_B', check='NAME_B'),
            Dummy(id=6, name='NAME_B', check='NAME_B')
        ]
        lm = EmbeddedManager(data, type=Dummy)
        self.assertEqual(3, len(lm.filter(name=F('check'))))
        self.assertEqual(2, lm.filter(name=F('check'))[0].id)
        self.assertEqual(5, lm.filter(name=F('check'))[1].id)
        self.assertEqual(6, lm.filter(name=F('check'))[2].id)
        
    def test_filter_dict_with_field(self):
        data = {
            'key1': Dummy(id=1, name='NAME_A', check='NAME_X'),
            'key2': Dummy(id=2, name='NAME_A', check='NAME_A'),
            'key3': Dummy(id=3, name='NAME_B', check='NAME_X'),
            'key4': Dummy(id=4, name='NAME_B', check='NAME_X'),
            'key5': Dummy(id=5, name='NAME_B', check='NAME_B'),
            'key6': Dummy(id=6, name='NAME_B', check='NAME_B')
        }
        lm = EmbeddedManager(data, type=Dummy)
        self.assertEqual(3, len(lm.filter(name=F('check'))))
        self.assertEqual(2, lm.filter(name=F('check'))['key2'].id)
        self.assertEqual(5, lm.filter(name=F('check'))['key5'].id)
        self.assertEqual(6, lm.filter(name=F('check'))['key6'].id)
        
    def test_set(self):
        data = [
            Dummy(id=1, name='NAME_A', check='NAME_X'),
            Dummy(id=2, name='NAME_A', check='NAME_A'),
            Dummy(id=3, name='NAME_B', check='NAME_X'),
            Dummy(id=4, name='NAME_B', check='NAME_X'),
            Dummy(id=5, name='NAME_B', check='NAME_B'),
            Dummy(id=6, name='NAME_B', check='NAME_B')
        ]
        lm = EmbeddedManager(type=Dummy)
        self.assertEqual(0, len(lm))
        lm.set(data)
        self.assertEqual(6, len(lm))
        self.assertEqual(2, lm.filter(name=F('check'))[0].id)
        self.assertEqual(5, lm.filter(name=F('check'))[1].id)
        self.assertEqual(6, lm.filter(name=F('check'))[2].id)
        
    def test_clear(self):
        data = [
            Dummy(id=1, name='NAME_A', check='NAME_X'),
            Dummy(id=2, name='NAME_A', check='NAME_A'),
            Dummy(id=3, name='NAME_B', check='NAME_X'),
            Dummy(id=4, name='NAME_B', check='NAME_X'),
            Dummy(id=5, name='NAME_B', check='NAME_B'),
            Dummy(id=6, name='NAME_B', check='NAME_B')
        ]
        lm = EmbeddedManager(data, type=Dummy)
        self.assertEqual(6, len(lm))
        lm.clear()
        self.assertEqual(0, len(lm))
        
        
class FinderTests(TestCase):
    
    def test_mixin_adds_find_method(self):
        test = FDummy(id=1, name='NAME')
        self.assertTrue(hasattr(test, '__find__'))
        self.assertTrue(callable(test.__find__))
        
    def test_find_embedded_list_names(self):
        test = FDummy(
            id=1, 
            name='NAME_1',
            embedded = EmbeddedManager([
                    FDummy(id=2, name='NAME_2'),
                    FDummy(id=3, name='NAME_3'),
                    FDummy(id=4, name='NAME_4'),
                ]))
        result = test.__find__('embedded.name')
        self.assertEqual(3, len(result))
        self.assertTrue('NAME_2' in result)
        self.assertTrue('NAME_3' in result)
        self.assertTrue('NAME_4' in result)
        
    def test_find_embedded_dict_names(self):
        test = FDummy(
            id=1, 
            name='NAME_1',
            embedded = EmbeddedManager({
                    'key1': FDummy(id=2, name='NAME_2'),
                    'key2': FDummy(id=3, name='NAME_3'),
                    'key3': FDummy(id=4, name='NAME_4'),
                }))
        result = test.__find__('embedded.name')
        self.assertEqual(3, len(result))
        self.assertTrue('NAME_2' in result)
        self.assertTrue('NAME_3' in result)
        self.assertTrue('NAME_4' in result)
        
    def test_find_filtered_embedded_list_names(self):
        test = FDummy(
            id=1, 
            name='NAME_1',
            embedded = EmbeddedManager([
                    FDummy(id=2, name='NAME_2'),
                    FDummy(id=3, name='NAME_3'),
                    FDummy(id=4, name='NAME_4'),
                ]))
        result = test.__find__('embedded[id=3].name')
        self.assertEqual(1, len(result))
        self.assertTrue('NAME_3' in result)
        result = test.__find__('embedded[id=5].name')
        self.assertEqual(0, len(result))
        result = test.__find__('embedded[2].name')
        self.assertEqual(1, len(result))
        self.assertTrue('NAME_4' in result)
        result = test.__find__('embedded[3].name')
        self.assertEqual(0, len(result))
        
    def test_find_filtered_embedded_dict_names(self):
        test = FDummy(
            id=1, 
            name='NAME_1',
            embedded = EmbeddedManager({
                    'key1': FDummy(id=2, name='NAME_2'),
                    'key2': FDummy(id=3, name='NAME_3'),
                    'key3': FDummy(id=4, name='NAME_4'),
                }))
        result = test.__find__('embedded[id=3].name')
        self.assertEqual(1, len(result))
        self.assertTrue('NAME_3' in result)
        result = test.__find__('embedded[id=5].name')
        self.assertEqual(0, len(result))
        result = test.__find__('embedded[key3].name')
        self.assertEqual(1, len(result))
        self.assertTrue('NAME_4' in result)
        result = test.__find__('embedded[key4].name')
        self.assertEqual(0, len(result))
        
    def test_find_filtered_embedded_link_name(self):
        test = FDummy(
            id=1, 
            name='NAME_1',
            link=FDummy(id=5, name='NAME_5'),
            embedded = EmbeddedManager([
                    FDummy(id=2, name='NAME_2'),
                    FDummy(id=3, name='NAME_3'),
                    FDummy(id=4, name='NAME_4'),
                ]))
        result = test.__find__('link.name')
        self.assertEqual(1, len(result))
        self.assertTrue('NAME_5' in result)
        result = test.__find__('link[id=5].name')
        self.assertEqual(1, len(result))
        self.assertTrue('NAME_5' in result)
        result = test.__find__('link[id=6].name')
        self.assertEqual(0, len(result))
        
    def test_find_filtered_embedded_wildcard_name(self):
        test = FDummy(
            id=1, 
            name='NAME_1',
            link=FDummy(id=5, name='NAME_5'),
            embedded = EmbeddedManager([
                    FDummy(id=2, name='NAME_2'),
                    FDummy(id=3, name='NAME_3'),
                    FDummy(id=4, name='NAME_4'),
                ]))
        result = test.__find__('*.name')
        self.assertEqual(4, len(result))
        self.assertTrue('NAME_5' in result)
        result = test.__find__('*[id=5].name')
        self.assertEqual(1, len(result))
        self.assertTrue('NAME_5' in result)
        result = test.__find__('*[id=6].name')
        self.assertEqual(0, len(result))
        
    def test_find_filtered_embedded_open_search_name(self):
        test = FDummy(
            id=1, 
            name='NAME_1',
            link=FDummy(id=5, name='NAME_5'),
            embedded = EmbeddedManager([
                    FDummy(
                        id=2, 
                        name='NAME_2',
                        sub=EmbeddedManager([
                            FDummy(id=1, name='NAME_1_1'),
                            FDummy(id=2, name='NAME_1_2'),
                            FDummy(id=3, name='NAME_1_3')
                        ])
                    ),
                    FDummy(
                        id=3, 
                        name='NAME_3',
                        sub=EmbeddedManager([
                            FDummy(id=1, name='NAME_2_1'),
                            FDummy(id=2, name='NAME_2_2'),
                            FDummy(id=3, name='NAME_2_3')
                        ])
                    ),
                    FDummy(
                        id=4, 
                        name='NAME_4',
                        sub=EmbeddedManager([
                            FDummy(id=1, name='NAME_3_1'),
                            FDummy(id=2, name='NAME_3_2'),
                            FDummy(id=3, name='NAME_3_3')
                        ])
                    )
                ]))
        with self.assertRaises(ValueError):
            result = test.__find__('**')
        result = test.__find__('**.name')
        self.assertEqual(13, len(result))
        self.assertTrue('NAME_5' in result)
        self.assertTrue('NAME_2' in result)
        self.assertTrue('NAME_1_1' in result)
        self.assertTrue('NAME_1_2' in result)
        self.assertTrue('NAME_1_3' in result)
        self.assertTrue('NAME_3' in result)
        self.assertTrue('NAME_2_1' in result)
        self.assertTrue('NAME_2_2' in result)
        self.assertTrue('NAME_2_3' in result)
        self.assertTrue('NAME_4' in result)
        self.assertTrue('NAME_3_1' in result)
        self.assertTrue('NAME_3_2' in result)
        self.assertTrue('NAME_3_3' in result)
        result = test.__find__('**[id=3].name')
        self.assertEqual(2, len(result))
        self.assertTrue('NAME_3' in result)
        self.assertTrue('NAME_2_3' in result)
        result = test.__find__('**[id=6].name')
        self.assertEqual(0, len(result))
        result = test.__find__('embedded.sub[id=3].name')
        self.assertEqual(3, len(result))
        self.assertTrue('NAME_1_3' in result)
        self.assertTrue('NAME_2_3' in result)
        self.assertTrue('NAME_3_3' in result)
        result = test.__find__('embedded.sub[id=3,name="NAME_2_3"].name')
        self.assertEqual(1, len(result))
        self.assertTrue('NAME_2_3' in result)
        
        
        
        