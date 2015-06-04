#!/usr/bin/env python
# -*- coding: utf-8 -*-

subdirs_whose_tags_are_cleaned = ('IN', 'software')

#******************************************************************************
#*
#* $Id: martus2csv.py 3556 2012-07-17 18:41:17Z scott $
#*
#* $Revision: 3556 $
#*
#* $Date: 2012-07-17 11:41:17 -0700 (Tue, 17 Jul 2012) $
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

__all__ = ['run_flattener']

usage = """usage: %prog [options] XML_file(s) [-o output_name]
   Flatten a list of exported Martus bulletins.  Here is an example:
     %prog my-bulletins-1.xml my-bulletins-2.xml -o my-flat-file
   This code makes two passes over the input, so can't read stdin or a FIFO"""

__version__ = "$Revision: 3556 $"

import sys, os.path, time
import codecs
import logging as logsys
import zipfile, bz2
from cStringIO import StringIO
# from optparse import OptionParser
import gc

from util import DictRecordFastRead, tuple_index
from sax  import SAXHelper, parse_builder

from libmartus2csv import (intern_, message_as_name, cleaned_value,
                           main_table_name, Columns)

# option_parser = OptionParser(usage=usage, version=__version__)
# add_opt = option_parser.add_option
# 
# add_opt("-o", "--output",
#         dest="output_name",
#         help="Name of file set to create", metavar="OUTPUT")
# 
# add_opt("-d", "--allow-duplicate-ids", action="store_true", default=False,
#         dest="allow_duplicates",
#         help="Allow duplicate LocalIds")
# 
# add_opt("-D", "--ignore-dups", action="store_true", default=False,
#         dest="ignore_duplicates",
#         help="Ignore bulletins with duplicate LocalIds")
# 
# add_opt("-t", "--clean-tag-names", action="store_true", default=False,
#         dest="do_clean_tag_names",
#         help="clean Tag names the same as Label names")
# 
# add_opt("-T", "--not-clean-tag-names", action="store_true", default=False,
#         dest="do_not_clean_tag_names",
#         help="IN, software, etc default to 'clean': override")
# 
# add_opt("-A", "--allow-any-dup-tag-names", action="store_true", default=False,
#         dest="allow_any_dup_tag_names",
#         help="Allow duplicate tag names, even in the main table")
# 
# add_opt( "-l", "--limit", action="store", type="int", default=sys.maxint,
#          dest="limit", help="Limit processed bulletins per file")
# 
# add_opt('-q', '--quiet', action='store_true', default=False,
#         dest='is_quiet', help="only log warnings and errors")
# 
# add_opt('-v', '--verbose', action='store_true', default=False,
#         dest='is_verbose', help="log debug statements")
# 
# options, args = option_parser.parse_args()

# Global variables.
# These are globals with values that do not change.  They are hard-wired and
# not exposed in the GUI
allow_duplicates = False
ignore_duplicates = False
bulletin_limit = sys.maxint
do_clean_tag_names = False
allow_any_dup_tag_names = True
is_quiet = False
is_verbose = False

# Set up logging.  Can do on module load.
logsys.basicConfig()
logging = logsys.getLogger( )

Context = SAXHelper.ContextContext = SAXHelper.Context

class HitLimit(ValueError): pass

# ----------------------------------------------------------------------------

# user can't change these field's Value
ignored_types = ( intern('test-without-ignoring'), )
ignored_types = ( intern('MESSAGE'), intern('SECTION'), )

empty_tag       = intern('')
null_type       = intern('')
date_type       = intern('DATE')
date_range_type = intern('DATERANGE')
boolean_type    = intern('BOOLEAN')
boolean_default = intern('0')

metadata_column_names = ( intern('LocalId'),
                          intern('Version'),
                          intern('HistoryIds'),
                          # intern('CollisionIds'),
                          intern('DateSaved'),
                          intern('DateSavedGMT'),
                          intern('SecondsSaved'),
                          # intern('AllPrivate'),
                          intern('FileName'),
                          # intern('ClientBuild'), 
                          )

