from unittest import TestCase
from json_model import ListManager

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
        