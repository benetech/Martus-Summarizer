#! /usr/bin/env python
# -*- coding: utf-8 -*-

def html_tag(tag_name, content, **attributes):
    if content == None:
        content = ""
        
    # Handle special attribute "klass", which is used because "class" is a python reserved word
    if "klass" in attributes:
        attributes['class'] = attributes['klass']
        del attributes['klass']
        
    if attributes:
       att_string = " " + ", ".join([ '%s="%s"' % (att, val)
                                      for (att,val) in attributes.iteritems() ])
    else:
        att_string = ""
    return '<%s%s>%s</%s>' % (tag_name, att_string, content, tag_name)
 
 
def tag_function(tag_name):
    def func(content = None, **atts):
        return html_tag(tag_name, content, **atts)
    return func
 
td = tag_function('td')
tr = tag_function('tr')
h1 = tag_function('h1')
h2 = tag_function('h2')
h3 = tag_function('h3')
p = tag_function('p')
center = tag_function('center')
span = tag_function('span')
div = tag_function('div')
a = tag_function('a')
table = tag_function('table')
tbody = tag_function('tbody')


def make_table(cells, **table_attributes):
    """ cells should be a sequence of sequence of strings, each of which
        will become a toble cell """
    make_row = lambda row: '\t' + tr(''.join([ td(cell) for cell in row ]))
    content = '\n' + '\n'.join( map(make_row, cells) ) + '\n'
    return table(content, **table_attributes)
    
def alternating_rowstyle_generator():
    last_style = "row even"
    while True:
        if last_style == "row even":
            yield "row odd"
            last_style = "row odd"
        else:
            yield "row even"
            last_style = "row even"
        
alternating_row_styles = alternating_rowstyle_generator()
     
# utility function for neat little bar chart
def make_chart(width_string):
    bar_html = ""
    if '.' in width_string:
        width_string = width_string.split('.')[0]
        width_string +=  '%'
    if  width_string != '0%':
        bar_html += td(klass="bar_left", width=width_string)
    if  width_string != '100%':
        bar_html += td()
    return table(klass="bar_table", border="1",
                 cellpadding="0", cellspacing="0",
                 content = tbody(tr(bar_html)))
    

css_style_block = """
<style type="text/css">
    h1 { text-align: center }
    h2 { text-align: center }
    
    .even { background-color: rgb(220,220,220); }
    .odd { background-color: rgb(200,200,200); }

    .bar_table {  height: 15px; width: 80px; background-color: white;}
    .bar_left { background-color: rgb(153, 255, 153); }
    table { border-collapse: collapse; }
</style>
"""