LocalId_index      = tuple_index(metadata_column_names, 'LocalId')
Version_index      = tuple_index(metadata_column_names, 'Version')
HistoryIds_index   = tuple_index(metadata_column_names, 'HistoryIds')
# CollisionIds_index = tuple_index(metadata_column_names, 'CollisionIds')
DateSaved_index    = tuple_index(metadata_column_names, 'DateSaved')
DateSavedGMT_index = tuple_index(metadata_column_names, 'DateSavedGMT')
SecondsSaved_index = tuple_index(metadata_column_names, 'SecondsSaved')
# AllPrivate_index   = tuple_index(metadata_column_names, 'AllPrivate')
FileName_index     = tuple_index(metadata_column_names, 'FileName')
# ClientBuild_index  = tuple_index(metadata_column_names, 'ClientBuild')

grid_metadata_column_names = metadata_column_names[0:1]

# FIXME: replace with synonyms in tagged_bulletin
old_IN_grid_tag = intern('SecurityOfficialsReturnBody1')
new_IN_grid_tag = intern('DetentionFacility1')

# ----------------------------------------------------------------------------

class MartusSAXHelper(SAXHelper):
    def parse_location(self):
        data = (self.bulletin_count,
                self.locator.getLineNumber(), self.current_file)
        return "record %d (line %d in %s)" % data

# ---------------------------------------------

do_cache_columns = True
do_cache_columns = False

