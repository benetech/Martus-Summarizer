# -*- coding: utf-8 -*-

from __future__ import division

import sys
import time
import math
import os.path
import logging

# Local imports
import dsv2
from freq_table import FrequencyTable
from html_formatting_util import *

__all__ = ['run_summarizer']

# -----------------------------------------------------------------------------
#                     Type Guessing
# -----------------------------------------------------------------------------     

def is_int(val):
    try:
        int(val)
    except:
        return False
    return True
    
def is_float(val):
    try:
        float(val)
    except:
        return False
    return True
    
def is_char(val):
    return len(val) == 1
   
def is_string(val):
    return True
   
# types in priority order
type_check_functions = [ is_int, is_float, is_char, is_string ]
                     
def guess_type(vals):
    # in case it's an iterator
    vals = list(vals)
    # filter out missing values
    vals = filter(lambda x: x != "", vals)
    for check_func in type_check_functions:
        if False not in map(check_func, vals):
            return check_func.__name__[3:]
    return "unknown"  
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
#         Helper functions for constructing attribute summaries
# -----------------------------------------------------------------------------
 
def make_att_summary_div(field, freq_table, distinct_value_count, non_null_count,
                         number_of_example_values, row_count):
    """ div that looks like a table row that gives a short summary of the
        attribute.
    """
    logging.info("  ...%s" % field)  # progress message
    
    # First column: field name, which is also a link that toggles the visibility
    # of the detailed attribute summary information.
    field_name_toggle_link = a(field, href= \
       "javascript:toggleVisibility('%s')" % details_div_id(field))    
    # Flag key columns
    if distinct_value_count == row_count:
        field_name_toggle_link += " (key)"
        
    # Second column: field type.  Run my (primitive) type guesser.        
    guessed_type = guess_type(freq_table.get_values())
    
    # Fourth column: completeness (fraction of values not null)
    if non_null_count == 0:
        guessed_type = ''
        distinct_value_count = ''
    
    if row_count == 0:
        completeness_pcnt = "0%"
        completeness_str = 'NA'
    else:
        completeness_pcnt = '%.1f%%' % (100.0 * non_null_count / row_count)
        # TODO: when align="char"/char="." is supported in browsers, use it instead of this span hack.
        (whole_part, frac_part) = completeness_pcnt.split('.')
        completeness_str = "<span class=left>%s</span>.<span class=right>%s (%d/%d)</span>" % \
                                (whole_part, frac_part, non_null_count, row_count)
    completeness_table = make_table(cells=((make_chart(completeness_pcnt),
                                            completeness_str),) )
        
    # Pack it all together
    content = one_row_table(field_name_toggle_link,
                            guessed_type,
                            distinct_value_count,
                            completeness_table)
                            
    # Add the detailed attribute summary information as a hidden sub-div
    # Give it an id based on the field name so that the javascript
    # visibility toggling function can find it.
    content += div(make_field_detail_div(field, freq_table, number_of_example_values, row_count), 
                   id=details_div_id(field),
                   klass='field_info_details')
                   
    # Wrap the whole thing up in a div with an alternating background color.                   
    return div(content, klass=alternating_row_styles.next())

