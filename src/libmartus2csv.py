#!/usr/bin/env python
# -*- coding: utf-8 -*-
#******************************************************************************
#*
#* $Id: libmartus2csv.py 3547 2012-07-10 15:24:11Z jeffk $
#*
#* $Revision: 3547 $
#*
#* $Date: 2012-07-10 08:24:11 -0700 (Tue, 10 Jul 2012) $
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


import sys, re
import logging as logsys

from util import legalize_field_name

logging = logsys.getLogger( )
boolean_type = intern('BOOLEAN')

# ----------------------------------------------------------------------------

def intern_(value,                      # only argument you should pass
            value2interned_value={},
            str=str,
            intern=intern):

    return value2interned_value.setdefault( value,
                                            intern( str(value).strip() ) )

def message_as_name(message,            # only argument you should pass
                    message2name={},
                    dashes=re.compile(r'__+'),
                    intern=intern,
                    legalize_field_name=legalize_field_name):
    name = message2name.get(message)
    if name is not None:
        return name

    if  message:
        message = message.replace('&#160', ' ') # lxml.etree parser does this
        # This next line can result in an empty string if the message is
        # nothing but unicode, and thus is legalized as nothing but underscores.
        name = legalize_field_name(message).strip('_')
        if '__' in name:
            name = dashes.sub('_', name)
    else:
        name = message
    name = intern(name)
    message2name[message] = name
    return name

def cleaned_value(value):
    return value.strip().replace('|', '~').replace('&#160', ' ').replace('\n', '\\n')


##
# Column structure
#
#  Holds information about a set of columns for csv output
##

main_table_name = intern('_main_')

class Columns(object):
    __slots__ = ('_do_legalize_names', '_logging', '_do_allow_dup_tags',
                 'table_name', 'line_number', '_name2index',
                 'names', 'messages', 'types',
                 'last_dup_name', 'have_non_booleans',
                 'empty_values', 'name_type_pairs', 'schema')

    # do_allow_dup_tags is only active when is_message
    def __init__(self, table_name, line_number=0, do_legalize_names=False,
                 logging=True, do_allow_dup_tags=True,
                 # don't set the following ones
                 intern_=intern_,
                 main_table_name=main_table_name):
        self._do_legalize_names = do_legalize_names
        self._logging = logging
        self._do_allow_dup_tags = do_allow_dup_tags

        table_name = intern_(table_name)
        assert table_name is not main_table_name, \
            "can't have table_name of %s" % main_table_name
        self.table_name  = table_name or main_table_name
        self.line_number = line_number
        self._name2index = {}
        self.names    = []
        self.messages = []
        self.types    = []
        self.last_dup_name = ''
        self.have_non_booleans = False
        self.schema = None

    def log_warn_once(self, msg,
                      did_log_warn={}):
        table_name_msg_pair = (self.table_name, msg)
        if table_name_msg_pair not in did_log_warn:
            did_log_warn[table_name_msg_pair] = True
            logging.warning("table %s: %s" % table_name_msg_pair)

    def log_debug_once(self, msg,
                       did_log_debug={}):
        if self._logging:
            table_name_msg_pair = (self.table_name, msg)
            if table_name_msg_pair not in did_log_debug:
                did_log_debug[table_name_msg_pair] = True
                logging.debug("table %s: %s" % table_name_msg_pair)

    def add(self, name, message='', type=intern(''), do_ignore_dups=False,
            len=len,
            intern=intern,
            intern_=intern_,
            unicode=unicode,
            message_as_name=message_as_name):
        """Add column name to Columns; if name is blank, cleans and uses
           message.  Set do_ignore_dups if merging columns from different
           schemas"""

        oname, omessage = name, message
        type = intern_(type)
        if self._do_legalize_names:
            name = name.strip()
            name_orig = name
            name = message_as_name(name)
            if self._logging and name_orig != name:
                # get rid of unicode characters that can geek xterm
                name_orig = unicode(name_orig)
                self.log_warn_once( "renamed '%s' to %s" % (name_orig, name) )
        # The step of intern-ing the name was causing encoding problems. It's just
        # for efficiency, so we can totally skip it.
        # else:
        #     try:
        #         name = intern_(name)
        #     except:
        #         logging.error("set do_legalize_names if encoding error")
        #         raise ValueError
        message = message_as_name(message) # be more robust to minor msg tweaks
        if not name:
            name = message
        if not name:
            # message_as_name() resulted in a null or empty string, so fall back on
            # original message, which is likely all non-ascii.
            name = omessage
        if not name:
            prev_name = self.names[-1] if self.names else 'beginning'
            logging.error( "table %s: null column name after %s"
                           % (self.table_name, prev_name) )
            raise ValueError

        name2index = self._name2index   # look here not names, cuz synonyms
        if  name in name2index:
            if do_ignore_dups:
                return
            if not self._do_allow_dup_tags:
                msg = "table %s: duplicate tag: %s" % (self.table_name, name)
                logging.error(msg)
                raise ValueError
            self.last_dup_name = name
            name_orig = name
            version_num = 2
            while name in name2index:
                name = "%s_%d" % (name_orig, version_num)
                version_num += 1
            name = intern(name)
            self.log_warn_once( "dup tag name (index=%d), renamed to %s"
                                % (len(self.names), name) )

        self.log_debug_once("recorded column '%s'" % name)
        name2index[name] = len(self.names)
        self.names.append(name)
        self.messages.append(message)
        self.types.append(type)
        if type and type is not boolean_type: # metadata columns have null type
            self.have_non_booleans = True

    def make_immutable(self):
        names = self.names              # we'll sort this list before we return
        self.names     = tuple(self.names)
        self.messages  = tuple(self.messages)
        self.types     = tuple(self.types)
        self.empty_values = tuple( [intern('')] * len(names) )
        self.name_type_pairs = tuple( zip(self.names, self.types) )

        if self.table_name is main_table_name: # order matters in grids
            names.sort()
            names = tuple(names)
        else:
            names = self.names
        self.schema   = (self.table_name, names)

    def __getitem__(self, key):
        if not isinstance(key, int):
            return self._name2index[key]
        try:
            return self.names[key]
        except:
            logging.error( "table %s: want names[%d], but Columns has %d names"
                           % ( self.table_name, key, len(self.names) ) )
            raise
            
    def get(self, key, default=None):
        if not isinstance(key, int):
            return self._name2index.get(key, default)
        return self.names[key] if key < len(self.names) else default
            
    def __iter__( self ):
        return iter(self.names)

    def __len__( self ):
        return len(self.names)

    def __contains__( self, name ):
        if isinstance( name, int ):
            return name < len(self)
        return name in self._name2index

    def __repr__( self ):
        repr_msg = "<<%s Columns>>" % self.table_name
        return repr_msg
