#!/usr/bin/env python
"""
Creates pdb data files from lammps data files, given a template pdb file.
"""

from __future__ import print_function
import os
import copy
import re
import sys
import argparse
from nrel_tools.common import (InvalidDataError, warning, process_cfg, create_out_fname, list_to_file, process_pdb_tpl,
                               HEAD_CONTENT, ATOMS_CONTENT, TAIL_CONTENT, PDB_FORMAT, NUM_ATOMS, ATOM_NUM_DICT,
                               GOOD_RET, INPUT_ERROR, IO_ERROR, INVALID_DATA, silent_remove)

try:
    # noinspection PyCompatibility
    from ConfigParser import ConfigParser, MissingSectionHeaderError
except ImportError:
    # noinspection PyCompatibility
    from configparser import ConfigParser, MissingSectionHeaderError

__author__ = 'hmayes'


# Constants #

# Config File Sections
MAIN_SEC = 'main'

# Config keys
PDB_TPL_FILE = 'pdb_tpl_file'
GAUSSLOG_FILES_FILE = 'gausslog_list_file'
GAUSSLOG_FILES = 'gausslog_files_list'
GAUSSLOG_FILE = 'gausslog_file'
ONLY_FINAL = 'only_final_coords'
OUT_BASE_DIR = 'output_directory'
OUTFILE_NAME = 'output_file_name'
COMBINE_LOGS = 'combine_logs'

GAU_COORD_PAT = re.compile(r"Center     Atomic      Atomic             Coordinates.*")
GAU_SEP_PAT = re.compile(r"---------------------------------------------------------------------.*")
GAU_E_PAT = re.compile(r"SCF Done:.*")

# data file info

# Defaults
DEF_CFG_FILE = 'gausslog2pdb.ini'
# Set notation
DEF_CFG_VALS = {GAUSSLOG_FILES_FILE: 'gausslog_list.txt',
                OUT_BASE_DIR: None,
                GAUSSLOG_FILE: None,
                PDB_TPL_FILE: None,
                ONLY_FINAL: False,
                OUTFILE_NAME: None,
                COMBINE_LOGS: False,
                }
REQ_KEYS = {
            }

# For log file processing
SEC_HEAD = 'head_section'
SEC_ATOMS = 'atoms_section'
SEC_TAIL = 'tail_section'


def read_cfg(f_loc, cfg_proc=process_cfg):
    """
    Reads the given configuration file, returning a dict with the converted values supplemented by default values.

    :param f_loc: The location of the file to read.
    :param cfg_proc: The processor to use for the raw configuration values.  Uses default values when the raw
        value is missing.
    :return: A dict of the processed configuration file's data.
    """
    config = ConfigParser()
    good_files = config.read(f_loc)

    if not good_files:
        raise IOError('Could not read file {}'.format(f_loc))
    main_proc = cfg_proc(dict(config.items(MAIN_SEC)), DEF_CFG_VALS, REQ_KEYS)

    # To fix; have this as default!
    main_proc[GAUSSLOG_FILES] = []
    if os.path.isfile(main_proc[GAUSSLOG_FILES_FILE]):
        with open(main_proc[GAUSSLOG_FILES_FILE]) as f:
            for data_file in f:
                main_proc[GAUSSLOG_FILES].append(data_file.strip())
    if main_proc[GAUSSLOG_FILE] is not None:
        main_proc[GAUSSLOG_FILES].append(main_proc[GAUSSLOG_FILE])
    if len(main_proc[GAUSSLOG_FILES]) == 0:
        raise InvalidDataError("No files to process: no '{}' specified and "
                               "no list of files found for: {}".format(GAUSSLOG_FILE, main_proc[GAUSSLOG_FILES_FILE]))
    if main_proc[COMBINE_LOGS] and not main_proc[OUTFILE_NAME]:
        raise InvalidDataError("When combining outputs from multiple log files into one pdb, specify the output "
                               "file name")
    if main_proc[COMBINE_LOGS] and not main_proc[ONLY_FINAL]:
        warning("When combining outputs from multiple log files into one pdb, only the last coordinates of each "
                "log file will be kept.")
        main_proc[ONLY_FINAL] = True
    return main_proc


def parse_cmdline(argv):
    """
    Returns the parsed argument list and return code.
    `argv` is a list of arguments, or `None` for ``sys.argv[1:]``.
    """
    if argv is None:
        argv = sys.argv[1:]

    # initialize the parser object:
    parser = argparse.ArgumentParser(description='Creates pdb files from Gaussian input files, given a template pdb '
                                                 'file.')
    parser.add_argument("-c", "--config", help="The location of the configuration file in ini format. "
                                               "The default file name is {}, located in the "
                                               "base directory where the program as run.".format(DEF_CFG_FILE),
                        default=DEF_CFG_FILE, type=read_cfg)
    args = None
    try:
        args = parser.parse_args(argv)
    except IOError as e:
        warning("Problems reading file:", e)
        parser.print_help()
        return args, IO_ERROR
    except (KeyError, InvalidDataError, MissingSectionHeaderError, SystemExit) as e:
        if hasattr(e, 'code') and e.code == 0:
            return args, GOOD_RET
        warning(e)
        parser.print_help()
        return args, INPUT_ERROR

    return args, GOOD_RET


