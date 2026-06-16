#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of Beremiz, a Integrated Development Environment for
# programming IEC 61131-3 automates supporting plcopen standard and CanFestival.
#
# Copyright (C) 2007: Edouard TISSERANT and Laurent BESSARD
#
# See COPYING file for copyrights details.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.


import re
from collections import OrderedDict

from .definitions import *

TypeHierarchy = dict(TypeHierarchy_list)


def IsOfType(type, reference):
    """
    Returns true if the given data type is the same that "reference" meta-type or one of its types.
    """
    if reference is None:
        return True
    elif type == reference:
        return True
    else:
        parent_type = TypeHierarchy[type]
        if parent_type is not None:
            return IsOfType(parent_type, reference)
    return False


def GetSubTypes(type):
    """
    Returns list of all types that correspont to the ANY* meta type
    """
    return [
        typename
        for typename, _parenttype in list(TypeHierarchy.items())
        if not typename.startswith("ANY") and IsOfType(typename, type)
    ]


DataTypeRange = dict(DataTypeRange_list)

"""
Ordered list of common Function Blocks defined in the IEC 61131-3
Each block have this attributes:
    - "name" : The block name
    - "type" : The block type. It can be "function", "functionBlock" or "program"
    - "extensible" : Boolean that define if the block is extensible
    - "inputs" : List of the block inputs
    - "outputs" : List of the block outputs
    - "comment" : Comment that will be displayed in the block popup
    - "generate" : Method that generator will call for generating ST block code
Inputs and outputs are a tuple of characteristics that are in order:
    - The name
    - The data type
    - The default modifier which can be "none", "negated", "rising" or "falling"
"""

# xml2st no longer bundles a block library.  It is library-agnostic: the
# signatures of every block a project uses are embedded in the project's
# PLCopen XML (see plcopen/library_blocks.py) and registered per-compile via
# PLCControler.RegisterLibraryBlocks.  Any block still unknown at generation
# time degrades to PLCGenerator.SynthesizePermissiveBlockInfos.  These names
# are kept (empty) because other modules import them.
StdBlckLibs = {}
StdBlckLst = []

# -------------------------------------------------------------------------------
#                             Test identifier
# -------------------------------------------------------------------------------

IDENTIFIER_MODEL = re.compile(
    "(?:%(letter)s|_(?:%(letter)s|%(digit)s))(?:_?(?:%(letter)s|%(digit)s))*$"
    % {"letter": "[a-zA-Z]", "digit": "[0-9]"}
)


def TestIdentifier(identifier):
    """
    Test if identifier is valid
    """
    return IDENTIFIER_MODEL.match(identifier) is not None



# Dictionary to speedup block type fetching by name
StdBlckDct = OrderedDict()

for section in StdBlckLst:
    for desc in section["list"]:
        words = desc["comment"].split('"')
        if len(words) > 1:
            desc["comment"] = words[1]
        desc["usage"] = "\n (%s) => (%s)" % (
            ", ".join(["%s:%s" % (input[1], input[0]) for input in desc["inputs"]]),
            ", ".join(["%s:%s" % (output[1], output[0]) for output in desc["outputs"]]),
        )
        BlkLst = StdBlckDct.setdefault(desc["name"], [])
        BlkLst.append((section["name"], desc))

# -------------------------------------------------------------------------------
#                            Languages Keywords
# -------------------------------------------------------------------------------

# Keywords for Pou Declaration
POU_BLOCK_START_KEYWORDS = ["FUNCTION", "FUNCTION_BLOCK", "PROGRAM"]
POU_BLOCK_END_KEYWORDS = ["END_FUNCTION", "END_FUNCTION_BLOCK", "END_PROGRAM"]
POU_KEYWORDS = (
    ["EN", "ENO", "F_EDGE", "R_EDGE"]
    + POU_BLOCK_START_KEYWORDS
    + POU_BLOCK_END_KEYWORDS
)
for category in StdBlckLst:
    for block in category["list"]:
        if block["name"] not in POU_KEYWORDS:
            POU_KEYWORDS.append(block["name"])


# Keywords for Type Declaration
TYPE_BLOCK_START_KEYWORDS = ["TYPE", "STRUCT"]
TYPE_BLOCK_END_KEYWORDS = ["END_TYPE", "END_STRUCT"]
TYPE_KEYWORDS = (
    ["ARRAY", "OF", "T", "D", "TIME_OF_DAY", "DATE_AND_TIME"]
    + TYPE_BLOCK_START_KEYWORDS
    + TYPE_BLOCK_END_KEYWORDS
)
TYPE_KEYWORDS.extend(
    [keyword for keyword in list(TypeHierarchy.keys()) if keyword not in TYPE_KEYWORDS]
)


