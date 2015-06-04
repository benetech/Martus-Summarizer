#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#******************************************************************************
#*
#* $Id: simplehelper.py 3234 2011-10-07 08:31:36Z jeffk $
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



def attributes_to_dict( attributes ):
    results = {}
    for attribute in attributes.getNames():
        results[ str(attribute) ] = attributes.getValue( attribute )
    return results




class SimpleSAXHelper( ContentHandler ):

    def __init__( self ):
        self.__parse_contexts = []

        self.__all_methods = {
            "start": {},
            "end": {},
            "handle": {},
            "text": {},
        }

    def __get_any_method( self, name, kind ):
        try:
            method_map = self.__all_methods[kind]
            return method_map[ name ]
        except KeyError:
            if name not in self.__all_methods[kind]:

                method_name = kind + "_" + name.replace( "-", "_" )
                if hasattr( self, method_name ):

                    self.__all_methods[kind][name] = getattr( self, method_name )
                else:
                    self.__all_methods[kind][name] = None
            return self.__all_methods[kind][name]

    def __get_start_method( self, name ):
        return self.__get_any_method( name, "start" )

    def __get_end_method( self, name ):
        return self.__get_any_method( name, "end" )

    def __get_handle_method( self, name ):
        return self.__get_any_method( name, "handle" )

    def __get_text_method( self, name ):
        return self.__get_any_method( name, "text" )

    def get_parse_context( self ):
        if self.__parse_contexts:
            return self.__parse_contexts[-1]
        return None

    parse_context = property( get_parse_context )

    def characters( self, stuff ):
        if self.parse_context.text_handler:
            self.parse_context.text_handler( stuff )

        method = self.__get_text_method( self.parse_context.tag )
        if method:
            method( stuff )

    def startElement( self, name, attrs ):
        attributes = attributes_to_dict( attrs )
        method = self.__get_start_method( name )
        if method:
            method( **attributes )

        method = self.__get_handle_method( name )
        parent = None
        if len(self.__parse_contexts):
            parent = self.parse_context
        parse_context = Expando(self.parse_context)
        self.__parse_contexts.append( parse_context )

        parse_context.tag = name

        if method:
            parse_context.generator = method( **attributes )
        else:
            parse_context.generator =  self.default_action()

        parse_context.text_handler = parse_context.generator.next()


    def endElement( self, name ):
        parse_context = self.parse_context
        try:
            parse_context.generator.next()
            raise "Non-terminated generator"
        except StopIteration:
            del self.__parse_contexts[-1]

        method = self.__get_end_method( name )
        if method:
            method()

    def __default_text_handler( self, text ):
        self.parse_context.text += text

    def default_text_handler( self ):
        self.parse_context.text = ""
        return self.__default_text_handler

    def default_action( self ):
        yield None


def parse_builder( file_name, builder, error_handler = None ):
   input_file = xmlreader.InputSource( file_name )
   input_file.setByteStream( open( file_name, "r" ) )
   input_file.setEncoding( "UTF-8" )

   parser = sax.make_parser()
   parser.setContentHandler(builder)
   if isinstance( builder, EntityResolver ):
      parser.setEntityResolver( builder )
   if isinstance( builder, DTDHandler ):
      parser.setDTDHandler( builder )
   if error_handler is not None:
      parser.setErrorHandler( error_handler )
   parser.parse(file_name)