##
# Column structure
#
#  Builds column meta-data for output CSV files
##
class MartusColumnBuilder(MartusSAXHelper):

    def __init__( self ):
        SAXHelper.__init__( self )

        self.bulletin_count = 0
        self.ignore_tags = set(
            [
                intern("AuthorAccountId"),
                intern("PublicAndPrivateData"),
                intern("Attachment")
            ]
        )
        self.grid_tag2merged_columns = {}
        self.schema2grid_tag2columns = {}
        self.per_bulletin_grid_tag2columns = []

    class MartusBulletin( Context ):

        def start( self ):
            self.root.bulletin_count += 1
            if self.root.bulletin_count > bulletin_limit:
                raise HitLimit
            logging.debug( "Checking " + self.parse_location() )

            line_number = self.locator.getLineNumber()
            if not do_cache_columns:
                self.columns = Columns('', line_number, do_clean_tag_names)
                self.grid_tag2columns = {empty_tag: self.columns}
                
                for name in metadata_column_names:
                    self.columns.add(name)  # row_from_values assumes no type
            else:
                self.start_line_number = line_number
                self.grid_tag2columns = {}
                self.columns_args = []
                self.columns_args2columns = {}
                self.columns_args_append = self.columns_args.append
                for name in metadata_column_names:
                    self.columns_args_append( (name, '', null_type) )

        def end(self):
            if not do_cache_columns:
                columns = self.columns
                columns.make_immutable()
            else:
                columns_args_copy = list(self.columns_args)
                columns_args_copy.sort()
                columns_args = tuple(columns_args_copy)
                columns = self.columns_args2columns.get(columns_args)
                if not columns:
                    line_number = self.start_line_number
                    columns = Columns('', line_number, do_clean_tag_names)
                    self.columns = columns
                    self.grid_tag2columns[empty_tag] = columns
                    self.columns_args2columns[columns_args] = columns
                    columns_add = columns.add
                    for args in self.columns_args:
                        columns_add(*args)
                    columns.make_immutable()
            if columns.last_dup_name and not allow_any_dup_tag_names:
                logging.error("table %s: dup name %s is illegal,"
                              " since not in grid"
                              % (main_table_name, columns.last_dup_name))
                sys.exit(1)

            schema = [columns.schema
                      for columns in self.grid_tag2columns.values()]
            schema.sort()
            schema = tuple(schema)

            schema2grid_tag2columns = self.root.schema2grid_tag2columns
            grid_tag2columns = schema2grid_tag2columns.get(schema)
            if  grid_tag2columns is None:
                grid_tag2columns = self.grid_tag2columns
                schema2grid_tag2columns[schema] = self.grid_tag2columns

                setdefault = self.root.grid_tag2merged_columns.setdefault
                line_num   = columns.line_number
                for tag, columns in grid_tag2columns.items():
                    merged_columns = setdefault( tag, Columns(tag, line_num) )
                    merged_columns_add = merged_columns.add
                    for name, type in columns.name_type_pairs:
                        merged_columns_add(name, '', type, True)

            self.root.per_bulletin_grid_tag2columns.append(grid_tag2columns)

        class MainFieldSpecs( Context ):
            class Field( Context ):
                def __init__( self, parent, attrs ):
                    Context.__init__(self, parent, attrs)
                    self.type = intern_( attrs.getValue("type") )

                class Tag( Context ):
                    def end(self,
                            intern_=intern_):
                        if self.type in ignored_types:
                            return

                        tag = self.all_text
                        if do_clean_tag_names:
                            tag = message_as_name(tag)
                        else:
                            tag = intern_(tag)
                        if tag not in self.ignore_tags:
                            if  self.type != "GRID":
                                if not do_cache_columns:
                                    self.columns.add(tag, '', self.type)
                                else:
                                    args = (tag, '', self.type)
                                    self.columns_args_append(args)
                            else:
                                if  tag is old_IN_grid_tag:
                                    tag  = new_IN_grid_tag
                                if not do_cache_columns:
                                    line_number = self.locator.getLineNumber()
                                    columns = Columns(tag, line_number,
                                                      do_clean_tag_names)
                                    self.grid_tag2columns[tag] = columns
                                    for name in grid_metadata_column_names:
                                        # row_from_values assumes null type
                                        columns.add(name)
                                    (-self).columns = columns
                                else:
                                    line_number = self.locator.getLineNumber()
                                    (-self).start_line_number = line_number
                                    columns_args = []
                                    self.grid_tag2columns_args[tag] = \
                                        columns_args
                                    for name in grid_metadata_column_names:
                                        # row_from_values assumes null type
                                        args = (tag, '', null_type)
                                        columns_args.append(args)
                                    (-self).columns_args = columns_args

                class GridSpecDetails( Context ):
                    def start(self):
                        # FIXME: this code was in end(), not sure about it
                        if do_cache_columns:
                            args = tuple(self.columns_args)
                            columns = self.columns_args2columns.get(args)
                            if not columns:
                                columns = Columns(tag, self.line_number,
                                                  do_clean_tag_names)
                            self.columns = columns
                            self.columns_add = columns.add

                    def end(self):
                        self.columns.make_immutable()

                    class Column(Context):
                        def __init__(self, parent, attrs,
                                     empty_tag=empty_tag,
                                     intern_=intern_):
                            Context.__init__(self, parent, attrs)
                            self.type = attrs.getValue("type")
                            self.tag = self.label = empty_tag

                        def end(self):
                            if not do_cache_columns:
                                self.columns.add(self.tag, self.label, self.type)
                            else:
                                args = (self.tag, self.label, self.type)
                                self.columns_args_append(args)

                        class Tag( Context ):
                            def end( self ):
                                tag = self.all_text
                                if do_clean_tag_names:
                                    tag = message_as_name(tag)
                                else:
                                    tag = intern_(tag)
                                (-self).tag = tag

                        class Label( Context ):
                            def end( self ):
                                (-self).label = self.all_text

        PrivateFieldSpecs=MainFieldSpecs

##
# Main flattening class
#
#  Creates flat files
##

