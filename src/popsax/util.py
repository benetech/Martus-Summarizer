#!/usr/bin/env python
# -*- coding: UTF-8 -*-
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

"""
The popsax utility library
"""


# ----------------------------------------------------------------------------

class Expando(object):
        """
        Expando is an object that allows for any number of arbitrary fields
        to be assigned to it at run-time.  The object essentially acts as a
        container or dictionary.
        
        An Expando can also have a parent from which it can inherit its
        values.  A childs values over-rides the values of the parent in the
        search order.  Any object can be a parent, but typically parents are
        themselves Expando objects.
        
        There is no "parent" property, rather access to parent is via the
        negation operator.
        """
        def __init__( self, parent = None, **fields ):
            """
            Expando contstructor can take a parent and a set of fields
            in the parameter list.
            """
            self.__parent = parent
            for name,value in fields.items():
                setattr( self, name, value )

        def __getattr__( self, name ):
            """
            Attempts to fetch value from self, on failure attempts to fetch
            value from parent.
            """
	    this_dict = self.__dict__
#            try:
#                return self.__dict__[name]
#            except KeyError:
#                if -self:
	    if name in this_dict:
		    return this_dict[name]
	    if '_Expando__parent' in this_dict:
                    return getattr( this_dict['_Expando__parent'], name )

            raise AttributeError, "No '" + name + "' in class " + str(self.__class__)

        def __hasattr__( self, name ):
            """
            True if self has value or parent has value
            """
	    this_dict = self.__dict__
            if name in this.__dict__:
                return True
            if '_Context__parent' not in this_dict:
                return False
            return hasattr( this_dict['_Context__parent'], name )

        def __neg__( self ):
            """
            This is how you fetch the parent from the outside
            """
            return self.__parent

        def __iter__( self ):
            """
            Only iterates over own values not the parent.
            """
            return iter( self.__dict__ )
            
            

