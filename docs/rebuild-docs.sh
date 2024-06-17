#!/bin/bash
#  Copyright (C) 2020 Michel Gokan Khan
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along
#  with this program; if not, write to the Free Software Foundation, Inc.,
#  51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
#  This file is a part of the PerfSim project, which is now open source and available under the GPLv2.
#  Written by Michel Gokan Khan, February 2020

# Make sure to install sphinx before rebuilding (https://www.sphinx-doc.org/en/master/usage/installation.html)

ROOTPATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && cd ../ && pwd -P )"
echo "$ROOTPATH"
rm -Rf $ROOTPATH/docs/*.rst
#ROOTPATH="$(echo "$ROOTPATH" | sed 's/ /\\ /g')"
#echo "$ROOTPATH"
#rm $(echo "$ROOTPATH" | sed 's/ /\ /g')/docs/*.rst
#rm ${rst}
#sphinx-apidoc -F -o $ROOTPATH/docs $ROOTPATH/perfsim/ --templatedir=$ROOTPATH/docs/_templates/ $ROOTPATH/tests/
sphinx-apidoc -F -o $ROOTPATH/docs $ROOTPATH/perfsim/ $ROOTPATH/tests/ --templatedir=$ROOTPATH/docs/_templates/

cd $ROOTPATH/docs/
make clean
make html
#make latexpdf

cp $ROOTPATH/PRIVACY $ROOTPATH/docs/_build/html/privacy-policy

cp $ROOTPATH/docs/_static/logo/perfsim-logo-dark.png $ROOTPATH/docs/_build/html/_static/perfsim-logo-dark.png

python $ROOTPATH/docs/replace_marker_in_html.py $ROOTPATH/docs/_build/html/index.html
