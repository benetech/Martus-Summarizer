#!/usr/bin/env python
# -*- coding: utf-8 -*-
#******************************************************************************
#*
#* $Id: dsv2.py 3540 2012-07-10 14:39:47Z jeffk $
#*
#* $Revision: 3540 $
#*
#* $Date: 2012-07-10 07:39:47 -0700 (Tue, 10 Jul 2012) $
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
# This is a trial replacement for the hrdag.dsv library.
# Because of many updates to python since the original hrdag.dsv was written,
# espeially named tuples, much of the old functionality of the library is now
# present in the python standard library.  In addition, we have standardized
# our csv formats a lot, so we don't need so many different functions and
# options in the library.
# 
# We actually may not even need this library once the standard library
# csv module supports named tuples.
#
# Returns named tuples instead of hrdag.record instances; these behave very
# similarly, so I don't expect any problems.


import csv
import sys, os.path
import collections

from util import legalize_field_name

def read_records(datafile, column_name_map=None, rename_duplicate_names=False):
    """ Returns an iterator over records in file as tuples.
    
        datafile should be a string giving the path to the desired file
        to be read, or an already open file containing the dsv data;
        '-' can be used to read from stdin.

        An optional column_name_map will rename datafile's column names.
        
        If rename_duplicate_names is True, any column names that are duplicates
        (after cleaning and passing through the column_name_map) will be renamed
        as <duplicated_name>_1, <duplicated_name>_2, etc.  Default False, which
        means an exception will be raised if there are duplicate column names.
        
        Formatting assumptions:
          - The first line is a header.
          - Delimiters are pipes (|), commas (,), or tabs (\t)
          - Fields are optionally quoted by double quotes(\"), and
            quotes are escaped by doubling them (\"\")
    """
    if datafile == '-':
        data = sys.stdin
    elif isinstance(datafile, str):
        assert os.path.exists(datafile), datafile
        data = open(datafile, 'rU')     # U means Universal newlines
    else:
        # Test for the methods we require.  Should be present in any file-like object.
        assert hasattr(datafile, 'readline') and hasattr(datafile, '__iter__')
        data = datafile
        
    # Read the header from the 1st line, guess which character is the delimiter
    possible_delimiters = "|,\t"
    first_line = data.readline()
    assert first_line, "Input is empty or has a blank first line."
    delimiter_counts = [ sum( delim==c for c in first_line )
                         for delim in possible_delimiters ]
    assert any(delimiter_counts), "No delimiters found in first line!"
    # [-1] gets the last element of the sort
    #   (delimiter with biggest count, [1] gets the delimiter itself)
    guessed_delimiter = \
        sorted(zip(delimiter_counts, possible_delimiters))[-1][1]
    
    # Make an iterator that gives the first and then all other lines together,
    # without the need to seek backwards in the file.  This lets us support
    # non-seekable file-like objects.
    def all_lines():
        yield first_line
        for line in data:
            yield line
    
    # read the file using the csv library, return the results as named tuples
    csv_records = csv.reader(all_lines(), delimiter=guessed_delimiter,
                             quotechar='"', doublequote=True)
    column_names = csv_records.next()
    original_column_names = column_names
    if column_name_map:
        column_names = [ column_name_map.get(name, name) for name in column_names ]
    
    # Handle duplicate names
    if rename_duplicate_names:
        column_name_counts = collections.defaultdict(int)
        for cn in column_names:
            column_name_counts[cn] += 1
        for cn, count in column_name_counts.items():
            if count > 1:
                for i in range(count):
                    column_names[column_names.index(cn)] = '%s_%d' % (cn, i)

    class RecordIterator():
        def __init__(self):
            self.column_names = original_column_names
            self.cleaned_column_names = column_names
            self._fields = column_names
        
        def __iter__(self):
            for record in csv_records:
                yield record
        
        # Visible access to the column names        
        def fieldnames(self):
            return record_type._fields
        column_names = fieldnames
            
    return RecordIterator()

reader = read_records                   # analogous to the next one
   
def writer(output_file=None, column_names=None, delimiter='|', quotechar='"'):
    """ Delegate writing directly to the csv module, using our default
    csv format parameters.  [To disable the csv module's quoting,
    set quotechar to a character that doesn't appear in your data,
    such as '@' or '~'.]
    
    If column_names are provided, they are coerced via __str__ and written as
    the first output line.
    """
    if not output_file:
        output_file = sys.stdout
    elif isinstance(output_file, str):
        output_file = open(output_file, 'w') 
    assert isinstance(output_file, file) 
    csv_writer = csv.writer(output_file,
                            delimiter=delimiter, quotechar=quotechar,
                            lineterminator='\n', doublequote=True)
    if column_names is not None:
        if isinstance(column_names, str):
            assert delimiter in column_names, "can't find delimter in header"
            column_names = column_names.split(delimiter)
        column_name_strings = [ str(cn) for cn in column_names ]
        if len(set(column_name_strings)) != len(column_name_strings):
            for column_name in set(column_name_strings):
                column_name_strings.remove(column_name)
            raise ValueError("Duplicate column names: %s" %column_name_strings)
        csv_writer.writerow(column_name_strings)
    return csv_writer
