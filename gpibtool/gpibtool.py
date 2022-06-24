#!/usr/bin/env python3
# -*- coding: utf8 -*-

# pylint: disable=C0111  # docstrings are always outdated and wrong
# pylint: disable=C0114  # Missing module docstring (missing-module-docstring)
# pylint: disable=W0511  # todo is encouraged
# pylint: disable=C0301  # line too long
# pylint: disable=R0902  # too many instance attributes
# pylint: disable=C0302  # too many lines in module
# pylint: disable=C0103  # single letter var names, func name too descriptive
# pylint: disable=R0911  # too many return statements
# pylint: disable=R0912  # too many branches
# pylint: disable=R0915  # too many statements
# pylint: disable=R0913  # too many arguments
# pylint: disable=R1702  # too many nested blocks
# pylint: disable=R0914  # too many local variables
# pylint: disable=R0903  # too few public methods
# pylint: disable=E1101  # no member for base
# pylint: disable=W0201  # attribute defined outside __init__
# pylint: disable=R0916  # Too many boolean expressions in if statement

# import gpib
# import visa
# import pyvisa as visa  # conflct with https://github.com/visa-sdk/visa-python
# from pyvisa.errors import VisaIOError
# from gpib import GpibError


import os
import sys
from contextlib import contextmanager
from signal import SIG_DFL
from signal import SIGPIPE
from signal import signal
from typing import Union

import click
import pyvisa
import sh
from asserttool import ic
from bnftool import get_bnf_syntax
from click_auto_help import AHGroup
from clicktool import click_add_options
from clicktool import click_global_options
from clicktool import tv
from mptool import output
from pyvisa.errors import VisaIOError

signal(SIGPIPE, SIG_DFL)


# https://github.com/pyvisa/pyvisa-py/issues/282
@contextmanager
def _supress_stderr():
    original_stderr = os.dup(
        2
    )  # stderr stream is linked to file descriptor 2, save a copy of the real stderr so later we can restore it
    blackhole = os.open(
        os.devnull, os.O_WRONLY
    )  # anything written to /dev/null will be discarded
    os.dup2(
        blackhole, 2
    )  # duplicate the blackhole to file descriptor 2, which the C library uses as stderr
    os.close(
        blackhole
    )  # blackhole was duplicated from the line above, so we don't need this anymore
    yield
    os.dup2(original_stderr, 2)  # restoring the original stderr
    os.close(original_stderr)


class NoResourcesFoundError(ValueError):
    pass


def get_instrument(
    *,
    address: str,
    verbose: Union[bool, int, float],
):

    if verbose:
        ic(address)
    rm = pyvisa.ResourceManager("@py")
    ic(address)
    inst = rm.open_resource(address)
    return inst


def command_query(
    *,
    address: str,
    command: str,
    verbose: Union[bool, int, float],
):

    ic(address)
    inst = get_instrument(
        address=address,
        verbose=verbose,
    )
    # idn = inst.query("*IDN?")
    idn = inst.query(command)
    if verbose:
        ic(idn)
    return idn.strip()


def command_idn(
    *,
    address: str,
    verbose: Union[bool, int, float],
):

    idn = command_query(address=address, command="*IDN?", verbose=verbose)
    # inst = get_instrument(address=address, verbose=verbose,)
    # idn = inst.query("*IDN?")
    # if verbose:
    #    ic(idn)
    # return idn.strip()
    return idn


def get_resources(
    verbose: Union[bool, int, float],
):

    # with redirect_stderr(None):
    #    with redirect_stdout(None):
    with _supress_stderr():
        resource_manager = pyvisa.ResourceManager()
        resources = list(resource_manager.list_resources())

    if verbose:
        ic(resources)
    try:
        resources.remove("ASRL/dev/ttyS0::INSTR")
    except ValueError:
        pass

    if resources:
        return tuple(resources)
    else:
        raise NoResourcesFoundError


@click.group(no_args_is_help=True, cls=AHGroup)
@click_add_options(click_global_options)
@click.pass_context
def cli(
    ctx,
    verbose: Union[bool, int, float],
    verbose_inf: bool,
    dict_input: bool,
):

    tty, verbose = tv(
        ctx=ctx,
        verbose=verbose,
        verbose_inf=verbose_inf,
    )


@cli.command("idn")
@click.argument("address", type=str)
@click_add_options(click_global_options)
@click.pass_context
def _read_command_idn(
    ctx,
    address: str,
    verbose: Union[bool, int, float],
    verbose_inf: bool,
    dict_input: bool,
):

    tty, verbose = tv(
        ctx=ctx,
        verbose=verbose,
        verbose_inf=verbose_inf,
    )

    print(command_idn(address=address, verbose=verbose))


@cli.command("info")
@click_add_options(click_global_options)
@click.pass_context
def _pyvisa_info(
    ctx,
    verbose: Union[bool, int, float],
    verbose_inf: bool,
    dict_input: bool,
):

    tty, verbose = tv(
        ctx=ctx,
        verbose=verbose,
        verbose_inf=verbose_inf,
    )

    info_command = sh.Command("/usr/bin/pyvisa-info")
    # python -c "from pyvisa import util; util.get_debug_info()"
    info_command(_out=sys.stdout)


