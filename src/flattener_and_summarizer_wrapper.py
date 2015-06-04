# $Id: flattener_and_summarizer_wrapper.py 3476 2012-04-25 18:33:55Z jeffk $
#
# Authors:     Jeff Klingner
# Maintainers: Jeff Klingner
# Copyright:   2011, Benetech, GPL v2 or later
# ============================================

__all__ = ['go', 'UserCorrectableError']

# To ensure portability, start by nuking the search path, so that only local libraries
# plus the standard location can be loaded.
import sys
sys.path = [p for p in sys.path if 'data-projects' not in p]
# sys.path.append()

import tempfile
import os.path
import shutil

from martus2csv import run_flattener
from dsv_summarizer import run_summarizer

class UserCorrectableError(Exception):
    def __init__(self, descrip):
        self.descrip = descrip
        super(UserCorrectableError, self).__init__(descrip)


def go(input_xml_filename,
       output_html_directory,
       include_csv_output,
       output_csv_directory,
       num_example_values):
    
    # Verify that the input file exists and has the right type.
    if input_xml_filename == '':
        raise UserCorrectableError("No input file selected.")

    if not os.path.exists(input_xml_filename):
        raise UserCorrectableError("Input file %s doesn't exist." % input_xml_filename)

    if not input_xml_filename.endswith(".xml"):
        raise UserCorrectableError("Chosen input file is not an XML file.")
        
    if output_html_directory == '':
        raise UserCorrectableError("No HTML output directory selected.")

    if not os.path.exists(output_html_directory):
        raise UserCorrectableError("HTML output directory %s doesn't exist." % output_html_directory)

    if include_csv_output and not os.path.exists(output_csv_directory):
        raise UserCorrectableError("CSV output directory %s doesn't exist." % output_html_directory)

    # Derive the stem that will be used to name the flatfiles, and therefore
    # the html summaries.
    basename = os.path.basename(input_xml_filename)
    stem_name = os.path.splitext(basename)[0]
    
    # We need a temporary directory to write the flattened data CSV files into.
    temp_flatfile_dir = tempfile.mkdtemp(prefix="martus_data_summarizer_tempfile_")

    try:
        flattener_output_pathname = os.path.join(temp_flatfile_dir, stem_name)
        # In the future, this can be generalized to run on many xml files or zip files at once.
        run_flattener(input_xml_filename, flattener_output_pathname)
    
        # Get the list of csv files that was created
        flat_csv_files = os.listdir(temp_flatfile_dir)
        assert all(filename.endswith(".csv") for filename in flat_csv_files)
    
        for csv_file in flat_csv_files:
            output_filename = csv_file.replace('.csv', '.summary.html')
            full_input_path = os.path.join(temp_flatfile_dir, csv_file)
            full_html_output_path = os.path.join(output_html_directory, output_filename)
            assert os.path.exists(full_input_path)
            run_summarizer(full_input_path, full_html_output_path, num_example_values)

            if include_csv_output:
                full_csv_output_path = os.path.join(output_csv_directory, csv_file)
                os.rename(full_input_path, full_csv_output_path)

    finally:
        # Delete the temp directory
        shutil.rmtree(temp_flatfile_dir)
