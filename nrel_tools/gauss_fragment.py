#!/usr/bin/env python
"""
homolytic fragmenter
"""

from __future__ import print_function
import os
import sys
import argparse
import numpy as np
from nrel_tools.common import (InvalidDataError, warning, process_cfg, create_out_fname, list_to_file,
                               GOOD_RET, INPUT_ERROR, IO_ERROR, INVALID_DATA,
                               ATOM_TYPE, ATOM_COORDS, process_gausscom_file,
                               )

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
GAUSSCOM_FILE = 'input_com_or_pdb_file'
OUT_BASE_DIR = 'output_directory'
CUT_ATOMS = 'cut_atoms'
GAUSS_COMMAND = 'gaussian_options_line'
GAUSS_CP_COMMAND = 'gaussian_cp_options_line'

# data file info

# Defaults
DEF_CFG_FILE = 'gausscom_fragment.ini'
DEF_GAUSS_COMMAND = '# m062x/Def2TZVP nosymm scf=xqc opt freq'
DEF_GAUSS_CP_COMMAND = '# m062x/Def2TZVP nosymm Counterpoise=2'

# Set notation
DEF_CFG_VALS = {OUT_BASE_DIR: None,
                GAUSSCOM_FILE: None,
                GAUSS_COMMAND: DEF_GAUSS_COMMAND,
                GAUSS_CP_COMMAND: DEF_GAUSS_CP_COMMAND,
                }
REQ_KEYS = {CUT_ATOMS: str,
            }

# For file processing
CUT_PAIR_LIST = 'cut_pair_list'
SEC_HEAD = 'head_section'
SEC_ATOMS = 'atoms_section'
SEC_TAIL = 'tail_section'
FRAGMENT = 'fragment'
MAX_BOND_DIST = 1.9  # same length units as in input and output file, here Angstroms


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

    cut_pairs = main_proc[CUT_ATOMS].split(';')
    main_proc[CUT_PAIR_LIST] = []
    for pair in cut_pairs:
        if pair == '':
            continue
        atom_pair = [int(x) for x in pair.split(',')]
        if len(atom_pair) != 2:
            raise InvalidDataError("The '{}' values should be sets of two atoms, separated by commas, with each pair "
                                   "separated by ';'".format(CUT_PAIR_LIST))
        main_proc[CUT_PAIR_LIST].append(atom_pair)

    if main_proc[OUT_BASE_DIR]:
        if not os.path.exists(main_proc[OUT_BASE_DIR]):
            os.makedirs(main_proc[OUT_BASE_DIR])

    return main_proc


def parse_cmdline(argv):
    """
    Returns the parsed argument list and return code.
    `argv` is a list of arguments, or `None` for ``sys.argv[1:]``.
    """
    if argv is None:
        argv = sys.argv[1:]

    # initialize the parser object:
    parser = argparse.ArgumentParser(description='Creates cp files from Gaussian input files, given a list of atom '
                                                 'numbers where to cut (list format: atom1, atom2; atom3, atom4.')
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


def calc_dist(a, b):
    return np.linalg.norm(np.subtract(a, b))


def validate_atom_num(atom_pair, atoms_content, gausscom_file):
    # check that both atom numbers are not larger than the total number of atoms,
    # and that they are close enough to be bonded
    for atom_num in atom_pair:
        if atom_num not in atoms_content:
            raise InvalidDataError("Found atom id {} in '{}', but there are only {} atoms in the file {}"
                                   "".format(atom_num, CUT_ATOMS, len(atoms_content), gausscom_file))
    pair_dist = calc_dist(atoms_content[atom_pair[0]][ATOM_COORDS], atoms_content[atom_pair[1]][ATOM_COORDS])
    if pair_dist > MAX_BOND_DIST:
        raise InvalidDataError("Atom ids {} and {} are {:.2f} Angstroms apart, which is greater than the tested "
                               "maximum bond distance of {:.2f}".format(atom_pair[0], atom_pair[1], pair_dist,
                                                                        MAX_BOND_DIST))


