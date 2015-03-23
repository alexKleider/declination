#!/usr/bin/env python3
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
declination.py

Usage:
  declination.py -h | --version
  declination.py -i INPUT -o OUTPUT

Options:
  -h --help  Print this docstring.
  --version  Provide version.
  -i INPUT --input=INPUT  Provide input file INPUT.
  -o OUTPUT --output=OUTPUT Send output to OUTPUT.

Input must consist of individual lines consisting of
whitespace separated fields as follows:
4_digit_year month date lat_\N{Degree sign} lat_' long_\N{Degree sign} long_' grid_offset
The first three fields must be integers.
The next three fields will be interpreted as floats.
Fewer than six fields will result in an error; more will be ignored.
Any line beginning with a '#' will be put back into the output
but will otherwise be ignored.
North Latitude and West Longitude are positive, 
NOTE that with regard to Longitude this is against convention.
This script will NOT work for areas in the Eastern or Southern
hemispheres.  (It could easily be modified to do so: contact the author
if interested: alex at kleider dot ca)

Declination is returned in the last two fields expressed as decimal degrees
first relative to True North, then relative to Grid North.
A negative indicates East, positive West. ("East is least, West is best.")
"""

# import standard library modules
import sys
import shlex
import subprocess
# import custom modules
import docopt
# metadata such as version number
VERSION = "0.0.0"
# other constants
COMMENT_INDICATOR = '#'
n_FIELDS = 8
COMMAND_by_AARON = (' '.join((
"curl -d lat1={0[lat1]} -d lon1={0[lon1]} -d lat1Hemisphere=N -d",
"lon1Hemisphere=W -d ajaz=true -d resultFormat=csv -d",
"startYear={0[year]} -d startDay={0[day]} -d startMonth={0[month]}",
"http://www.ngdc.noaa.gov/geomag-web/calculators/calculateDeclination"
)))

# global variables
# custom exception types
# private functions and classes
# public functions and classes

def get_options():
    return docopt.docopt(__doc__, version=VERSION)

def get_request_dict(line_array):
     """Parameter is an array of items from an input line.
     Returns an appropriate dictionary."""
     return dict(
         lat_d = line_array[3],
         lat_m = line_array[4],
         lat1 = float(line_array[3]) + float(line_array[4])/60,
         lon_d = line_array[5],
         lon_m = line_array[6],
         lon1 = float(line_array[5]) + float(line_array[6])/60,
         year = line_array[0],
         day = line_array[2],
         month = line_array[1],
         grid_offset = float(line_array[7]),
          )

def get_response_dict(response):            
    """<response> is an array created by spliting the relevant
    line of output coming from the website.
    Returns a suitable dictionary."""
    return dict(   
            decimal_year=float(response[0]),
            latitude=float(response[1]),
            longitude=-float(response[2]),  # East is least, ...
#           elevation=float(response[3]),
            declination=float(response[4]),
#           decl_sv=float(response[5]),
#           decl_uncertainty=float(response[6]),
            )

def get_decl(request_dict):
    """Parameter is a dict of the form returned by get_request_dict.
    Return value is provied by get_response_dict after it is provided an
    array version of the relevant line of the response obtained by the
    web site.
    (The relevant data collected from the net is in a line of the form:
    "[2015.54795, 61.1, -101.1, 0.0, 5.52539, -0.10319, 0.68124]"
    b'#   7 Fields:'
    b'#     (1) Date in decimal years'
    b'#     (2) Latitude in decimal Degrees'
    b'#     (3) Longitude in decimal Degrees'
    b'#     (4) Elevation in km GPS'
    b'#     (5) Declination in decimal Degrees'
    b'#     (6) Declination_sv in decimal Degrees'
    b'#     (7) Declination_uncertainty in decimal Degrees'
    """
    cmd = shlex.split(COMMAND_by_AARON.format(request_dict))
    try:
        output = subprocess.check_output(cmd)
    except CalledProcessError as err:
        print("ERROR: return code is {}, \n   Output: {}"
                .format(err.returncode, err.output))
    b_lines = output.split(b'\n')
    data_line = b_lines[-2]
    data = data_line.split(b',')
    return get_response_dict(data)

def format_output(in_dict, out_dict):
    """Desired output is of the form:
2015 08 01  64 12  95 45  2.02 | 2015.xxx  64.xx 95.xx  x.xx | x.xx
year mo day 
    Lat degree/min
        Long degree/min
                   grid offset | Decimal yr
                                decimal latitude
                                      decimal longitude
                                                  declination
                                                    grid declination
"""
    return (' '.join((
"{0[year]:<4}-{0[month]:0>2}-{0[day]:0>2}",
"{0[lat_d]}\N{Degree sign} {0[lat_m]}\N{PRIME}",
"{0[lon_d]}\N{Degree sign} {0[lon_m]}\N{PRIME}",
"{0[grid_offset]:>6.3f} |",
"{1[decimal_year]:.3f} {1[latitude]:>6.3f}\N{Degree sign}",
"{1[longitude]:>6.3f}\N{Degree sign}",
"{1[declination]:.3f} {2:.3f}\N{Degree sign}",))
        .format(in_dict, out_dict,
                out_dict['declination'] - in_dict['grid_offset']))

# main function
def main():
    args = get_options()
    output = []
    with open(args['--input'], 'r') as infile:
        for line in infile:
            stripped_line = line.strip()
            if stripped_line:
                if stripped_line[0] == COMMENT_INDICATOR:
                    output.append(line[:-1])
                    continue
                parts = stripped_line.split()
                if len(parts) < n_FIELDS:
                    output.append(line[:-1] + ' BAD INPUT LINE')
                    continue
                # put date and lat/long into dict
                request_dict = get_request_dict(parts)
                # calculate data
                result_dict = get_decl(request_dict)
                # format and append results
                output.append(format_output(request_dict, result_dict))
            else:
                output.append(line[:-1])
    all_output = '\n'.join(output)
    with open(args['--output'], 'w') as outfile:
        outfile.write(all_output)

if __name__ == '__main__':  # code block to run the application
    print("Running Python3 script: 'declination.py'.......")
    main()