@cli.command("syntax")
@click_add_options(click_global_options)
@click.pass_context
def _bnf_syntax(
    ctx,
    verbose: Union[bool, int, float],
    verbose_inf: bool,
    dict_input: bool,
):

    tty, verbose = tv(
        ctx=ctx,
        verbose=verbose,
        verbose_inf=verbose_inf,
    )

    bnf_symbols = get_bnf_syntax()
    command_message_elements = {
        "<Header>": "This is the basic command name. If the header ends with a question mark, the command is a query. The header may begin with a colon (:) character. If the command is concatenated with other commands, the beginning colon is required. Never use the beginning colon with command headers beginning with a star (*).",
        "<Mnenomic>": "This is a header subfunction. Some command headers have only one mnemonic. If a command header has multiple mnemonics, a colon (:) character always separates them from each other.",
        "<Argument>": "This is a quantity, quality, restriction, or limit associated with the header. Some commands have no arguments while others have multiple arguments. A <space> separates arguments from the header. A <comma> separates arguments from each other.",
        "<Comma>": "A single comma is used between arguments of multiple-argument commands. Optionally, there may be white space characters before and after the comma.",
        "<Space>": "A white space character is used between a command header and the related argument. Optionally, a white space may consist of multiple white space characters.",
    }
    command = "[:]<Header>[<Space><Argument>[<Comma> <Argument>]...]"
    query = ("[:]<Header>", "[:]<Header>[<Space><Argument> [<Comma><Argument>]...]")

    output(bnf_symbols, reason=None, dict_input=dict_input, tty=tty, verbose=verbose)
    output(
        command_message_elements,
        reason=None,
        dict_input=dict_input,
        tty=tty,
        verbose=verbose,
    )
    output(command, reason=None, dict_input=dict_input, tty=tty, verbose=verbose)
    output(query, reason=None, dict_input=dict_input, tty=tty, verbose=verbose)


@cli.command("command-write")
@click.argument("address", type=str)
@click.argument("command", type=str)
@click_add_options(click_global_options)
@click.pass_context
def _command_write(
    ctx,
    address: str,
    command: str,
    verbose: Union[bool, int, float],
    verbose_inf: bool,
    dict_input: bool,
):

    tty, verbose = tv(
        ctx=ctx,
        verbose=verbose,
        verbose_inf=verbose_inf,
    )

    inst = get_instrument(
        address=address,
        verbose=verbose,
    )
    if verbose:
        ic(command, len(command))
    result = inst.write(command)
    print(result)


@cli.command("command-query")
@click.argument("address", type=str)
@click.argument("command", type=str)
@click_add_options(click_global_options)
@click.pass_context
def _command_query(
    ctx,
    address: str,
    command: str,
    verbose: Union[bool, int, float],
    verbose_inf: bool,
    dict_input: bool,
):

    tty, verbose = tv(
        ctx=ctx,
        verbose=verbose,
        verbose_inf=verbose_inf,
    )

    inst = get_instrument(
        address=address,
        verbose=verbose,
    )
    if verbose:
        ic(command, len(command))
    result = inst.query(command)
    print(result)


@cli.command("addresses")
@click.option("--ipython", is_flag=True)
@click_add_options(click_global_options)
@click.pass_context
def _list_addresses(
    ctx,
    verbose: Union[bool, int, float],
    verbose_inf: bool,
    dict_input: bool,
    ipython: bool,
):

    tty, verbose = tv(
        ctx=ctx,
        verbose=verbose,
        verbose_inf=verbose_inf,
    )

    # https://github.com/pyvisa/pyvisa-py/issues/282
    with _supress_stderr():
        resources = get_resources(verbose=verbose)
    if verbose:
        ic(resources)
    for resource in resources:
        output(resource, reason=None, tty=tty, dict_input=dict_input, verbose=verbose)


@cli.command("idns")
@click.option("--ipython", is_flag=True)
@click_add_options(click_global_options)
@click.pass_context
def _list_idns(
    ctx,
    verbose: Union[bool, int, float],
    verbose_inf: bool,
    dict_input: bool,
    ipython: bool,
):

    dict_input = True  # this does not take input on stdin, todo: fix dict_input convention to reflect this
    tty, verbose = tv(
        ctx=ctx,
        verbose=verbose,
        verbose_inf=verbose_inf,
    )

    ic('calling: pyvisa.ResourceManager("@py")')
    with _supress_stderr():
        rm = pyvisa.ResourceManager("@py")

    ic("calling: get_resources()")
    resources = get_resources(verbose=verbose)
    for resource in resources:
        if verbose:
            ic(resource)
        inst = rm.open_resource(resource)
        if verbose:
            ic(inst)
        try:
            output(
                inst.query("*IDN?"),
                reason=resource,
                tty=tty,
                verbose=verbose,
                dict_input=dict_input,
            )
        except VisaIOError as e:
            if verbose:
                ic(e)
            if not e.args[0].endswith("Timeout expired before operation completed."):
                raise e
