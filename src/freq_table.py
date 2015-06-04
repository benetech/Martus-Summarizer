#! /usr/bin/python
# -*- coding: UTF-8 -*-

from __future__ import division

import math

class FrequencyTable(object):
    """Simple frequency table based on a dict"""
       
    def __init__(self, value_sequence=None):
        self.clear()
        if value_sequence:
            self.increment_from_sequence(value_sequence)
    
    def clear(self):
        self.table = dict()
        self.total = 0
    
    def increment(self, value):
        self.total += 1
        if value in self.table:
            self.table[value] += 1
        else:
            self.table[value] = 1
    
    def get_count(self, value):
        """ Returns the number of occurences of value, or 1 if value is not
            in the table."""
        return self.table.get(value, 1)
        
    def get_counts(self):
        """ Returns a sequence of all counts, divorced from their values. """
        return self.table.itervalues()
        
    def get_values(self):
        """ Returns a sequence of all values, divorced from their counts. """
        return self.table.keys()
    
    def get_freq(self, value):
        """ Return the frequency of value, expressed as the fraction of all
            values which are equal to it. """
        return self.get_count(value) / self.total
        
    def get_log_idf(self, value):
        """ Returns the log of the inverse frequency of a term.
            If terms are gleaned from 'documents' with only one or a few
            terms, then this amounts to TF-IDF """
        return math.log( 1 / self.get_freq(value) )
        
    def get_match_prob(self, value):
        """ Returns the complement (1-p) of the probability that two values
            chosen at random match on the given value.  This is sort of like
            the probability that two items having the givin value represent
            the same thing. """
        return 1 - self.get_freq(value)
            
    def increment_from_sequence(self, value_sequence):
        for value in value_sequence:
            self.increment(value)