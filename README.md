**mp8**: (**m**)essage(**p**)ack utf(**8**)


#### Description:
```
writing each arg to stdout:
    messagepack(arg) IF sys.stdout.isatty(); ELSE repr(arg):

You are using a terminal.

IF stdout is not a terminal:
    convert each arg passed to mpp:
        from: the terminal input encoding
        to:   messagepack(arg)
ELSE:
    convert each arg passed to mpp:
        from: the terminal input encoding
        to:   repr(arg)

Messagepack will preserve it's type for other applications that assume messagepacked stdin;

In most setups, this means you enter unicode and write it's UTF-8 byte
representation (messagepacked) to the pipe, or it's unicode repr() back to the terminal.
```

#### pyPsudocode:
```
stdin: not read from, explicitely closed on startup
env (`man 1p export`): not explicitly used
args: N <= `getconf ARG_MAX`
stdout:
    for arg in args:
        if tty:
            print(repr(arg))
        else:
            print(messagepack(arg))
```
#### Examples:
```
$ gpibtool

$ gpibtool --help
Usage: gpibtool [OPTIONS] COMMAND [ARGS]...

Options:
  -v, --verbose
  --dict
  --verbose-inf
  --help         Show this message and exit.

Commands:
  addresses
  command-query
  command-write
  idn
  idns
  info
  syntax

$ # list current GPIB addresses:
$ gpibtool addresses
·ASRL/dev/ttyUSB0::INSTR¯GPIB0::2::INSTR
$ # send the IDN command to each address:
$ gpibtool idns
¯GPIB0::2::INSTRÙ-TEKTRONIX,AFG3022B,C037086,SCPI:99.0 FV:3.2.2
$ # this command is composable, so the same result can be obtained with:
$ gpibtool addresses | gpibtool idn --dict
Traceback (most recent call last):
  File "/usr/lib/python-exec/python3.10/gpibtool", line 12, in <module>
    sys.exit(cli())
  File "/usr/lib/python3.10/site-packages/click/core.py", line 1130, in __call__
    return self.main(*args, **kwargs)
  File "/usr/lib/python3.10/site-packages/click/core.py", line 1055, in main
    rv = self.invoke(ctx)
  File "/usr/lib/python3.10/site-packages/click/core.py", line 1657, in invoke
    return _process_result(sub_ctx.command.invoke(sub_ctx))
  File "/usr/lib/python3.10/site-packages/click/core.py", line 1404, in invoke
    return ctx.invoke(self.callback, **ctx.params)
  File "/usr/lib/python3.10/site-packages/click/core.py", line 760, in invoke
    return __callback(*args, **kwargs)
  File "/usr/lib/python3.10/site-packages/click/decorators.py", line 26, in new_func
    return f(get_current_context(), *args, **kwargs)
  File "/usr/lib/python3.10/site-packages/gpibtool/gpibtool.py", line 163, in _read_command_idn
    command_idn(address=address, verbose=verbose),
  File "/usr/lib/python3.10/site-packages/gpibtool/gpibtool.py", line 97, in command_idn
    idn = command_query(address=address, command="*IDN?", verbose=verbose)
  File "/usr/lib/python3.10/site-packages/gpibtool/gpibtool.py", line 85, in command_query
    idn = inst.query(command)
  File "/usr/lib/python3.10/site-packages/pyvisa/resources/messagebased.py", line 648, in query
    return self.read()
  File "/usr/lib/python3.10/site-packages/pyvisa/resources/messagebased.py", line 486, in read
    message = self._read_raw().decode(enco)
  File "/usr/lib/python3.10/site-packages/pyvisa/resources/messagebased.py", line 442, in _read_raw
    chunk, status = self.visalib.read(self.session, size)
  File "/usr/lib/python3.10/site-packages/pyvisa_py/highlevel.py", line 519, in read
    return data, self.handle_return_value(session, status_code)
  File "/usr/lib/python3.10/site-packages/pyvisa/highlevel.py", line 251, in handle_return_value
    raise errors.VisaIOError(rv)
pyvisa.errors.VisaIOError: VI_ERROR_TMO (-1073807339): Timeout expired before operation completed.

$ # display troubleshooting info:
$ gpibtool info
Output of /usr/bin/pyvisa-info:
Machine Details:
   Platform ID:    Linux-5.19.0-gentoo-x86_64-x86_64-Intel-R-_Core-TM-_i7-4910MQ_CPU_@_2.90GHz-with-glibc2.36
   Processor:      Intel(R) Core(TM) i7-4910MQ CPU @ 2.90GHz

Python:
   Implementation: CPython
   Executable:     /usr/bin/python3.10
   Version:        3.10.7
   Compiler:       GCC 11.3.0
   Bits:           64bit
   Build:          Sep 27 2022 18:25:44 (#main)
   Unicode:        UCS4

PyVISA Version: 1.12.0

Backends:
   ivi:
      Version: 1.12.0 (bundled with PyVISA)
      Binary library: Not found
   py:
      Version: 0.5.3
      ASRL INSTR: Available via PySerial (3.5)
      USB INSTR: Available via PyUSB (1.2.1). Backend: libusb1
      USB RAW: Available via PyUSB (1.2.1). Backend: libusb1
      TCPIP INSTR: Available 
      TCPIP SOCKET: Available 
      GPIB INSTR: Available via Linux GPIB (b'4.3.5')
      GPIB INTFC: Available via Linux GPIB (b'4.3.5')
   sim:
      Version: 0.4.0
      Spec version: 1.1

Output of /usr/bin/lsusb:
Bus 004 Device 002: ID 8087:8000 Intel Corp. Integrated Rate Matching Hub
Bus 004 Device 001: ID 1d6b:0002 Linux Foundation 2.0 root hub
Bus 002 Device 002: ID 8087:8008 Intel Corp. Integrated Rate Matching Hub
Bus 002 Device 001: ID 1d6b:0002 Linux Foundation 2.0 root hub
Bus 003 Device 001: ID 1d6b:0003 Linux Foundation 3.0 root hub
Bus 001 Device 004: ID 05c8:0374 Cheng Uei Precision Industry Co., Ltd (Foxlink) HP EliteBook integrated HD Webcam
Bus 001 Device 003: ID 138a:003f Validity Sensors, Inc. VFS495 Fingerprint Reader
Bus 001 Device 002: ID 08bb:29b0 Texas Instruments PCM2900B Audio CODEC
Bus 001 Device 006: ID 8087:07dc Intel Corp. Bluetooth wireless interface
Bus 001 Device 014: ID 07a6:8511 ADMtek, Inc. ADM8511 Pegasus II Ethernet
Bus 001 Device 013: ID 3923:709b National Instruments Corp. GPIB-USB-HS
Bus 001 Device 012: ID 067b:2303 Prolific Technology, Inc. PL2303 Serial Port / Mobile Action MA-8910P
Bus 001 Device 011: ID 05e3:0608 Genesys Logic, Inc. Hub
Bus 001 Device 001: ID 1d6b:0002 Linux Foundation 2.0 root hub

```