def make_field_detail_div(field, freq_table, number_of_example_values, row_count):
    """ div that can be revealed that contains more detailed attribute summary
        info.  Right now, it shows two small tables, one with sorted values
        so that the smallest and largest values can be seen, and one with
        values sorted by their frequency so the commonest and rarest values
        can be seen.
    """    
    #logging.info("sorting %s by value" % field)
    sorted_values = list(freq_table.get_values())
    sorted_values.sort()
    
    #logging.info("sorting %s by value count" % field)
    sorted_count_values = list(zip(freq_table.get_counts(),
                                   freq_table.get_values()))
    sorted_count_values.sort()
    sorted_count_values.reverse()
    
    max_shown_values = number_of_example_values
    if max_shown_values == 0:
        # Special case, no example values at all
        values = []
        freq_values = []
    elif max_shown_values is not None and len(sorted_values) > max_shown_values:
        # There are too many to show all distinct values.  Just grab the
        # top and bottom of the list and connect them with an ellipsis.
        first_values = sorted_values[0:max_shown_values//2]   # half from the beginning
        last_values = sorted_values[-max_shown_values//2:] # and half from the end
        values = first_values + ["..."] + last_values
        
        commonest_values = sorted_count_values[0:max_shown_values//2]
        rarest_values = sorted_count_values[-max_shown_values//2:]
        freq_values = commonest_values + [["", "..."]] + rarest_values
    else:
        # There are few enough distinct values for this attribute that all
        # of them can be shown, or no maximum is enforced.
        values = sorted_values
        freq_values = sorted_count_values
    
    # Make values into a list of singleton lists for table layout
    values = [ [value] for value in values ]
    # Add count and percentage colums to the little frequency table
    freq_values = [ (val,cnt, pcnt(cnt,row_count)) for (cnt,val) in freq_values ]
    # Add a header column to the little frequency table
    freq_values = [["", "count", "%"]] + freq_values
    
    # A 1x2 table to place two two summary tables nicely whithin the detail area
    content = make_table( [[
        div("Sorted Distinict Values") + make_table(values, align="center"),
        div("Most Common and Rarest Values") + make_table(freq_values, align="center")]],
        align="center", width="100%", klass="summary_tables")
        
    return content

def pcnt(int_string, total):
    """ Little utility function for forming a percentage string """
    if int_string == "":
        return ""
    else:
        return '%.1f%%' % (100.0 * int(int_string) / total)

def fixed_width_row(cells):
    column_widths = ('40%', '15%', '15%', '30%')
    assert len(cells) == len(column_widths)
    row = ""
    for (i, cell) in enumerate(cells):
        row += td(cell, width=column_widths[i])
    return tr(row)

def one_row_table(*cells): 
    return table(fixed_width_row(cells), width="100%")

def details_div_id(s):
    """ Return the id of the div used to display the attribute summary. """
    return s + "_details"
# -----------------------------------------------------------------------------


def main(input_file, output_file, number_of_example_values):
    
    logging.info("Running summarizer on %s" % input_file)
    logging.info("Writting summary to %s" % output_file)

    outfile = open(output_file, 'w')

    def w(s):
        outfile.write(s + '\n')

    input_rows = dsv2.read_records(input_file, rename_duplicate_names=True)
    fields = input_rows.column_names
    # Handle empty field names by giving them placeholder names
    i = 1
    for j in range(len(fields)):
        if fields[j].strip() == "":
            fields[j] = "this_field_has_no_name_in_input_file__%d" % i
            i += 1

    # data structures needed for calculations
    freq_tables = dict()
    non_null_counts = dict()
    distinct_value_counts = dict()
    for field in fields:
        freq_tables[field] = FrequencyTable()
        non_null_counts[field] = 0

    row_count = 0
    logging.info("Passing over input data; building frequency tables in memory.")

    # Pass over the input file, adding values to the frequency tables
    # and collecting needed information.
    for row in input_rows:
        row_count += 1
        for (field, value) in zip(fields, row):
            freq_tables[field].increment(value)
            if value:
                non_null_counts[field] += 1


    for field in fields:
        distinct_value_counts[field] = len(freq_tables[field].get_values())
    
    # Now the HTML-formatted output.
    w('<html>')
    w('<head>')
    # assume utf-8
    w('    <meta http-equiv="content-type" content="text/html; charset=UTF-8">')
    # Page title, for nicer window and tab labeling
    page_title = os.path.splitext(os.path.basename(input_file))[0]
    w('    <title>%s</title>' % page_title)

    # CSS styles used by classes defined in this script
    w("""
        <style type="text/css">
        div.header_row td { font-weight: bold; }
        div.row { border-width: 0px 0px 1px 0px;
                  border-style: solid;
                  border-color: black; }

        div.field_info_details { display: none; }

        div.centered { margin-left: 5%; margin-right: 5% }

        table.summary_tables td div { text-align: center;
                                      text-decoration: underline;
                                      font-style: italic;
                                      margin-left: 5%;
                                      margin-right: 5%; }

        table.summary_tables td table td { padding-left: 20px; }

        table.pairwise_dependencies td { text-align: center;
                                         border-width: 1px;
                                         border-style: solid;
                                         border-color: black; }
        table.pairwise_dependencies a { text-decoration: none; }
        div.chi_summary { display: block; }
        div.chi_detail { display: none; }

        span.left { float: left; text-align: right; width: 2em; }
        span.right { float: right; text-align: left; }
        </style>
    """)
    # CSS styles used by classes defined in my html_formatting_util
    w(css_style_block)

    # Javascript function that toggles the visibility of the attribute summary details.
    w("""
        <script language="Javascript">
        function toggleVisibility(elem_name) {
            elem = document.getElementById(elem_name)
            new_value = elem.style.display == "block" ? "none" : "block"
            elem.style.display = new_value
        }
        </script>
    """)

    w('</head>')
    w('<body>')
    
    
    w(h1(page_title))

     # Warnings
    w("""
        <p style="text-align: center">Please note that the Martus
        bulletin data below is not encrypted and anyone who gets
        a copy of this file will be able to read all the data.</p>
    """)

    
    # -----------------------------------------------------------------------------
    #                  Attribute Summaries
    # -----------------------------------------------------------------------------
    logging.info("Summarizing attributes...")

    # The header row of the attribute summary table
    field_info_headers = one_row_table('field name', 'guessed type',
                                       'distinct values', 'completeness')
    field_info_header_row = div(field_info_headers, klass="header_row row")                               

    # Each attribute summary is put in a div, and they are all wrapped in 
    # a centering div.
    attribute_summaries = [make_att_summary_div(field, freq_tables[field], distinct_value_counts[field],
                                                non_null_counts[field],
                                                number_of_example_values, row_count) for field in fields]
    whole_table = [field_info_header_row] + attribute_summaries
    table_str = "\n".join(whole_table)
    w(div(table_str, klass="centered"))
    w(center(p("%d Rows, %d Columns" % (row_count, len(fields)))))
    # -----------------------------------------------------------------------------


    w('</body></html>')
    outfile.close()
    
    logging.info("Summarization Complete.")
     

# Entry point for wrapper script.  The only exported name.
def run_summarizer(input_file, output_file, number_of_example_values):
    main(input_file, output_file, number_of_example_values)