class MartusCSVBuilder(MartusSAXHelper):

    def __init__(self, name, column_metadata):
        SAXHelper.__init__( self )
        self.bulletin_count = 0
        self.local_ids = set()

        self.per_bulletin_grid_tag2columns = \
            column_metadata.per_bulletin_grid_tag2columns
        grid_tag2CSV_metadata = self.grid_tag2CSV_metadata = {}
        for tag, columns in column_metadata.grid_tag2merged_columns.items():
            columns.make_immutable() # easier here than in MartusColumnBuilder
            CSV_data = grid_tag2CSV_metadata[tag] = DictRecordFastRead()
            file_name = name
            if tag:
                file_name += "-" + tag
            CSV_data.file_name = file_name + ".csv"
            CSV_data.output    = codecs.open(CSV_data.file_name, "w", "UTF-8")
            CSV_data.merged_columns = columns
            self.write_header(CSV_data.merged_columns, CSV_data.output)
            if not tag:                 # main table?
                self.CSV_metadata = CSV_data

    def write_header(self, columns, output,
                     date_range_type=date_range_type):
        names = []
        names_append = names.append
        for name, type in columns.name_type_pairs:
            if type is date_range_type:
                names_append(name + '_low')
                names_append(name + '_high')
            else:
                names_append(name)

        print >>output, '|'.join(names)

    def merged_values(self, CSV_metadata, values):
        columns        = CSV_metadata.columns
        merged_columns = CSV_metadata.merged_columns
        merged_values  = list(merged_columns.empty_values)
        for name, value in zip(columns.names, values):
            try:
                index = merged_columns[name]
            except:
                logging.error("CSV_metadata.columns.names is %s and CSV_metadata.merged_columns is %s" % (CSV_metadata.columns.names, CSV_metadata.merged_columns._name2index.keys()))
                raise
            merged_values[index] = value
        return  merged_values

    def row_from_values(self, CSV_metadata, values,
                        null_date='0001-01-01',
                        date_type=date_type,
                        date_range_type=date_range_type,
                        boolean_type=boolean_type,
                        boolean_default=boolean_default):
        merged_columns = CSV_metadata.merged_columns
        # the main bulletin is never empty (in a rational world);
        #   if you use is_row_empty for main, you must handle defaulted fields,
        #   and you must notice whether any grid rows were written.
        is_row_empty = (merged_columns.table_name is not main_table_name)
        have_non_booleans = CSV_metadata.columns.have_non_booleans
        row = []
        row_append = row.append
        for type, value in zip(merged_columns.types, values):
            if type is date_range_type:
                value = str(value)
                if  value.startswith( ('Range:', 'range:') ):
                    value = value[6:]
                dates = value.split(',')
                for index in range( len(dates) ):
                    if  dates[index] == null_date:
                        dates[index] =  ''
                    elif dates[index]:
                        is_row_empty = False
                if len(dates) == 1:
                    dates.append(dates[0])
                assert len(dates) == 2, "invalid date-range: %s" % dates
                row.extend(dates)
                continue

            if type is date_type:
                value = str(value)
                if  value.startswith( ('Simple:', 'simple:') ):
                    value = value[7:]
                if  value == null_date:
                    value = ''
                elif value:
                    is_row_empty = False
            elif type is boolean_type and value == boolean_default \
                    and have_non_booleans:
                pass # not necessarily real value, and have unambiguous columns
            elif type and value:        # metadata columns don't have a type
                is_row_empty = False
            row_append(value)

        return None if is_row_empty else row

    def print_row(self, CSV_metadata, values):
        columns = CSV_metadata.merged_columns
        if len(columns) < len(values):
            logging.error( "table %s: has %d columns, found %d values for %s"
                           % ( columns.table_name, len(columns), len(values),
                               self.parse_location() ) )
            sys.exit(1)
        values = self.merged_values(CSV_metadata, values)
        row  = self.row_from_values(CSV_metadata, values)
        if row:
            line = "|".join(row)
            if '"' in line:
                # R will drop record if field doesn't conform to CSV standard
                quoted_row = []
                for field in row:
                    if '"' in field:
                        field = '"%s"' % field.strip('"').replace('"', '""')
                    quoted_row.append(field)
                line = "|".join(quoted_row)
            print >>CSV_metadata.output, line

    def close_all_csv_files(self):
        for (tag, CSV_metadata) in self.grid_tag2CSV_metadata.items():
            CSV_metadata.output.close()


    class MartusBulletin( Context ):

        def start( self ):
            self.root.bulletin_count += 1
            if self.root.bulletin_count > bulletin_limit:
                raise HitLimit
            logging.info( "Flattening " + self.parse_location() )
            self.bulletin = self
            self.local_id = None
            self.is_all_private = ''
            self.root.do_toss_bulletin = False

            grid_tag2columns = self.per_bulletin_grid_tag2columns.pop(0)
            for tag, columns in grid_tag2columns.items():
                CSV_metadata = self.grid_tag2CSV_metadata[tag]
                CSV_metadata.columns = columns
                if not tag:             # main table?
                    self.columns = columns
                    self.column_name2index = columns._name2index
                    self.values = list(columns.empty_values)

        class BulletinMetaData(Context):

            class BulletinLocalId( Context ):
                def end(self,
                        LocalId_index=LocalId_index,
                        FileName_index=FileName_index):
                    local_id = intern_(self.all_text)
                    self.values[LocalId_index] = local_id
                    if local_id in self.local_ids:
                        msg = ( "duplicate LocalId %s at %s"
                                % ( local_id, self.parse_location() ) )
                        if ignore_duplicates:
                            logging.warning("dropping " + msg)
                            self.root.do_toss_bulletin = True
                        elif not allow_duplicates:
                            logging.error(msg)
                            raise ValueError, ("DuplicateLocalId", local_id)
                        else:
                            logging.warning(msg)
                    self.local_ids.add(local_id)
                    self.bulletin.local_id = local_id

                    basename = os.path.basename(self.current_file)
                    self.values[FileName_index] = basename

            class BulletinLastSavedDateTime(Context):
                def end(self,
                        gmtime=time.gmtime,
                        strftime=time.strftime,
                        DateSavedGMT_index=DateSavedGMT_index,
                        SecondsSaved_index=SecondsSaved_index):
                    unix_time = self.all_text.strip()[:-3]
                    self.values[SecondsSaved_index] = unix_time
                    unix_time = int(unix_time)
                    time_tuple = gmtime(unix_time)
                    date = strftime("%x %X", time_tuple)
                    self.values[DateSavedGMT_index] = date

            class LocalizedBulletinLastSavedDateTime(Context):
                def end(self,
                        DateSaved_index=DateSaved_index):
                    self.values[DateSaved_index] = self.all_text.strip()

            class AllPrivate(Context):
                def end(self,
                        AllPrivate_index=None):
                        # AllPrivate_index=AllPrivate_index):
                    pass
                    # self.values[AllPrivate_index] = self.all_text.strip()

            class BulletinVersion(Context):
                def end(self,
                        Version_index=Version_index):
                    self.values[Version_index] = self.all_text.strip()

            class History(Context):
                def start(self):
                    self.history_ids = []
                    self.history_ids_append = self.history_ids.append

                class Ancestor(Context):
                    def end(self):
                        value = intern_(self.all_text)
                        self.history_ids_append(value)
                def end(self):
                    self.root.history_ids = self.history_ids
            # put 'end' at BulletinMetaData level in case no History element
            def end(self,
                    LocalId_index=LocalId_index,
                    HistoryIds_index=HistoryIds_index):
                history_ids = self.root.history_ids
                history_ids.append(self.values[LocalId_index])
                self.values[HistoryIds_index] = ','.join(history_ids)
            # ... since History element could be missing, need initialization
            def start(self):
                self.root.history_ids = []

        class FieldValues( Context ):
            class Field( Context ):
                def __init__(self, parent, attrs,
                             intern_=intern_):
                    Context.__init__( self, parent, attrs )
                    tag = attrs.getValue("tag")
                    if do_clean_tag_names:
                        self.tag = message_as_name(tag)
                    else:
                        self.tag = intern_(tag)

                def start( self ):
                    self.index = self.columns.get(self.tag, -1)

                class Value( Context ):

                    class GridData( Context ):
                        def start( self ):
                            if  self.tag is old_IN_grid_tag:
                                self.tag  = new_IN_grid_tag
                            try:
                                self.CSV_metadata = \
                                    self.grid_tag2CSV_metadata[ self.tag ]
                            except:
                                tags = self.grid_tag2CSV_metadata.keys()
                                tags.sort()
                                logging.error("known grid_tags: %s" % tags)
                                main_columns = \
                                    self.grid_tag2CSV_metadata[''].columns
                                logging.error("main schema at line number %d" %
                                              main_columns.line_number)
                                logging.error( "%s not found at %s"
                                               % (self.tag,
                                                  self.parse_location() ) )
                                sys.exit(1)
                            self.columns = self.CSV_metadata.columns

                        class Row( Context ):
                            def start( self ):
                                try:
                                    self.values = [self.local_id]
                                except:
                                    raise ValueError("Missing LocalId")

                            class Column( Context ):
                                def end(self,
                                        cleaned_value=cleaned_value):
                                    value = cleaned_value(self.all_text)
                                    self.values.append(value)

                            def end( self ):
                                if self.root.do_toss_bulletin:
                                    return
                                missing_field_count = \
                                    len(self.columns) - len(self.values)
                                if missing_field_count > 0:
                                    self.values += [''] * missing_field_count
                                self.print_row(self.CSV_metadata, self.values)

                    def end( self ):
                        if self.index >= 0:
                            value = cleaned_value(self.all_text)
                            self.values[self.index] = value

        def end( self ):
            if not self.root.do_toss_bulletin:
                name2index = self.columns._name2index
                self.print_row(self.CSV_metadata, self.values)

