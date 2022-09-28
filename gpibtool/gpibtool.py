#!/usr/bin/env python3
# -*- coding: utf8 -*-

# pylint: disable=missing-docstring               # [C0111] docstrings are always outdated and wrong
# pylint: disable=missing-module-docstring        # [C0114]
# pylint: disable=fixme                           # [W0511] todo is encouraged
# pylint: disable=line-too-long                   # [C0301]
# pylint: disable=too-many-instance-attributes    # [R0902]
# pylint: disable=too-many-lines                  # [C0302] too many lines in module
# pylint: disable=invalid-name                    # [C0103] single letter var names, name too descriptive
# pylint: disable=too-many-return-statements      # [R0911]
# pylint: disable=too-many-branches               # [R0912]
# pylint: disable=too-many-statements             # [R0915]
# pylint: disable=too-many-arguments              # [R0913]
# pylint: disable=too-many-nested-blocks          # [R1702]
# pylint: disable=too-many-locals                 # [R0914]
# pylint: disable=too-few-public-methods          # [R0903]
# pylint: disable=no-member                       # [E1101] no member for base
# pylint: disable=attribute-defined-outside-init  # [W0201]
# pylint: disable=too-many-boolean-expressions    # [R0916] in if statement

# import gpib
# import visa
# import pyvisa as visa  # conflct with https://github.com/visa-sdk/visa-python
# from pyvisa.errors import VisaIOError
# from gpib import GpibError

from __future__ import annotations

import os
import sys
from contextlib import contextmanager
from signal import SIG_DFL
from signal import SIGPIPE
from signal import signal

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
from stdiotool import supress_stderr

signal(SIGPIPE, SIG_DFL)


class NoResourcesFoundError(ValueError):
    pass


def get_instrument(
    *,
    address: str,
    verbose: bool | int | float,
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
    verbose: bool | int | float,
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
    verbose: bool | int | float,
):

    idn = command_query(address=address, command="*IDN?", verbose=verbose)
    # inst = get_instrument(address=address, verbose=verbose,)
    # idn = inst.query("*IDN?")
    # if verbose:
    #    ic(idn)
    # return idn.strip()
    return idn


def get_resources(
    verbose: bool | int | float,
):

    with supress_stderr():
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
    verbose: bool | int | float,
    verbose_inf: bool,
    dict_output: bool,
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
    verbose: bool | int | float,
    verbose_inf: bool,
    dict_output: bool,
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
    verbose: bool | int | float,
    verbose_inf: bool,
    dict_output: bool,
):

    tty, verbose = tv(
        ctx=ctx,
        verbose=verbose,
        verbose_inf=verbose_inf,
    )

    info_command = sh.Command("pyvisa-info")
    # python -c "from pyvisa import util; util.get_debug_info()"
    info_command(_out=sys.stdout)


@cli.command("syntax")
@click_add_options(click_global_options)
@click.pass_context
def _bnf_syntax(
    ctx,
    verbose: bool | int | float,
    verbose_inf: bool,
    dict_output: bool,
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

    output(bnf_symbols, reason=None, dict_output=dict_output, tty=tty, verbose=verbose)
    output(
        command_message_elements,
        reason=None,
        dict_output=dict_output,
        tty=tty,
        verbose=verbose,
    )
    output(command, reason=None, dict_output=dict_output, tty=tty, verbose=verbose)
    output(query, reason=None, dict_output=dict_output, tty=tty, verbose=verbose)


@cli.command("command-write")
@click.argument("address", type=str)
@click.argument("command", type=str)
@click_add_options(click_global_options)
@click.pass_context
def _command_write(
    ctx,
    address: str,
    command: str,
    verbose: bool | int | float,
    verbose_inf: bool,
    dict_output: bool,
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
    verbose: bool | int | float,
    verbose_inf: bool,
    dict_output: bool,
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
    verbose: bool | int | float,
    verbose_inf: bool,
    dict_output: bool,
    ipython: bool,
):

    tty, verbose = tv(
        ctx=ctx,
        verbose=verbose,
        verbose_inf=verbose_inf,
    )

    # https://github.com/pyvisa/pyvisa-py/issues/282
    with supress_stderr():
        resources = get_resources(verbose=verbose)
    if verbose:
        ic(resources)
    for resource in resources:
        output(resource, reason=None, tty=tty, dict_output=dict_output, verbose=verbose)


@cli.command("idns")
@click.option("--ipython", is_flag=True)
@click_add_options(click_global_options)
@click.pass_context
def _list_idns(
    ctx,
    verbose: bool | int | float,
    verbose_inf: bool,
    dict_output: bool,
    ipython: bool,
):

    # forcing dict_output=True since a IDN alone is _never_ as useful as a (GPIB source: IDN) mapping
    # toodoo-maybe: if the GPIB source was read on stdin, this wouldnt be be necessary
    dict_output = True  # this does not take input on stdin, todo: fix dict_output convention to reflect this
    tty, verbose = tv(
        ctx=ctx,
        verbose=verbose,
        verbose_inf=verbose_inf,
    )

    if verbose:
        ic('calling: pyvisa.ResourceManager("@py")')
    with supress_stderr():
        rm = pyvisa.ResourceManager("@py")

    if verbose:
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
                dict_output=dict_output,
            )
        except VisaIOError as e:
            if verbose:
                ic(e)
            if not e.args[0].endswith("Timeout expired before operation completed."):
                raise e
