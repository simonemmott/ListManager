from unittest import TestCase
from json_model import ListManager, DoesNotExist, F, Expression, parse_criteria

class Dummy(object):
    def __init__(self, **kw):
        for key, value in kw.items():
            setattr(self, key, value)
            
            
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
                    objects=ListManager([
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
                    objects=ListManager([
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
                    objects=ListManager([
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
        


class ListManagerTests(TestCase):

    def test_new_instance(self):
        data = ['a', 'b', 'c']
        lm = ListManager(data)
        self.assertIsNotNone(lm)
        
    def test_all_is_an_iterator(self):
        data = ['a', 'b', 'c']
        lm = ListManager(data)
        i=0
        for item in lm.all():
            self.assertEqual(data[i], item)
            i = i + 1
        
    def test_all_is_indexable(self):
        data = ['a', 'b', 'c']
        lm = ListManager(data)
        i=0
        self.assertEqual('a', lm.all()[0])
        self.assertEqual('b', lm.all()[1])
        self.assertEqual('c', lm.all()[2])
        
    def test_get_item(self):
        data = ['a', 'b', 'c']
        lm = ListManager(data)
        self.assertEqual('a', lm.get('a'))
        self.assertEqual('b', lm.get('b'))
        self.assertEqual('c', lm.get('c'))
        with self.assertRaises(DoesNotExist):
            lm.get('z')
        
    def test_get_with_key(self):
        data = [
            Dummy(id=1, name='NAME_1'),
            Dummy(id=2, name='NAME_2'),
            Dummy(id=3, name='NAME_3')
        ]
        lm = ListManager(data)
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
        with self.assertRaises(AttributeError):
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
        lm = ListManager(data)
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
        lm = ListManager(data)
        
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
        
    def test_length(self):
        data = [
            Dummy(id=1, name='NAME_A'),
            Dummy(id=2, name='NAME_A'),
            Dummy(id=3, name='NAME_B'),
            Dummy(id=4, name='NAME_B')
        ]
        lm = ListManager(data)
        self.assertEqual(4, len(lm))
        

    def test_append(self):
        data = [
            Dummy(id=1, name='NAME_A'),
            Dummy(id=2, name='NAME_A'),
            Dummy(id=3, name='NAME_B'),
            Dummy(id=4, name='NAME_B')
        ]
        lm = ListManager(data)
        lm.append(Dummy(id=5, name='NAME_C'))
        self.assertEqual(5, len(lm))
        self.assertEqual(5, lm.get(id=5).id)
        self.assertEqual('NAME_C', lm.get(id=5).name)
        self.assertEqual(1, len(lm.filter(name='NAME_C')))
        self.assertEqual(5, lm.filter(name='NAME_C')[0].id)
        self.assertEqual('NAME_C', lm.filter(name='NAME_C')[0].name)
        
    def test_create_with_no_type(self):
        data = [
            Dummy(id=1, name='NAME_A'),
            Dummy(id=2, name='NAME_A'),
            Dummy(id=3, name='NAME_B'),
            Dummy(id=4, name='NAME_B')
        ]
        lm = ListManager(data)
        with self.assertRaisesRegex(TypeError, 'No type defined for ListManager'):
            lm.create(id=5, name='CREATED')

    def test_create_with_type(self):
        data = [
            Dummy(id=1, name='NAME_A'),
            Dummy(id=2, name='NAME_A'),
            Dummy(id=3, name='NAME_B'),
            Dummy(id=4, name='NAME_B')
        ]
        lm = ListManager(data, type=Dummy)
        created = lm.create(id=5, name='CREATED')
        self.assertIsNotNone(created)
        self.assertTrue(isinstance(created, Dummy))
        self.assertEqual(5, created.id)
        self.assertEqual('CREATED', created.name)
        self.assertEqual(5, len(lm))
        got = lm.get(id=5)
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
        lm = ListManager(data, type=Dummy)
        self.assertEqual(1, len(lm.filter(name='NAME_B').filter(flag='B')))
        self.assertEqual(5, lm.filter(name='NAME_B').filter(flag='B')[0].id)
        self.assertEqual('NAME_B', lm.filter(name='NAME_B').filter(flag='B')[0].name)
        self.assertEqual('B', lm.filter(name='NAME_B').filter(flag='B')[0].flag)
        
    def test_filter_get(self):
        data = [
            Dummy(id=1, name='NAME_A', flag='A'),
            Dummy(id=2, name='NAME_A', flag='B'),
            Dummy(id=3, name='NAME_B', flag='C'),
            Dummy(id=4, name='NAME_B', flag='A'),
            Dummy(id=5, name='NAME_B', flag='B'),
            Dummy(id=6, name='NAME_B', flag='C')
        ]
        lm = ListManager(data, type=Dummy)
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
        lm = ListManager(data, type=Dummy)
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
        lm = ListManager(data, type=Dummy)
        self.assertEqual(3, len(lm.filter(name=F('check'))))
        self.assertEqual(2, lm.filter(name=F('check'))[0].id)
        self.assertEqual(5, lm.filter(name=F('check'))[1].id)
        self.assertEqual(6, lm.filter(name=F('check'))[2].id)
        
        
        
        
        
        
        
        
        