def fragment_molecule(atom_pair, atoms_content):
    single_bond_atoms = ['H', 'Cl', ]
    unassigned_atom_numbers = list(range(1, len(atoms_content)+1))
    frag1_list = []
    frag2_list = []
    for atom in atom_pair:
        # Check if fragment made up of just one atom
        lonely_frag = False
        if atoms_content[atom][ATOM_TYPE] == 'O':
            for other_atom in unassigned_atom_numbers:
                lonely_frag = True
                if other_atom == atom_pair[0] or other_atom == atom_pair[1]:
                    continue
                pair_dist = calc_dist(atoms_content[atom][ATOM_COORDS], atoms_content[other_atom][ATOM_COORDS])
                if pair_dist < MAX_BOND_DIST:
                    lonely_frag = False
                    break
        elif atoms_content[atom][ATOM_TYPE] in single_bond_atoms:
            lonely_frag = True
        if lonely_frag:
            atoms_content[atom][FRAGMENT] = 1
            frag1_list.append(atom)
            unassigned_atom_numbers.remove(atom)
            frag2_list = unassigned_atom_numbers
            for other_atom in unassigned_atom_numbers:
                atoms_content[other_atom][FRAGMENT] = 2
            return frag1_list, frag2_list
    # Now the more difficult cases
    frag1_list.append(atom_pair[0])
    unassigned_atom_numbers.remove(atom_pair[0])
    atoms_content[atom_pair[0]][FRAGMENT] = 1
    frag2_list.append(atom_pair[1])
    unassigned_atom_numbers.remove(atom_pair[1])
    atoms_content[atom_pair[1]][FRAGMENT] = 2
    # first add to frag 1
    atoms_to_check = [atom_pair[0]]
    add_atoms_to_fragment(unassigned_atom_numbers, atoms_content, atoms_to_check, frag1_list, 1, single_bond_atoms)
    # make sure no atoms in fragment 1 are within bonding distance of any atoms remaining in the
    # unassigned_atom_numbers list
    for f1_atom in frag1_list:
        for atom in unassigned_atom_numbers:
            pair_dist = calc_dist(atoms_content[atom][ATOM_COORDS], atoms_content[f1_atom][ATOM_COORDS])
            if pair_dist < MAX_BOND_DIST:
                raise InvalidDataError("Found that atom {} assigned to fragment 1 is within {} Angstroms of atom {} "
                                       "which was not assigned to fragment 1".format(f1_atom, MAX_BOND_DIST, atom))
    # check that all remaining atoms are bonded to each other
    atoms_to_check = [atom_pair[1]]
    add_atoms_to_fragment(unassigned_atom_numbers, atoms_content, atoms_to_check, frag2_list, 2, single_bond_atoms)
    if len(unassigned_atom_numbers) > 0:
        raise InvalidDataError("Atoms {} were not assigned to either fragment 1 or 2.".format(unassigned_atom_numbers))
    frag1_list.sort()
    frag2_list.sort()
    if len(frag1_list) > len(frag2_list):
        return frag2_list, frag1_list
    else:
        return frag1_list, frag2_list


def add_atoms_to_fragment(atom_numbers, atoms_content, atoms_to_check, frag_list, frag_num, single_bond_atoms):
    add_to_atoms_to_check = []
    while len(atoms_to_check) > 0:
        for check_atom in atoms_to_check:
            atoms_to_remove_from_atom_list = []
            for atom in atom_numbers:
                pair_dist = calc_dist(atoms_content[atom][ATOM_COORDS], atoms_content[check_atom][ATOM_COORDS])
                if pair_dist < MAX_BOND_DIST:
                    frag_list.append(atom)
                    atoms_content[atom][FRAGMENT] = frag_num
                    # avoid changing list while iterating
                    atoms_to_remove_from_atom_list.append(atom)
                    if atoms_content[atom][ATOM_TYPE] not in single_bond_atoms:
                        add_to_atoms_to_check.append(atom)
            for atom in atoms_to_remove_from_atom_list:
                atom_numbers.remove(atom)
        atoms_to_check = []
        for atom in add_to_atoms_to_check:
            atoms_to_check.append(atom)
        add_to_atoms_to_check = []