def process_gausscom_files(cfg, pdb_tpl_content):
    if cfg[COMBINE_LOGS]:
        f_name = create_out_fname(cfg[OUTFILE_NAME], ext='.pdb', base_dir=cfg[OUT_BASE_DIR])
        silent_remove(f_name)
    for gausslog_file in cfg[GAUSSLOG_FILES]:
        if not cfg[PDB_TPL_FILE]:
            pdb_tpl_content[HEAD_CONTENT] = ["TITLE     {}".format(gausslog_file)]
            pdb_tpl_content[TAIL_CONTENT] = ["END"]
        if not cfg[COMBINE_LOGS]:
            if cfg[OUTFILE_NAME]:
                out_name = cfg[OUTFILE_NAME]
            else:
                out_name = gausslog_file
            f_name = create_out_fname(out_name, ext='.pdb', base_dir=cfg[OUT_BASE_DIR])
        process_gausslog_file(cfg, gausslog_file, pdb_tpl_content, f_name)


def process_gausslog_file(cfg, gausslog_file, pdb_tpl_content, f_name):
    with open(gausslog_file) as d:
        section = SEC_HEAD
        atom_id = 0
        lines_after_coord = 2  # blank line, description, blank line, charge & multiplicity
        if cfg[COMBINE_LOGS]:
            mode = 'a'
        else:
            mode = 'w'
        message = True
        coord_match = False
        first_pass = True

        for line in d:
            line = line.strip()
            if len(line) == 0:
                continue
            # not currently keeping anything from the header
            if section == SEC_HEAD:
                if GAU_COORD_PAT.match(line):
                    coord_match = True
                    if cfg[PDB_TPL_FILE]:
                        pdb_data_section = copy.deepcopy(pdb_tpl_content[ATOMS_CONTENT])
                    else:
                        pdb_data_section = []
                    continue
                elif coord_match and lines_after_coord > 0:
                    lines_after_coord -= 1
                    if lines_after_coord == 0:
                        section = SEC_ATOMS
                    continue

            elif section == SEC_ATOMS:
                if GAU_SEP_PAT.match(line):
                    section = SEC_TAIL
                    continue

                split_line = line.split()

                try:
                    atom_type = ATOM_NUM_DICT[int(split_line[1])]
                except KeyError:
                    raise InvalidDataError("Currently, this code only expects atom numbers up to 36 (Kr), and the "
                                           "atomic number read was {}. Update the code to use this with your current "
                                           "output.".format(split_line[1]))
                # if working from a template, check atom type
                if cfg[PDB_TPL_FILE]:
                    pdb_atom_type = pdb_data_section[atom_id][8].split(' ')[-1]
                    if atom_type != pdb_atom_type:
                        warning("Atom types do not match for atom number {}; pdb atom type is {} while gausscom type "
                                "is {}".format(atom_id, pdb_atom_type, atom_type))
                else:
                    pdb_data_section.append(atom_id)
                    pdb_data_section[atom_id] = ['HETATM', '{:5d}'.format(atom_id+1), '  {:4}'.format(atom_type),
                                                 'UNL  ', 1, 0.0, 0.0, 0.0, '  1.00  0.00           '+atom_type]
                pdb_data_section[atom_id][5:8] = map(float, split_line[3:6])
                atom_id += 1
            elif section == SEC_TAIL:
                if GAU_E_PAT.match(line):
                    if first_pass:
                        first_pass = False
                    else:
                        del pdb_tpl_content[HEAD_CONTENT][-1]
                    pdb_tpl_content[HEAD_CONTENT].append("REMARK    {}".format(line))
                    section = SEC_HEAD
                    coord_match = False
                    atom_id = 0
                    lines_after_coord = 2

                    if not cfg[ONLY_FINAL]:
                        list_to_file(pdb_tpl_content[HEAD_CONTENT] + pdb_data_section + pdb_tpl_content[TAIL_CONTENT],
                                     f_name, list_format=PDB_FORMAT, mode=mode, print_message=message)
                        message = False
                        mode = 'a'

    if cfg[ONLY_FINAL]:
        list_to_file(pdb_tpl_content[HEAD_CONTENT] + pdb_data_section + pdb_tpl_content[TAIL_CONTENT],
                     f_name, list_format=PDB_FORMAT, mode=mode, print_message=message)

    # Now that finished reading the file, first make sure didn't  exit before reaching the desired number of atoms
    if cfg[PDB_TPL_FILE]:
        if atom_id != pdb_tpl_content[NUM_ATOMS]:
            raise InvalidDataError('In gausscom file: {}\n'
                                   '  found {} atoms, but pdb expects {} atoms'.format(gausslog_file, atom_id,
                                                                                       pdb_tpl_content[NUM_ATOMS]))


def main(argv=None):
    # Read input
    args, ret = parse_cmdline(argv)
    if ret != GOOD_RET or args is None:
        return ret

    cfg = args.config

    # Read template and data files
    try:
        if cfg[PDB_TPL_FILE]:
            pdb_tpl_content = process_pdb_tpl(cfg[PDB_TPL_FILE])
        else:
            pdb_tpl_content = {}
        process_gausscom_files(cfg, pdb_tpl_content)
    except IOError as e:
        warning("Problems reading file:", e)
        return IO_ERROR
    except InvalidDataError as e:
        warning("Problems reading data:", e)
        return INVALID_DATA

    return GOOD_RET  # success


if __name__ == '__main__':
    status = main()
    sys.exit(status)