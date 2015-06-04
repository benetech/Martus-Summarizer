#!/usr/bin/env python
# -*- coding: utf-8 -*-
#******************************************************************************
#*
#* $Id: util.py 3234 2011-10-07 08:31:36Z jeffk $
#*
#* $Revision: 3234 $
#*
#* $Date: 2011-10-07 01:31:36 -0700 (Fri, 07 Oct 2011) $
#*
#*=============================================================================
#*
#*  Human Rights Data Analysis Software Repository
#*  Copyright (C) 2006, Beneficent Technology, Inc. (Benetech).
#*
#*
#*  This program is free software; you can redistribute it and/or modify
#*  it under the terms of the GNU General Public License as published by
#*  the Free Software Foundation; either version 2 of the License, or
#*  (at your option) any later version.
#*
#*  This program is distributed in the hope that it will be useful,
#*  but WITHOUT ANY WARRANTY; without even the implied warranty of
#*  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#*  accompanying Analyzer license for more details on the required
#*  license terms for this software in file "LICENSE.txt".
#*
#*  You should have received a copy of the GNU General Public License
#*  along with this program; if not, write to the Free Software
#*  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#*
#******************************************************************************
#
# $Header$

import string

# ----------------------------------------------------------------------------

# string.whitespace and string.punctuation are all ASCII, so unicode()
# here just converts to a unicode object and doesn't do any decoding.
illegal_chars = unicode(string.whitespace + string.punctuation + '-')
# The rest of the string definitions are done with unicode literals,
# so for the whole of leagilize_field_name, we're operating on
# unicode objects.
illegal_char_replacements = u"_" * len(illegal_chars)
diacritical_chars =             u"áéíóúñÁÉÍÓÚÑ"
diacritical_char_replacements = u"aeiounAEIOUN"

all_target_chars      = illegal_chars             + diacritical_chars
all_replacement_chars = illegal_char_replacements + diacritical_char_replacements

# To use the unicode version of string.translate(), make a mapping from unicode
# ordinals to unicode ordinals.
all_target_ordinals = map(ord, all_target_chars)
translation_table = dict(zip(all_target_ordinals, all_replacement_chars))

def legalize_field_name(untrusted_field_name):
    """ Convert a field name into a legal python identifier that can be
        used in the dot-style attribute lookup way of accessing a record's
        fields.
    
        If the untrusted field name is of type str and contains non-ascii
        characters, it must be encoded in utf-8.
    
        # Whitespace and punctuation and hyphens are replaced by underscores
        >>> legalize_field_name("Date of death")
        'Date_of_death'
        >>> legalize_field_name('No.-of-deaths')
        'No__of_deaths'
        
        # Characters with diacriticals are converted to ascii equivalents
        >>> legalize_field_name("año")
        'ano'
        
        # Unicode characters which we haven't put in the table of ascii
        # translations are turned into underscores.
        >>> legalize_field_name("Rock “and” Röll")
        'Rock__and__R_ll'
        
        # strings starting with a number are prepended with c_
        # (c for column, columna, campo, etc)
        >>> legalize_field_name("1er Apellido")
        'c_1er_Apellido'
    """
    cleaned = unicode(untrusted_field_name.strip())
    assert cleaned != "", "Empty or whitespace only fieldname passed to legalize_field_name()"
    cleaned = cleaned.translate(translation_table)
    
    # Valid identifiers cannot start with a number
    if  cleaned[0] in '0123456789':
        cleaned = 'c_' + cleaned
        
    # Any unicode characters left in the string are not in the
    # translation toble.  Replace them with underscores.
    ok_chars = string.ascii_letters + string.digits + "_"
    cleaned = "".join(char if char in ok_chars else "_" for char in cleaned)
    
    # Should not be any unicode left, so casting to str should not throw an
    # encoding error.  If it does, then we need to expand the translation table
    # to include whatever new interesting characters have turned up in column
    # headers.
    return str(cleaned)

# ----------------------------------------------------------------------------


# ----------------------------------------------------------------------------

class ImmutableError(ValueError):
    """Attempt to modify an immutable attribute/object.""" 

# -------------------------------------------------------