# Keywords for Variable Declaration
VAR_BLOCK_START_KEYWORDS = [
    "VAR",
    "VAR_INPUT",
    "VAR_OUTPUT",
    "VAR_IN_OUT",
    "VAR_TEMP",
    "VAR_EXTERNAL",
]
VAR_BLOCK_END_KEYWORDS = ["END_VAR"]
VAR_KEYWORDS = (
    ["AT", "CONSTANT", "RETAIN", "NON_RETAIN"]
    + VAR_BLOCK_START_KEYWORDS
    + VAR_BLOCK_END_KEYWORDS
)


# Keywords for Configuration Declaration
CONFIG_BLOCK_START_KEYWORDS = [
    "CONFIGURATION",
    "RESOURCE",
    "VAR_ACCESS",
    "VAR_CONFIG",
    "VAR_GLOBAL",
]
CONFIG_BLOCK_END_KEYWORDS = ["END_CONFIGURATION", "END_RESOURCE", "END_VAR"]
CONFIG_KEYWORDS = (
    ["ON", "PROGRAM", "WITH", "READ_ONLY", "READ_WRITE", "TASK"]
    + CONFIG_BLOCK_START_KEYWORDS
    + CONFIG_BLOCK_END_KEYWORDS
)

# Keywords for Structured Function Chart
SFC_BLOCK_START_KEYWORDS = ["ACTION", "INITIAL_STEP", "STEP", "TRANSITION"]
SFC_BLOCK_END_KEYWORDS = ["END_ACTION", "END_STEP", "END_TRANSITION"]
SFC_KEYWORDS = ["FROM", "TO"] + SFC_BLOCK_START_KEYWORDS + SFC_BLOCK_END_KEYWORDS


# Keywords for Instruction List
IL_KEYWORDS = [
    "TRUE",
    "FALSE",
    "LD",
    "LDN",
    "ST",
    "STN",
    "S",
    "R",
    "AND",
    "ANDN",
    "OR",
    "ORN",
    "XOR",
    "XORN",
    "NOT",
    "ADD",
    "SUB",
    "MUL",
    "DIV",
    "MOD",
    "GT",
    "GE",
    "EQ",
    "NE",
    "LE",
    "LT",
    "JMP",
    "JMPC",
    "JMPCN",
    "CAL",
    "CALC",
    "CALCN",
    "RET",
    "RETC",
    "RETCN",
]


# Keywords for Structured Text
ST_BLOCK_START_KEYWORDS = ["IF", "ELSIF", "ELSE", "CASE", "FOR", "WHILE", "REPEAT"]
ST_BLOCK_END_KEYWORDS = ["END_IF", "END_CASE", "END_FOR", "END_WHILE", "END_REPEAT"]
ST_KEYWORDS = (
    [
        "TRUE",
        "FALSE",
        "THEN",
        "OF",
        "TO",
        "BY",
        "DO",
        "DO",
        "UNTIL",
        "EXIT",
        "RETURN",
        "NOT",
        "MOD",
        "AND",
        "XOR",
        "OR",
    ]
    + ST_BLOCK_START_KEYWORDS
    + ST_BLOCK_END_KEYWORDS
)

# All the keywords of IEC
IEC_BLOCK_START_KEYWORDS = []
IEC_BLOCK_END_KEYWORDS = []
IEC_KEYWORDS = ["E", "TRUE", "FALSE"]
for all_keywords, keywords_list in [
    (
        IEC_BLOCK_START_KEYWORDS,
        [
            POU_BLOCK_START_KEYWORDS,
            TYPE_BLOCK_START_KEYWORDS,
            VAR_BLOCK_START_KEYWORDS,
            CONFIG_BLOCK_START_KEYWORDS,
            SFC_BLOCK_START_KEYWORDS,
            ST_BLOCK_START_KEYWORDS,
        ],
    ),
    (
        IEC_BLOCK_END_KEYWORDS,
        [
            POU_BLOCK_END_KEYWORDS,
            TYPE_BLOCK_END_KEYWORDS,
            VAR_BLOCK_END_KEYWORDS,
            CONFIG_BLOCK_END_KEYWORDS,
            SFC_BLOCK_END_KEYWORDS,
            ST_BLOCK_END_KEYWORDS,
        ],
    ),
    (
        IEC_KEYWORDS,
        [
            POU_KEYWORDS,
            TYPE_KEYWORDS,
            VAR_KEYWORDS,
            CONFIG_KEYWORDS,
            SFC_KEYWORDS,
            IL_KEYWORDS,
            ST_KEYWORDS,
        ],
    ),
]:
    for keywords in keywords_list:
        all_keywords.extend(
            [keyword for keyword in keywords if keyword not in all_keywords]
        )
