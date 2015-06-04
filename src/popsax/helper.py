#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#******************************************************************************
#*
#* $Id: helper.py 3234 2011-10-07 08:31:36Z jeffk $
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

import xml.sax as sax
import xml.sax.xmlreader as xmlreader
from xml.sax.handler import ContentHandler
from xml.sax.handler import DTDHandler
from xml.sax.handler import EntityResolver
from xml.sax.handler import ErrorHandler
from popsax.util import Expando
import types
# from sets import Set as set
import sys

class ContextClass( type ):
     def __init__( self, name, parents, others ):
          self.initialized = False

          type.__init__( self, name, parents, others )

class SAXHelper( Expando, ContentHandler ):

    def setDocumentLocator( self, locator ):
         self.locator = locator

    class Context( Expando ):
        __metaclass__ = ContextClass

        ignore_methods = set( ['end', 'start', 'text'] )

        def __init__( self, parent = None, attrs = None ):
           Expando.__init__( self, parent )
           this_class = type(self)
           if not this_class.initialized:
                if parent != None:
                     parent_class = type(parent)
                     for attr in dir(parent_class):
                          if attr.startswith( "_" ) or attr == 'Context':
                               continue
                          thing = getattr( parent_class, attr )
                          if not isinstance( thing, type ):
                               continue
                          if thing == this_class:
                               continue
                          if not hasattr( this_class, attr ):
                               setattr( self, attr, thing )
                               pass
                type(self).initialized = True

           if attrs:
               for name in attrs.getNames():
                  property = name.replace( "-", "_" ).replace( ":", "__" )
                  setattr( self, property, attrs.getValue( name ) )

           

        def __hasattr__( self, name ):
            if name in SAXHelper.Context.ignore_methods:
                return False
            return Expando.__hasattr__( self, name )

        def __getattr__( self, name ):
            if name in SAXHelper.Context.ignore_methods:
                raise AttributeError, name
            return Expando.__getattr__( self, name )

    def get_context( self ):
        return self.__dict__['_SAXHelper__contexts'][-1]

    context = property( get_context )

    def get_root( self ):
        return self

    root = property( get_root )

    def __init__( self ):
        Expando.__init__( self )
        self.__contexts = [self]        
        self.document = self
        self.__handlers = {}

    def characters( self, stuff ):
        context = self.context
 
        context.all_text = context.all_text + stuff
        if hasattr( context, "text" ):
            self.__contexts[-1].text( stuff )

    def startElement( self, name, attrs ):
         name = name.replace( "-", "_" ).replace( ":", "__" )

         attribute = None
         context = None
         this_context = self.context
         key = (name, type(this_context))

         try:
              if key in self.__handlers:
                   handler = self.__handlers[key]
              else:
                   handler = getattr( this_context, name )
                   self.__handlers[key] = handler
         except AttributeError:
              handler = SAXHelper.Context
              self.__handlers[key] = handler

         context = handler( this_context, attrs )
         if hasattr( context, "start" ):
              context.start()

         context.tag_name = name
         context.all_text = ''
         self.__contexts.append( context )


    def endElement( self, name ):
        if  hasattr( self.context, "end" ):
                self.context.end()
        self.__contexts[-1].all_text = None
        del self.__contexts[-1]

    def startDocument( self ):
        if hasattr( self, "start" ):
            self.context.start()

    def endDocument( self ):
        if hasattr( self, "end" ):
            self.context.end()


def parse_builder( file_name_or_file, builder, error_handler = None ):
   if isinstance( file_name_or_file, str ):
        input = open( file_name_or_file, "r" )
   else:
        input = file_name_or_file
   input_file = xmlreader.InputSource( str(file_name_or_file) )
   input_file.setByteStream( input )
   input_file.setEncoding( "UTF-8" )

   parser = sax.make_parser()
   parser.setContentHandler(builder)
   if isinstance( builder, EntityResolver ):
      parser.setEntityResolver( builder )
   if isinstance( builder, DTDHandler ):
      parser.setDTDHandler( builder )
   if error_handler is not None:
      parser.setErrorHandler( error_handler )
   parser.parse(file_name_or_file)