def write_com_file(com_file_name, gauss_command, for_comment_line, atoms_content, broke_double_bond,
                   frag_num=None, frag_list=None):
    """
    After figuring out the fragments, make Gaussian input files to calculate the counterpoint correction (if a non-zero
    list is passed to "frag_list". Otherwise, make a Gaussian input file to optimize any fragments with len > 1.
    :param com_file_name: str
    :param gauss_command: str
    :param for_comment_line: str
    :param atoms_content: dictionary with atom type, atom coordinates, and fragment ID
    :param broke_double_bond: flag to change multiplicity
    :param frag_num: optional integer that will be used to name the file
    :param frag_list: optional list that will be used to make a Gaussian input file with only the atoms in that fragment
    :return: nothing
    """
    # Don't bother making a separate file if just one atom; there would be lots of repeat calculations that way
    if frag_list is None:
        frag_list = []
    if frag_num:
        if len(frag_list) < 6:
            element_list = []
            for atom_num in frag_list:
                element_list.append(atoms_content[atom_num][ATOM_TYPE])
            print("Fragment {} is only {}".format(os.path.basename(com_file_name), element_list))
            return
        comment_begin = 'radical calculation of fragment {} '.format(frag_num)
        if broke_double_bond:
            charge_mult = '0 3'
        else:
            charge_mult = '0 2'
    else:
        comment_begin = 'cp calculation '
        if broke_double_bond:
            charge_mult = '0 1   0 3    0 3'
        else:
            charge_mult = '0 1   0 2    0 2'
        frag_list = range(1, len(atoms_content)+1)
    print_list = [[gauss_command], [], [comment_begin + for_comment_line], [], [charge_mult]]
    for atom_num in frag_list:
        if frag_num:
            atom_line = atoms_content[atom_num][ATOM_TYPE] + \
                        '    {:11.6f} {:11.6f} {:11.6f}'.format(*atoms_content[atom_num][ATOM_COORDS])
        else:
            atom_line = atoms_content[atom_num][ATOM_TYPE] + \
                        '(Fragment={})    {:11.6f} {:11.6f} {:11.6f}'.format(atoms_content[atom_num][FRAGMENT],
                                                                             *atoms_content[atom_num][ATOM_COORDS])
        print_list.append(atom_line)
    print_list.append([])
    print_list.append([])
    list_to_file(print_list, com_file_name)


def print_com_files(atom_pair, atoms_content, gausscom_file, cfg, frag1, frag2):
    for_comment_line = 'from fragment pair {} and {}'.format(atom_pair, gausscom_file)
    # First print template for CP calc (the coordinates should later be replaced by further optimized coordinates,
    # if desired)
    cp_file_name = create_out_fname(gausscom_file, suffix='_{}_{}_cp'.format(*atom_pair),
                                    ext='.com', base_dir=cfg[OUT_BASE_DIR])
    if len(frag1) == 1 and atoms_content[frag1[0]][ATOM_TYPE] == 'O':
        broke_double_bonds = True
    else:
        broke_double_bonds = False
    write_com_file(cp_file_name, cfg[GAUSS_CP_COMMAND], for_comment_line, atoms_content, broke_double_bonds)
    frag1_file_name = create_out_fname(gausscom_file, suffix='_{}_{}_f1'.format(*atom_pair), base_dir=cfg[OUT_BASE_DIR])
    write_com_file(frag1_file_name, cfg[GAUSS_COMMAND], for_comment_line, atoms_content, broke_double_bonds, 1, frag1)
    frag2_file_name = create_out_fname(gausscom_file, suffix='_{}_{}_f2'.format(*atom_pair), base_dir=cfg[OUT_BASE_DIR])
    write_com_file(frag2_file_name, cfg[GAUSS_COMMAND], for_comment_line, atoms_content, broke_double_bonds, 2, frag2)


def main(argv=None):
    # Read input
    args, ret = parse_cmdline(argv)
    if ret != GOOD_RET or args is None:
        return ret

    cfg = args.config
    gauss_file = cfg[GAUSSCOM_FILE]
    file_name = os.path.basename(gauss_file)
    ext = os.path.splitext(file_name)[1]

    # Read template and data files
    try:
        if ext == '.com':
            gausscom_content = process_gausscom_file(gauss_file)
            atom_data = gausscom_content[SEC_ATOMS]
        elif ext == '.pdb':
            pdb_content = process_gausscom_file(gauss_file)
            atom_data = pdb_content[SEC_ATOMS]
        else:
            raise InvalidDataError("This program expects to read a Gaussian input file with extension '.com' or a "
                                   "pdb file with extension '.pdb', but input file is {}".format(gauss_file))
        # Before making files, check that atom numbers are valid
        for atom_pair in cfg[CUT_PAIR_LIST]:
            validate_atom_num(atom_pair, atom_data, gauss_file)
        for atom_pair in cfg[CUT_PAIR_LIST]:
            frag1, frag2 = fragment_molecule(atom_pair, atom_data)
            print_com_files(atom_pair, atom_data, gauss_file, cfg, frag1, frag2)
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