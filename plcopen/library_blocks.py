#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of the OpenPLC xml2st transpiler.
#
# It reads block signatures that an upstream tool (e.g. openplc-editor)
# embeds in the project's PLCopen XML, so xml2st can type the temporary
# variables it generates for FUNCTION outputs WITHOUT bundling any block
# library of its own.  xml2st therefore stays library-agnostic: everything
# it needs to transpile a project travels inside the project file.
#
# Payload location (PLCopen TC6 vendor-extension point, schema-valid):
#
#   <project>
#     ...
#     <addData>
#       <data name="openplc.org/xml2st/library-blocks" handleUnknown="discard">
#         <libraryBlocks>
#           <pou name="CURRENT_DT" pouType="function">
#             <interface><returnType><DT/></returnType></interface>
#           </pou>
#           <pou name="ADD" pouType="function" extensible="true">
#             <interface>
#               <returnType><ANY_NUM/></returnType>
#               <inputVars>
#                 <variable name="IN1"><type><ANY_NUM/></type></variable>
#                 <variable name="IN2"><type><ANY_NUM/></type></variable>
#               </inputVars>
#             </interface>
#           </pou>
#           ...
#         </libraryBlocks>
#       </data>
#     </addData>
#   </project>
#
# Definitions use standard PLCopen <pou> interface elements (the same shape the
# editor already serialises for user POUs), plus one xml2st-specific attribute,
# `extensible`, marking variadic functions (ADD, AND, OR, ...).  Generic IEC
# meta-types (ANY, ANY_NUM, ...) are preserved verbatim — xml2st resolves them
# from the wired connections exactly as it does for any library block.

from lxml import etree

#: `name` attribute identifying our payload inside <addData>/<data>.
LIBRARY_BLOCKS_DATA_NAME = "openplc.org/xml2st/library-blocks"


def _local(elem):
    """Local (namespace-stripped) tag name of an element."""
    return etree.QName(elem.tag).localname


def _type_name(type_elem):
    """Return the IEC type string carried by a <type> element.

    Mirrors plcopen._getvariableTypeinfos: a base type is the child tag name
    upper-cased (<INT/> -> "INT"), a derived type is its `name` attribute.
    """
    for child in type_elem:
        if _local(child) == "derived":
            return child.get("name")
        return _local(child).upper()
    return "ANY"


def _section_vars(interface, section):
    """[(name, type, 'none'), ...] for variables under interface/<section>."""
    result = []
    for sec in interface:
        if _local(sec) != section:
            continue
        for var in sec:
            if _local(var) != "variable":
                continue
            var_type = "ANY"
            for child in var:
                if _local(child) == "type":
                    var_type = _type_name(child)
                    break
            result.append((var.get("name"), var_type, "none"))
    return result


def _return_type(interface):
    for child in interface:
        if _local(child) == "returnType":
            return _type_name(child)
    return None


def _pou_to_block_infos(pou):
    """Convert a library <pou> element into an xml2st block_infos dict."""
    interface = next((c for c in pou if _local(c) == "interface"), None)

    inputs, outputs, inouts = [], [], []
    if interface is not None:
        inputs = _section_vars(interface, "inputVars")
        outputs = _section_vars(interface, "outputVars")
        inouts = _section_vars(interface, "inOutVars")
        return_type = _return_type(interface)
        if return_type is not None:
            outputs = [("OUT", return_type, "none")] + outputs

    # IN_OUT parameters appear on both sides, matching the convention the
    # generator relies on to detect inout pins (PLCGenerator.GenerateBlock).
    inputs = inputs + inouts
    outputs = outputs + inouts

    desc = {
        "name": pou.get("name"),
        "type": pou.get("pouType") or "function",
        "extensible": (pou.get("extensible") or "").lower() == "true",
        "inputs": inputs,
        "outputs": outputs,
        "comment": "",
    }
    desc["usage"] = "\n (%s) => (%s)" % (
        ", ".join("%s:%s" % (i[1], i[0]) for i in desc["inputs"]),
        ", ".join("%s:%s" % (o[1], o[0]) for o in desc["outputs"]),
    )
    return desc


def extract_library_blocks(xml_file_path):
    """Return block_infos for every block embedded in the project's
    library-blocks payload, or [] when none is present.

    Parses leniently and never raises: a malformed/absent payload simply
    yields no extra blocks, leaving xml2st's normal (permissive) behaviour
    untouched.
    """
    try:
        root = etree.parse(xml_file_path).getroot()
    except Exception:
        return []

    blocks = []
    for data in root.iter():
        if _local(data) != "data" or data.get("name") != LIBRARY_BLOCKS_DATA_NAME:
            continue
        for container in data:
            if _local(container) != "libraryBlocks":
                continue
            for pou in container:
                if _local(pou) == "pou" and pou.get("name"):
                    blocks.append(_pou_to_block_infos(pou))
    return blocks