class Dict(dict):
    """Return dict with some of the following extra properties:
       1) key lookups can return a default if key doesn't exist
          (but collections.defaultdict in Python-2.5 has better semantics)
       2) dict can be marked as immutable (can't add keys or modify values)

    >>> def_dict = Dict(make_dict(a=1, b=2), None)
    >>> print def_dict
    {'a': 1, 'b': 2}
    >>> print def_dict['b']
    2
    >>> print def_dict['c']
    None
    >>> print def_dict.keys()
    ['a', 'b']
    >>> def_dict['c'] = 3
    >>> print def_dict.values()
    [1, 3, 2]
    """

    # __slots__ saves memory, and ensures that we set keys in base class
    # these attribute names may be duplicated in class DictRecord
    __slots__ = (     '_default___attr_that_is_HOPEFULLY_not_a_key_',
                 '_is_immutable___attr_that_is_HOPEFULLY_not_a_key_')

    def __init__(self, _dict=None, default=KeyError, is_immutable=False,
                 dict__init__=dict.__init__):
        if  _dict is None:
            _dict = {}
        dict__init__(self, _dict)
        self.     _default___attr_that_is_HOPEFULLY_not_a_key_ = default
        self._is_immutable___attr_that_is_HOPEFULLY_not_a_key_ = is_immutable

    def __getitem__(self, key,
                    dict__getitem__=dict.__getitem__):
        try:
            return  dict__getitem__(self, key)
        except KeyError:
            default = self._default___attr_that_is_HOPEFULLY_not_a_key_
            if default is KeyError:
                raise
            else:
                return default

    def raise_ImmutableError(self, *args):
        raise ImmutableError, "dict %s is immutable" % self
    def __setitem__(self, key, value,
                    dict__setitem__=dict.__setitem__):
        if key in self.__slots__:
            Dict.__setattr__(self, key, value)
        elif self._is_immutable___attr_that_is_HOPEFULLY_not_a_key_:
            self.raise_ImmutableError(self)
        else:
            dict__setitem__(self, key, value)
    def __delitem__(self, key):
        if self._is_immutable___attr_that_is_HOPEFULLY_not_a_key_:
            self.raise_ImmutableError(self)
        else:
            dict.__delitem__(self, key)
    def clear(self):
        if self._is_immutable___attr_that_is_HOPEFULLY_not_a_key_:
            self.raise_ImmutableError(self)
        else:
            dict.clear(self)
    def popitem(self):
        if self._is_immutable___attr_that_is_HOPEFULLY_not_a_key_:
            self.raise_ImmutableError(self)
        else:
            return dict.popitem(self)
    def setdefault(self, key, default=None,
                   dict_setdefault=dict.setdefault):
        if self._is_immutable___attr_that_is_HOPEFULLY_not_a_key_:
            self.raise_ImmutableError(self)
        else:
            return dict_setdefault(self, key, default)
    def update(self, map):
        if self._is_immutable___attr_that_is_HOPEFULLY_not_a_key_:
            self.raise_ImmutableError(self)
        else:
            dict.update(self, map)

# -------------------------------------------------------

# -------------------------------------------------------

class DictRecord(Dict):
    """Return dict that can be accessed using key as attribute, like a record.

    >>> dict_rec = DictRecord(make_dict(a=1, b=2), None)
    >>> print dict_rec
    {'a': 1, 'b': 2}
    >>> print dict_rec.a
    1
    >>> print dict_rec['b']
    2
    >>> print dict_rec.c
    None
    >>> print dict_rec['c']
    None
    >>> print dict_rec.keys()
    ['a', 'b']
    >>> dict_rec.c = 3
    >>> print dict_rec.c
    3
    >>> print dict_rec.values()
    [1, 3, 2]
    """

    # we have no attributes of our own (we store __init__ args in Dict)
    __slots__ = ()

    def __init__(self, _dict=None, default=KeyError, is_immutable=False,
                 filter=filter,
                 dict__dict__keys=dict.__dict__.keys(),
                 Dict__init__=Dict.__init__):
        if  _dict is None:
            _dict = {}
        dup_names = filter( _dict.has_key, dict__dict__keys )
        if dup_names:
            raise ValueError, "dict key(s) %s are builtin dict methods" \
                  % dup_names
        Dict__init__(self, _dict, default, is_immutable)

    # treat attributes the same as keys
    __getattr__ = Dict.__getitem__

    def __setattr__(self, key, value,
                    Dict__setattr__=Dict.__setattr__,
                    dict__setitem__=dict.__setitem__):
        if key in Dict.__slots__:
            Dict__setattr__(self, key, value)
        elif self._is_immutable___attr_that_is_HOPEFULLY_not_a_key_:
            Dict.raise_ImmutableError(self)
        elif key in dict.__dict__:
            raise ValueError, "key '%s' is builtin dict method" % key
        else:
            dict__setitem__(self, key, value)

# -------------------------------------------------------

class DictRecordFastRead(DictRecord):
    """Return dict that can be accessed using key as attribute, like a record.

    >>> dict_rec = DictRecordFastRead( make_dict(a=1, b=2) )
    >>> print dict_rec
    {'a': 1, 'b': 2}
    >>> print dict_rec.a
    1
    >>> print dict_rec['b']
    2
    >>> print dict_rec.keys()
    ['a', 'b']
    >>> dict_rec.c = 3
    >>> print dict_rec.c
    3
    >>> print dict_rec.values()
    [1, 3, 2]
    """

    # we have no attributes of our own (we store __init__ args in DictRecord)
    __slots__ = ()

    def __init__(self, _dict=None, is_immutable=False,
                 DictRecord__init__=DictRecord.__init__):
        if  _dict is None:
            _dict = {}
        DictRecord__init__(self, _dict, is_immutable=is_immutable)

    __getitem__ = dict.__getitem__
    # treat attributes the same as keys
    # first is faster; didn't work in early days, but works w/python-2.[56]
    __getattr__ = dict.__getitem__
   #__getattr__ = Dict.__getitem__

# -------------------------------------------------------



# ----------------------------------------------------------------------------

def tuple_index(tuple_, item):
    return list(tuple_).index(item)

# ----------------------------------------------------------------------------
