#!./venv/bin/python3
# -*- coding: utf-8 -*-
# vim: set file encoding=utf-8 :
#
# file: 'declination.py'
# Part of ___, ____.

# Copyright 2015 Alex Kleider
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#   Look for file named COPYING.
"""

Usage:
    declination.py -h | --version
    declination.py [options]

Options:
    -h --help  Print usage statement.
    --version  Print version.
    -i INFILE --infile=INFILE   Input file
    -o OUTFILE --outfile=OUTFILE   Output file

This is being done in a virtual environment with Python 3.
Non standard libraries used: 'docopt' and 'requests':
see accompanying file 'requirements.txt'.
Thanks to Aaron Borden who helped me with the HTTP part. 
"""
# import library modules
import sys
from docopt import docopt
import requests
# metadata such as version number
VERSION = "0.0.0"
# other constants
COMMENT_INDICATOR = '#'
SITE = (  # If this changes, line_array2dict() 
          # will likely need to be changed.
"http://www.ngdc.noaa.gov/geomag-web/calculators/calculateDeclination")
# global variables
n_FIELDS = 8  # With 7 fields, could get the declination.
              # The 8th field provides grid North offset
              # which is needed to calculate declination re grid.
test_line = (
"2015 08 28  63 375  96 15  -2.46")

# custom exception types
# private functions and classes
# public functions and classes

def line2array(line):
    """Takes a line of input and tries to return a dictionary.
    Returns None if line is a comment line.
    Returns an error string if format can not be interpreted.
    """
    stripped_line = line.strip()
    if stripped_line:
        if stripped_line[0] == COMMENT_INDICATOR:
            return
        parts = stripped_line.split()
        if len(parts) < n_FIELDS:
            return 'Error: Bad input line.'
        return parts

def line_array2dict(line_array):
    """Parameter is an array of items from an input line.
    If successful, returns a dictionary containing keys needed by the
    request to be sent to SITE as well as those needed to format the
    output, otherwise returns an error string.
    The parameter is expected to be generated from an input
    line by the client function (line2dict.)"""
    try:
        ret = dict(
             lat_d = line_array[3],  # Latitude degrees
             lat_m = line_array[4],  # Latitude minutes
             lon_d = line_array[5],  # Longitude degrees
             lon_m = line_array[6],  # Longitude minutes
             grid_offset = float(line_array[7]),
             # The following are used to format the http request.
             lat1 = float(line_array[3]) + float(line_array[4])/60,
             lon1 = float(line_array[5]) + float(line_array[6])/60,
             lat1Hemisphere='N',
             lon1Hemisphere='W',
             ajaz='true',
             resultFormat='csv',
             startYear = line_array[0],
             startDay = line_array[2],
             startMonth = line_array[1],
             grid='on'
              )
    except ValueError:
        return (
    'Error: Probably could not convert degrees &/or minutes into float.')
    return ret

def response_array2dict(response_array):            
    """<response_array> is an array created by spliting the relevant
    line of output coming from the website.
    Returns a suitable dictionary."""
    return dict(   
            decimal_year=float(response_array[0]),
            latitude=float(response_array[1]),
            longitude=-float(response_array[2]),  # East is least, ...
            elevation=float(response_array[3]),
            declination=float(response_array[4]),
            decl_sv=float(response_array[5]),
            decl_uncertainty=float(response_array[6]),
            )

def response2dict(response):
    lines = response.split('\n')
    data_line = lines[-2]
    data = data_line.split(',')
    return response_array2dict(data)

def processed_line(in_dict, out_dict):
    """Desired output is of the form:
2015 08 01  64 12  95 45  2.02 | 2015.xxx  64.xx 95.xx  x.xx | x.xx
 ^    ^  ^   ^  ^   ^  ^   ^      ^         ^     ^       ^      ^
year mo day  ^  ^   ^  ^   ^      ^         ^     ^       ^      ^
    Lat degree/min  ^  ^   ^      ^         ^     ^       ^      ^
        Long degree/min    ^      ^         ^     ^       ^      ^
                   grid offset | Decimal yr ^     ^       ^      ^
                                decimal latitude  ^       ^      ^
                                      decimal longitude   ^      ^
                                                  declination    ^
                                                    grid declination
"""
    return (' '.join((
"{0[startYear]:<4}-{0[startMonth]:0>2}-{0[startDay]:0>2}",
"{0[lat_d]}\N{Degree sign} {0[lat_m]}\N{PRIME}",
"{0[lon_d]}\N{Degree sign} {0[lon_m]}\N{PRIME}",
"{0[grid_offset]:>6.3f} |",
"{1[decimal_year]:.3f} {1[latitude]:>6.3f}\N{Degree sign}",
"{1[longitude]:>6.3f}\N{Degree sign}",
"{1[declination]:.3f} {2:.3f}\N{Degree sign}",))
        .format(in_dict, out_dict,
                out_dict['declination'] - in_dict['grid_offset']))

def process_inputfile_object(input_file_object, output_array):
    """First parameter is a file object which can be read.
    The second param is a collector of ouput lines.
    """
    for line in input_file_object:
        line_array = line2array(line)
        if (line_array == None            # Comment line.
        or isinstance(line_array, str)):  # Error report.
            if line_array:              
                output_array.append(
                # Adding a line to announce the error report.
                "#! The following line is malformed:")
            output_array.append(line[:-1]) # Reported either way.
        elif isinstance(line_array, list):
            # Data to process
            source_dict = line_array2dict(line_array)
            retrieved_dict = get_response_dict(source_dict) 
            output_line = processed_line(source_dict, retrieved_dict)
            output_array.append(output_line)
        else:
            print("DEAD CODE BEING RUN!")
            sys.exit(1)

def get_response_dict(source_dict):
    """Returns the web response in dictionary format.
    Parameter is a dictionary created from an input line.
    """
    r = requests.get(SITE, params=source_dict)
    return response2dict(r.text)

def test():
    line_array = line2array(test_line)
    payload = line_array2dict(line_array)
    if isinstance(payload, dict):
        r = requests.get(SITE, params=payload)
        print(r.url)
        print(r.text)
        print("Response is of type {}.".format(type(r.text)))
        print(response2dict(r.text))
    elif isinstance(payload,str):
        # An error is being reported:
        print(payload)
    elif payload == None:
        print("'payload' is a comment.")
    else:
        print("This should be dead code.")

def get_output(args):
    """Parameter is output of docopt's interpretation of the
    commandline parameters.  Output is a single string.
    This function reads from the input file, gets declination
    from the web and then generates the output.
    """
    output_array = []
    if args["--infile"]:
        with open(args['--infile'], 'r') as infile:
            process_inputfile_object(infile, output_array)
    else:
        with sys.stdin as infile:
            process_inputfile_object(infile, output_array)
    return '\n'.join(output_array)

# main function
def main():
    args = docopt(__doc__, version = VERSION)
    print(args)
    output = ("   DATE    Latit   Longit    grid    decDate" + 
                "  decLat  decLong  Decl  gridDec" +
                get_output(args) + '\n')
    if args["--outfile"]:
        with open(args['--outfile'], 'w') as outfile:
            outfile.write(output)
    else:
#       print(output)
        with sys.stdout as outfile:
            outfile.write(output)
    


if __name__ == '__main__':  # code block to run the application
    main()


