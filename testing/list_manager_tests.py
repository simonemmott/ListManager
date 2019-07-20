from unittest import TestCase
from json_model import ListManager, DoesNotExist

class Dummy(object):
    def __init__(self, **kw):
        for key, value in kw.items():
            setattr(self, key, value)

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


        