def process_files( file_list, builder ):
    def process_file( name, input ):
        try:
            try:
                logging.info( "Processing file '%s'" % name )
                builder.current_file = name
                parse_builder( input, builder )
            except HitLimit:
                pass
        finally:
            input.close()

    for file_name in file_list:
        if  zipfile.is_zipfile( file_name ):
            zipfile_object = zipfile.ZipFile( file_name )
            try:
                for info in zipfile_object.infolist():
                    if info.file_size > 0 \
                            and info.filename.lower().endswith( '.xml' ):
                        name = info.filename
                        zip_description = "%s/(%s)" % (file_name,name)
                        logging.info("Reading data from %s" % zip_description)
                        data = zipfile_object.read( name )
                        stringio = StringIO(data)
                        process_file( zip_description, stringio )
                        del data
                        del stringio
            finally:
                zipfile_object.close()
            del zipfile_object
            gc.collect()
        elif file_name.endswith('.bz2'):
            # BZ2 library only supports compressed files containing a single xml member.
            bz2_object = bz2.BZ2File(file_name)
            try:
                process_file(file_name, bz2_object)
            finally:
                bz2_object.close()
            del bz2_object
            gc.collect()
        else:
            if not ( file_name.endswith('.xml') or os.path.isfile(file_name) ):
                file_name += '.xml'
            process_file( file_name, open( file_name ) )

def do_flattening(bulletin_files, output_name):
    
    if is_quiet:
        logging.setLevel( logsys.WARN )
    elif is_verbose:
        logging.setLevel( logsys.DEBUG )
    else:
        logging.setLevel( logsys.INFO )
        
    
    if output_name.endswith('.csv'):
        output_name = output_name[:-4]
    
    logging.debug( "Martus 3 XML" )
    logging.info( "Determining column structure" )
    column_metadata = MartusColumnBuilder()
    process_files(bulletin_files, column_metadata)

    logging.info( "Flattening bulletins" )
    csv_builder = MartusCSVBuilder(output_name, column_metadata)
    process_files(bulletin_files, csv_builder)
    csv_builder.close_all_csv_files()


def run_flattener(input_xml_filename, output_filename):
    assert input_xml_filename
    assert output_filename
    bulletin_files = [input_xml_filename]
    do_flattening(bulletin_files, output_filename)

# import profile
#profile.run( "do_flattening()", "profile" )

# do_flattening()
