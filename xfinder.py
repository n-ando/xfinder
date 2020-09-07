#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# @file xfinder
# @brief RaspberryPi/BeagleBone finder
# @author Noriaki Ando <n-ando@aist.go.jp>
# @copyright Copyright (C) 2014-2020 Noriaki Ando, All right reserved.
#
# This tool helps to find RaspberryPi, BeagleBone or other head-less
# cpu boards from specific MAC addresses.
#
# Usage:
# This tool finds RaspberryPi, BeagleBone or other embedded (or
# head-less) nodes by scanning a specific MAC address on a specific
# (or all) network interface(s).  This tool has two mode (CUI mode and
# GUI mode) which are switched by a command name itself or command
# line options.
#
# If this tool's command name is "pifinder(.py)" or "bbfinder(.py)",
# it will be run in CUI mode. With any other command names and command
# line options are given, it will be executed in CUI mode. Otherwise
# it are run as GUI mode.
#
# CUI mode:
# The following options are available:
#   -h, --help               print this help message
#
#   -i, --if=[IP_ADDR}       specify interface ip address
#                            if it is not specified, it scans all interfaces.
#                            partial IP address is also acceptable, for example
#                            -i 192 specify 192.XXX.YYY.ZZZ
#                            --if 192.168. specify 192.168.XXX.YYY
#
#   -t, --type=[BOARD_TYPE]  specify board type
#                            available boad types are""" % (sys.argv[0])
#
#   -p, --pattern=[MAC_ADDR] specify MAC address pattern to be matched
#                            ex. -p \"b8:27:eb:[a-f0-9:]*\"
#
# Examples:
# finding RaspberryPi on a network interface with 192.168.0.2
#    $ %s -t raspi -i 192.168.0.2
#    $ pifinder -i 192.168.0.2
#
# finding BeagleBoneBlack on all the interfaces
#    $ %ss -t bbb
#    $ bbfinder
#
# finding VMware virtual host with MAC address 00:50:56.*
#    $ %s -p \"00:50:56\"
#
# GUI mode
# 1. Launch the tool as GUI mode (without any options)
# 2. Select network interface address (or keep ALL if scan all I/Fs)
# 3. Select board type (RaspberryPi, BeagleBone, etc) and radio button
# 4. or if you want find specific MAC address, input MAC address
#    pattern and select radio button
# 5. Push "Scan" button. Scanning takes several tens of seconds and
#    the results are shown in the right table.
#------------------------------------------------------------
import sys
import os
import platform
import re
import time
import subprocess
from subprocess import Popen, PIPE
from threading import Thread

# Max thread Pinger agent
MAX_THREAD = 16
# If enable debug print, set True
DEBUG = False

# Suppress Tkinter deprecation message
os.environ["TK_SILENCE_DEPRECATION"] = "1"

# Suppress opening command window on Windows
if platform.system() == 'Windows':
    import subprocess
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = subprocess.SW_HIDE

    # Windows workaround for DLL loading order
    # https://github.com/pyinstaller/pyinstaller/wiki/Recipe-subprocess
    import ctypes
    ctypes.windll.kernel32.SetDllDirectoryA(None)

#------------------------------------------------------------
# Debug print function
#------------------------------------------------------------
def dprint(msg):
    if DEBUG:
        sys.stderr.write(msg)


#------------------------------------------------------------
# popen_args(): stdin/out/err settings for Popen
#
# "pyinstaller --noconsole" on Windows requires stdin/out/err
# strict redirection to avoid OSError
#
# https://github.com/pyinstaller/pyinstaller/wiki/Recipe-subprocess
#------------------------------------------------------------
def popen_args(include_stdout = True):
    # The following is true only on Windows.
    if hasattr(subprocess, 'STARTUPINFO'):
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        env = os.environ
    else:
        si = None
        env = None
    if include_stdout: # <= other Popen funcs
        ret = {'stdout': subprocess.PIPE}
    else: # <= Popen.check_output()
        ret = {}
    ret.update({'stdin': subprocess.PIPE,
                'stderr': subprocess.PIPE,
                'startupinfo': si,
                'env': env })
    return ret


#============================================================
# Getting current network information (IP address)
#============================================================
#------------------------------------------------------------
# get_interfaces_win32()
# return: It returns IP address list of current host
#------------------------------------------------------------
def get_interfaces_win32():
    try:
        p = Popen('ipconfig', shell = True, **popen_args())
        addr_list = []
        while True:
            line  = p.stdout.readline()
            if not line: break
            m = re.search("IPv4", str(line))
            if m:
                m0 = re.search("(\d+\.){3}(\d+)", str(line))
                if m0: addr_list.append(m0.group())
        p.wait()
    except:
        print("Unexpected error in get_interfaces_win32():",
                sys.exc_info()[0])
    dprint("get_interfaces_win32() = " + ' '.join(addr_list) + "\n")
    return addr_list

#------------------------------------------------------------
# get_interfaces_unix()
# return: It returns IP address list of current host
#------------------------------------------------------------
def get_interfaces_unix():
    try:
        p = Popen('LC_ALL=C ifconfig -a', shell = True, **popen_args())
        addr_list = []
        while True:
            line  = p.stdout.readline()
            if not line: break
            m = re.search("inet ([0-9]{1,3}(\.[0-9]{1,3}){3})", str(line))
            if m and m.group(1) != '127.0.0.1':
                dprint(m.group(1) + '\n')
                addr_list.append(m.group(1))
        p.wait()
    except:
        print("Unexpected error in get_interfaces_unix():",
                sys.exc_info()[0])
    dprint("get_interfaces_unix() = " + ' '.join(addr_list) + '\n')
    return addr_list

#------------------------------------------------------------
# get_interfaces_macos()
# return: It returns IP address list of current host
#------------------------------------------------------------
def get_interfaces_macos():
    try:
        p = Popen("LC_ALL='C' ifconfig -a", shell = True, **popen_args())
        addr_list = []
        while True:
            line  = p.stdout.readline()
            if not line: break
            m = re.search("inet ([0-9]{1,3}(\.[0-9]{1,3}){3})", str(line))
            if m and m.group(1) != '127.0.0.1':
                dprint(m.group(1) + '\n')
                addr_list.append(m.group(1))
        p.wait()
    except:
        print("Unexpected error in get_interfaces_macos():",
                sys.exc_info()[0])
    dprint("get_interfaces_macos() = " + ' '.join(addr_list) + '\n')
    return addr_list

#------------------------------------------------------------
# get_interfaces()
# return: It returns IP address list of current host
#------------------------------------------------------------
def get_interfaces():
    import os
    import platform
    if platform.system() == "Linux":
        return get_interfaces_unix()
    elif platform.system() == "Darwin":
        return get_interfaces_macos()
    elif platform.system() == "Windows":
        return get_interfaces_win32()
    else:
        print("Unsupported OS")
        return get_interfaces_unix()

#------------------------------------------------------------

#============================================================
# Getting current network information (mask, gw)
#============================================================
#------------------------------------------------------------
# get_netinfo_win32(ip_addr)
# ip_addr: An IP address of one of the current host.
# return : It returns the following dictionary
#    "if_addr": IP address of the interface. (the given IP address)
#    "if_mask": Net mask of the interface
#    "if_gw"  : Gateway of the interface
#------------------------------------------------------------
def get_netinfo_win32(ip_addr):
    p = Popen('ipconfig', **popen_args())
    r = {}
    r["if_addr"] = ip_addr
    while True:
        line  = p.stdout.readline()
        if not line: break

        m = re.search(ip_addr, str(line))
        if m:
            m0 = re.search("(\d+\.){3}(\d+)", str(p.stdout.readline()))
            if m0: r["if_mask"] = m0.group()
            m1 = re.search("(\d+\.){3}(\d+)", str(p.stdout.readline()))
            if m1: r["if_gw"]   = m1.group()
    p.wait()
    return r

#------------------------------------------------------------
# get_netinfo_unix(ip_addr)
# ip_addr: An IP address of one of the current host.
# return : It returns the following dictionary
#    "if_addr": IP address of the interface. (the given IP address)
#    "if_mask": Net mask of the interface
#    "if_gw"  : Gateway of the interface
#------------------------------------------------------------
def get_netinfo_unix(ip_addr):
    p = Popen('LC_ALL=C ifconfig -a', shell = True, **popen_args())
    r = {}
    r["if_addr"] = ip_addr
    while True:
        line  = p.stdout.readline()
        if not line: break
        m = re.search(ip_addr, str(line))
        if m:
            m0 = re.search("netmask ([0-9]{1,3}(\.[0-9]{1,3}){3})", str(line))
            if m0:
                r["if_mask"] = m0.group(1)
                dprint("mask: " + m0.group(1) + "\n")
    p.wait()
    return r

#------------------------------------------------------------
# get_netinfo_macos(ip_addr)
# ip_addr: An IP address of one of the current host.
# return : It returns the following dictionary
#    "if_addr": IP address of the interface. (the given IP address)
#    "if_mask": Net mask of the interface
#    "if_gw"  : Gateway of the interface
#------------------------------------------------------------
def get_netinfo_macos(ip_addr):
    p = Popen('LC_ALL=C ifconfig -a', shell = True, **popen_args())
    r = {}
    r["if_addr"] = ip_addr
    while True:
        line  = p.stdout.readline()
        if not line: break
        m = re.search(ip_addr, str(line))
        if m:
            m0 = re.search("netmask 0x([0-9a-f]{8})", str(line))
            if m0:
                hexmask = m0.group(1)
                r["if_mask"]= '.'.join(
                    [str(int(i,16)) for i in re.split('(..)',hexmask)[1::2]])
            m1 = re.search("(\d+\.){3}(\d+)", str(p.stdout.readline()))
            if m1: r["if_gw"]   = m1.group()
    p.wait()
    return r

#------------------------------------------------------------
# get_netinfo(ip_addr)
# ip_addr: An IP address of one of the current host.
# return : It returns the following dictionary
#    "if_addr": IP address of the interface. (the given IP address)
#    "if_mask": Net mask of the interface
#    "if_gw"  : Gateway of the interface
#------------------------------------------------------------
def get_netinfo(ip_addr):
    import os
    import platform
    if os.name == 'posix':
        if platform.system() == "Darwin":
            return get_netinfo_macos(ip_addr)
        else:
            return get_netinfo_unix(ip_addr)
    elif os.name == 'nt':
        return get_netinfo_win32(ip_addr)
    else:
        print("Unsupported OS")
#
#============================================================

#============================================================
# IP address manipuylation utilities
#============================================================

#------------------------------------------------------------
# count_maskbit(mask_str)
# mask_str: Dotted netmask expression like: 255.255.254.0
# return  : Number of bit for the given netmask string
#
# ex. count_maskbit("255.255.254.0") -> 23
#------------------------------------------------------------
def count_maskbit(mask_str):
    mask = mask_str.split(".")
    if len(mask) != 4:
        print("Error: invalid mask", mask_str)
        sys.exit(1)
    count = 0
    bitnum_pre = 8
    for m in mask:
        bitnum = bin(int(m)).count('1')
        if bitnum > bitnum_pre:
            print("Error: invalid mask", mask_str)
            sys.exit(1)
        count = count + bitnum
        bitnum_pre = bitnum
    return count

#------------------------------------------------------------
# sockaddr_to_hex(addr)
# addr   : IP address expression by char array which are used
#          in socket module functions
# return : Hexadecimal (4 bytes) IP address expression
#------------------------------------------------------------
def sockaddr_to_hex(addr):
    a = addr.split(".")
    b =   ((int(a[0]) & 0xFF) << 24) \
        + ((int(a[1]) & 0xFF) << 16) \
        + ((int(a[2]) & 0xFF) << 8)  \
        + ((int(a[3]) & 0xFF) << 0)
    return b

#------------------------------------------------------------
# hex_to_sockaddr(hex_addr)
# hex_addr: Hexadecimal (4 bytes) expression of IP address
# return  : IP address expression by char array which are used
#          in socket module functions
#------------------------------------------------------------
def hex_to_sockaddr(hex_addr):
    import socket
    import struct
    a0 = int((hex_addr >> 24) & 0xFF)
    a1 = int((hex_addr >> 16) & 0xFF)
    a2 = int((hex_addr >> 8)  & 0xFF)
    a3 = int((hex_addr >> 0)  & 0xFF)
    return struct.pack("BBBB", a0, a1, a2, a3)

#------------------------------------------------------------
# get_addr_range(ip_addr)
#
# This function calculates host IP addresses which are included
# in the current network from given an IP address with netmask.
#
# ip_addr: Dotted IP address expression with netmask bit number
#          separated by slash "/". ex. 150.29.99.231/24
# return : IP address list by array
#------------------------------------------------------------
def get_addr_range(ip_addr):
    import socket
    import struct
    r = []
    ip, mask = ip_addr.split("/")
    mask = int(mask)
    h = socket.inet_aton(ip)
    bin_addr = socket.htonl(struct.unpack("I", h)[0])
    hex_to_sockaddr(bin_addr)
    bin_mask = 0b0
    for i in range(0, 32):
        if i < mask:
            bin_mask = (bin_mask << 1) | 0b1
        else:
            bin_mask = bin_mask << 1
    bin_netw = bin_addr & bin_mask
    for x in range(0, pow(2,(32 - mask))):
        new_addr = bin_netw | x
        a0 = int((new_addr >> 24) & 0xFF)
        a1 = int((new_addr >> 16) & 0xFF)
        a2 = int((new_addr >> 8)  & 0xFF)
        a3 = int((new_addr >> 0)  & 0xFF)
        addr = struct.pack("BBBB", a0, a1, a2, a3)
        r.append(socket.inet_ntoa(addr))
    return r
#
#============================================================

#============================================================
# MAC address related functions
#============================================================

#------------------------------------------------------------
# get_macaddress_win32()
#------------------------------------------------------------
def get_macaddress_win32(host):
    p = Popen("arp -a " + host, shell = True, **popen_args())
    while True:
        line = p.stdout.readline()
        if not line: break
        m = re.search("(([0-9A-Fa-f]{1,2}[:-]){5}([0-9A-Fa-f]{1,2}))",
                    str(line))
        if m:
            # Macaddress's delimiter is '-' on Win arp
            return m.group(0).replace("-", ":")
    return ""

#------------------------------------------------------------
# get_macaddress_unix()
#------------------------------------------------------------
def get_macaddress_unix(host):
    p = Popen("arp " + host, shell = True, **popen_args())
    while True:
        line = p.stdout.readline()
        if not line: break
        m = re.search("(([0-9A-Fa-f]{1,2}[:-]){5}([0-9A-Fa-f]{1,2}))",
                    str(line))
        if m:
            return m.group(0)
    return ""

def get_macaddress(host):
    import os
    import platform
    if os.name == 'posix':
        return get_macaddress_unix(host)
    elif os.name == 'nt':
        return get_macaddress_win32(host)
    else:
        print("Unsupported OS")
#------------------------------------------------------------
    



#------------------------------------------------------------
# @class Pinger class
# This class pingsto hosts and returns aliving hosts list.
# PingAgents.wait() waits until finishing ping operation.
# PingAgent.results includes aliving hosts list.
# ex.
# hosts = ['192.168.0.1', '192.168.0.2', ... ]
# Pinger(hosts)
# PingAgent.wait()
# print PingAgent.results
#------------------------------------------------------------
class Pinger(object):
    running = True
    def __init__(self, hosts, numthreads = MAX_THREAD, pattern = None,
                 callback = None):
        PingAgent.reset()
        if numthreads > MAX_THREAD: numthreads = MAX_THREAD
        PingAgent.set_max(len(hosts))
        Pinger.running = True
        for host in hosts:
            if not Pinger.running: break
            pa = PingAgent(host, pattern, callback)
            pa.start()
            time.sleep(0.05)
            if numthreads == 0: continue
            while len(PingAgent.running) > numthreads:
                time.sleep(0.1)
    @staticmethod
    def abort():
        Pinger.running = False

class PingAgent(Thread):
    results = {}
    running = []
    count   = 0
    max_count = 0
    verbose = True
    def __init__(self, host, pattern = None, callback = None):
        Thread.__init__(self)
        self.host = host
        self.pattern = pattern
        self.callback = callback
        PingAgent.running.append(1)
        PingAgent.count += 1
        if PingAgent.verbose:
            sys.stderr.write('.')
            sys.stderr.flush()

    @staticmethod
    def wait():
        while len(PingAgent.running) != 0:
            time.sleep(1)
        return

    @staticmethod
    def reset():
        PingAgent.count = 0
        PingAgent.results = {}

    @staticmethod
    def set_max(max_count):
        PingAgent.max_count = max_count

    @staticmethod
    def verbose(vvv = True):
        PingAgent.verbose = vvv

    def run(self):
        import platform
        if platform.system() == 'Linux':
            p = subprocess.Popen("ping -t 1 -w 1 " +  self.host,
                                shell = True, ** popen_args())
            m = re.search("ttl", str(p.stdout.read()))
            dprint("ping -t 1 -w 1 " +  self.host + "\n")
            p.wait()
        elif platform.system() == 'Darwin':
            p = subprocess.Popen("ping -t 1 -c 1 " +  self.host,
                                shell = True, ** popen_args())
            m = re.search("ttl", str(p.stdout.read()))
            dprint("ping -t 1 -c 1 " +  self.host + "\n")
            p.wait()
        elif platform.system() == 'Windows':
            p = subprocess.Popen("ping -n 1 -w 1000 " + self.host,
                                shell = True, **popen_args())
            m = re.search("TTL", str(p.stdout.read()))
            dprint("ping -n 1" + self.host + "\n")
            p.wait()
        else:
            print("Unsupported OS")
        if m:
            if self.pattern:
                macaddr = get_macaddress(self.host)
                dprint("MAC addr: " + macaddr + "\n")
                pmatch = re.match(self.pattern, str(macaddr))
                if pmatch:
                    dprint("MAC address matched\n")
                    if self.callback:
                        self.callback(self.host, macaddr)
                    PingAgent.results[self.host] = macaddr
            else:
                PingAgent.results[self.host] = ""
        #finished
        PingAgent.running.pop()
#
#------------------------------------------------------------

#------------------------------------------------------------
# get_mac_matched_ip(host_ip, pattern)
#
# host_ip: One of the host IP address (ex. 192.168.11.10)
# pattern: Match pattern of mac address (ex. b8:27:eb:[a-f0-9:]*)
#
# ex. 
# RaspberryPi list = get_mac_matched_ip(host_ip, "b8:27:eb:[a-f0-9:]*")
# BeagleBone list  = get_mac_matched_ip(host_ip, "c8:a0:30:[a-f0-9:]*")
#------------------------------------------------------------
def get_mac_matched_ip(host_ip, pattern, callback = None):
    net_info = get_netinfo(host_ip)
    mask_bit = count_maskbit(net_info["if_mask"])
    addr_str = net_info["if_addr"] + "/" + str(mask_bit)
    addr_range = get_addr_range(addr_str)
    addr_range.reverse()
    Pinger(addr_range, 64, pattern, callback)
    PingAgent.wait()
    result = {}
    for ip_addr in PingAgent.results.keys():
        mac_addr = get_macaddress(ip_addr)
        m = re.match(pattern.lower(), mac_addr.lower())
        if m:
            result[ip_addr] = get_macaddress(ip_addr)
    return result

#------------------------------------------------------------
# get_raspberrypis(host_ip)
# Getting RaspberryPi list
#------------------------------------------------------------
def get_raspberrypis(host_ip, callback = None):
    return get_mac_matched_ip(host_ip, "b8:27:eb:[a-f0-9:]*", callback)

#------------------------------------------------------------
# get_beaglebones(host_ip)
# Getting BeagleBone list
#------------------------------------------------------------
def get_beaglebones(host_ip, callback = None):
    return get_mac_matched_ip(host_ip, "c8:a0:30:[a-f0-9:]*", callback)
#
#------------------------------------------------------------

#------------------------------------------------------------
# help()
#------------------------------------------------------------
def help():
    help_msg = """
Usage:
  %s [OPTIONS]

Options:
  -h, --help               print this help message

  -i, --if=[IP_ADDR}       specify interface ip address
                           if it is not specified, it scans all interfaces.
                           partial IP address is also acceptable, for example
                           -i 192 specify 192.XXX.YYY.ZZZ
                           --if 192.168. specify 192.168.XXX.YYY

  -t, --type=[BOARD_TYPE]  specify board type
                           available boad types are""" % (sys.argv[0])
    print(help_msg)
    for n, t in BOARD_TYPES.items():
        print("                      %s:" % (n))
        print("                     ", t[0])
    htlp_msg = """
  -p, --pattern=[MAC_ADDR] specify MAC address pattern to be matched
                           ex. -p \"b8:27:eb:[a-f0-9:]*\"

Examples:
 finding RaspberryPi on a network interface with 192.168.0.2
    $ %s -t raspi -i 192.168.0.2
    $ pifinder -i 192.168.0.2

 finding BeagleBoneBlack on all the interfaces
    $ %ss -t bbb
    $ bbfinder

 finding VMware virtual host with MAC address 00:50:56.*
    $ %s -p \"00:50:56\"
""" % (sys.argv[0], sys.argv[0], sys.argv[0])
    print(help_msg)


#------------------------------------------------------------
# CUI main function
#------------------------------------------------------------
BOARD_TYPES = {
    "RaspberryPi": (
    ("pi", "rpi", "raspi", "raspberry", "raspberrypi"),
    {"login": "pi", "passwd": "raspberry", "port": "22"},
    get_raspberrypis), 
    "BeagleBone" : (
    ("bb", "bbb", "beagle", "beaglebone", "beagleboneblack"),
    {"login": "root", "passwd": "", "port": "22"},
    get_beaglebones),
    }
def check_ifaddr(host_ip, a):
    curr_ifip = get_interfaces()
    for ip in curr_ifip:
        # -i 192.168 => matches current ip if 192.168.X.Y
        if ip.find(a) == 0: # head match only!!
            if host_ip.count(ip) == 0: host_ip.append(ip)
    if len(host_ip) == 0:
        print(a, "is not (or does not match) my IP address.")
        print("Available host IP addresses are:")
        print(curr_ifip)
        sys.exit(0)

def check_type(board_type, a):
    a = a.lower()
    for name in BOARD_TYPES:
        if BOARD_TYPES[name][0].count(a) != 0 and \
               board_type.count(name) == 0:
            board_type.append(name)

def print_boards(boards):
    for i, m in boards.items():
        import socket
        try:
            host_name = socket.gethostbyaddr(i)[0]
        except:
            host_name = ""
        print("    ", i, "\t", m, "\t", host_name)

def cui_main():
    try:
        options, args = getopt.getopt(sys.argv[1:],
                                      'hi:t:p:',
                                      ['help', 'if=', 'type=', 'pattern='])
    except getopt.GetoptError:
        print("given options are not correct.")
        sys.exit(-1)
    host_ip = []
    board_type = []
    pattern = []
    for o, a in options:
        # Help message
        if o == "-h" or o == "--help": help(); sys.exit(0)
        # Specifying host interface address
        elif o == "-i" or o == "--if": check_ifaddr(host_ip, a); continue
        # Specifying board type
        elif o == "-t" or o == "--type": check_type(board_type, a); continue
        # Specifying match patterns of MAC address
        elif o == "-p" or o == "--pattern": pattern.append(a.lower()); continue
        # Unknown
        else:
            print("Unknown option") # never come here
            sys.exit(-1)
    try:
        if len(host_ip) == 0: host_ip = get_interfaces()
        for b in board_type:
            print("Finding", b)
            for ip in host_ip:
                boards = BOARD_TYPES[b][2](ip)
                print("")
                print(len(boards), b, "found on", ip)
                if len(boards) != 0:
                    print_boards(boards)
        for p in pattern:
            print("Finding IPs with MAC address: ", p)
            for ip in host_ip:
                boards = get_mac_matched_ip(ip, p)
                print("")
                print(len(boards), "boards found on", ip)
                if len(boards) != 0:
                    print_boards(boards)
        return 0
    except:
        return -1
# end of main
#------------------------------------------------------------

#============================================================
# GUI application
import tkinter.ttk as ttk  # Python31+
import tkinter as Tk
from tkinter.font import Font as tkFont

class AsyncInvoker(Thread):
    def __init__(self, func):
        Thread.__init__(self)
        self.func = func
    def run(self):
        self.func()

#------------------------------------------------------------
# Terminal launcher
class Launcher:
    def __init__(self, cmd, appdir, path = None):
        self.win_bin  = []
        tmp = ("PROGRAMFILES", "PROGRAMFILES(x86)", "PROGRAMW6432")
        for e in tmp:
            import os
            env = os.environ.get(e)
            if env != None:
                self.win_bin.append(env.replace('\\', '/'))
        self.unix_bin = ["/usr/bin", "/usr/X11R6/bin",
                  "/usr/local/bin", "/bin",
                  "/opt/bin", "/opt/local/bin",
                  "/sbin", "/usr/sbin"]
        self.macos_bin = ["/usr/bin", "/usr/sbin",
                    "/usr/local/bin", "/usr/local/sbin",
                    "/Applications/",
                    "/Applications/Utilities/",
                    "/System/Applications/",
                    "/System/Applications/Utilities"]
        if path != None:
            self.win_bin.append(path)
            self.unix_bin.append(path)
            self.macos_bin.append(path)
        self.cmd = cmd
        self.appdir = appdir
        self.path = path
        self.cmd_path = None
        self.check_availability()
    def __del__(self):
        self.finalize()

    def check_availability(self):
        import platform
        dprint("check_availability => system(): " + platform.system() + '\n')
        if   platform.system() == 'Windows':
            bin_path = self.win_bin
        elif platform.system() == 'Darwin':
            bin_path = self.macos_bin
        elif platform.system() == 'Linux':
            bin_path = self.unix_bin
        else: # other OS
            sys.stderr.write("Unsupported OS\n")
        dprint("bin_path: " + '\n'.join(bin_path) + '\n')
        for p in bin_path:
            path = p + '/' + self.appdir + '/' + self.cmd
            if os.path.exists(path):
                self.cmd_path = path
                dprint(self.cmd + "is available")
                return True
        dprint(self.cmd + "not available")
        return None

    def is_available(self):
        if self.cmd_path == None:
            dprint(self.cmd + " not available\n")
            return False
        dprint(self.cmd + " available\n")
        return True

    def invoke_cmd(self):
        pass

    def launch(self, host, user, passwd, port = "22"):
        self.host = host
        self.user = user
        self.passwd = passwd
        self.port = port
        self.th = AsyncInvoker(self.invoke_cmd)
        self.th.start()

    def finalize(self):
        pass

#------------------------------------------------------------
# Teraterm launcher
#------------------------------------------------------------
class TeraTerm(Launcher):
    def __init__(self, cmd = "ttermpro.exe", appdir = "TeraTerm", path = None):
        Launcher.__init__(self, cmd, appdir, path)

    def invoke_cmd(self):
        cmd_array = [self.cmd_path,
                    self.host+':'+self.port,
                    '/user='+self.user,
                    '/passwd='+self.passwd]
        dprint("TeraTerm CMD: " + ' '.join(cmd_array) + "\n")
        Popen(cmd_array, shell = True, **popen_args())

#------------------------------------------------------------
# Linux's generic Terminal App launcher
#------------------------------------------------------------
class LinuxTerminal(Launcher):
    def __init__(self, cmd = "xterm", options = "", appdir = "", path = None):
        Launcher.__init__(self, cmd, appdir, path)
        self.login_sh_file = None
        self.options = options

    def invoke_cmd(self):
        # expect script for Terminal.app
        if os.path.exists("/usr/bin/expect"):
            login_sh = """#!/usr/bin/expect
spawn ssh -p %s %s@%s
match_max 100000
expect "*?assword:*"
send -- "%s\r"
send -- "\r"
interact
""" % (self.port, self.user, self.host, self.passwd)
        else:
            login_sh = """#!/bin/bash

echo "'expect' command not found"
echo "To omit the password input, install expect command."
echo "Ubuntu/Debian: apt install expect"
echo ""
echo "Plase input password: %s"
ssh -p %s %s@%s
""" % (self.passwd, self.port, self.user, self.host)

        dprint("login shell script for " + self.cmd + "\n")
        dprint(login_sh + "\n")

        # creating login script on TEMP dir
        temp_dir = os.environ.get("TEMP")
        if temp_dir == None: temp_dir = "/tmp"
        self.login_sh_file = temp_dir + "/login_" + self.host + ".sh"
        fd = open(self.login_sh_file, "w")
        fd.write(login_sh)
        fd.close()
        dprint("Login script created: " + self.login_sh_file + "\n")
        os.system("chmod 755 " + self.login_sh_file)
        # launch Terminal.app
        cmd = self.cmd + " " + self.options + " " + self.login_sh_file
        Popen(cmd, shell = True,  **popen_args())
        dprint(cmd + '\n')

    def finalize(self):
        if self.login_sh_file:
            os.remove(self.login_sh_file)

#------------------------------------------------------------
# Gnome terminal launcher
#------------------------------------------------------------
class GnomeTerminal(LinuxTerminal):
    def __init__(self, cmd = "gnome-terminal", options = "--", appdir = "", path = None):
        LinuxTerminal.__init__(self, cmd, options, appdir, path)

class Xterm(LinuxTerminal):
    def __init__(self, cmd = "xterm", options = "-e", appdir = "", path = None):
        LinuxTerminal.__init__(self, cmd, options, appdir, path)

class Kterm(LinuxTerminal):
    def __init__(self, cmd = "kterm", options = "-e", appdir = "", path = None):
        LinuxTerminal.__init__(self, cmd, options, appdir, path)

#------------------------------------------------------------
# Poderosa launcher
#------------------------------------------------------------
class Poderosa(Launcher):
    def __init__(self, cmd = "poderosa.exe", appdir = "Poderosa Terminal 5",
                path = None):
        Launcher.__init__(self, cmd, appdir, path)
        self.gts_file = None

    def invoke_cmd(self):
        gts = """<?xml version=\"1.0\" encoding=\"shift_jis\"?>
<poderosa-shortcut version=\"4.0\">
  <Poderosa.Terminal.TerminalSettings encoding=\"utf-8\" caption=\"%s\" />
  <Poderosa.Protocols.SSHLoginParameter destination=\"%s\"
                                        port=\"%s\"
                                        account=\"%s\"
                                        passphrase=\"%s\" />
</poderosa-shortcut>""" % (self.host, self.host, self.port,
                           self.user, self.passwd)
        temp_dir = os.environ.get("TEMP")
        if temp_dir == None: temp_dir = "C:/"
        self.gts_file = temp_dir + "/" + self.host + ".gts"
        dprint("Poderosa's gts file: " + self.gts_file + "\n")
        fd = open(self.gts_file, "w")
        fd.write(gts)
        fd.close()
        cmd_str = "\"%s\" -open \"%s\"" % (self.cmd_path, self.gts_file)
        dprint("Poderosa CMD: " + cmd_str + "\n")
        Popen(cmd_str, shell = True, **popen_args())

    def finalize(self):
        if self.gts_file:
            os.remove(self.gts_file)

#------------------------------------------------------------
# Putter launcher
#------------------------------------------------------------
class PuTTY(Launcher):
    def __init__(self, cmd = "putty.exe", appdir = "PuTTY", path = None):
        Launcher.__init__(self, cmd, appdir, path)

    def invoke_cmd(self):
        cmd_str = "\"%s\" -ssh %s@%s:%s -pw \"%s\"" \
        % (self.cmd_path, self.user, self.host, self.port, self.passwd)
        dprint("Putty CMD: " + cmd_str + "\n")
        Popen(cmd_str, shell = True,  **popen_args())

#------------------------------------------------------------
# Mac's generic Terminal App launcher
#------------------------------------------------------------
class MacTermApp(Launcher):
    def __init__(self, cmd = "Terminal.app", appdir = "", path = None):
        Launcher.__init__(self, cmd, appdir, path)
        self.login_sh_file = None

    def invoke_cmd(self):
        # expect script for Terminal.app
        login_sh = """#!/usr/bin/expect
spawn ssh -p %s %s@%s
match_max 100000
expect "*?assword:*"
send -- "%s\r"
send -- "\r"
interact
""" % (self.port, self.user, self.host, self.passwd)
        dprint("login shell script for Terminal.app\n")
        dprint(login_sh + "\n")

        # creating login script on TEMP dir
        temp_dir = os.environ.get("TEMP")
        if temp_dir == None: temp_dir = "/tmp"
        self.login_sh_file = temp_dir + "/login_" + self.host + ".sh"
        fd = open(self.login_sh_file, "w")
        fd.write(login_sh)
        fd.close()
        dprint("Login script created: " + self.login_sh_file + "\n")
        os.system("chmod 755 " + self.login_sh_file)
        # launch Terminal.app
        cmd = "/usr/bin/open -n -a " + self.cmd + " " + self.login_sh_file
        Popen(cmd, shell = True,  **popen_args())
        dprint(cmd + '\n')

    def finalize(self):
        if self.login_sh_file:
            os.remove(self.login_sh_file)

#------------------------------------------------------------
# Mac's default Terminal.app launcher
#------------------------------------------------------------
class TerminalApp(MacTermApp):
    def __init__(self, cmd = "Terminal.app", appdir = "", path = None):
        MacTermApp.__init__(self, cmd, appdir, path)

#------------------------------------------------------------
# iTerm.app launcher
#------------------------------------------------------------
class iTermApp(MacTermApp):
    def __init__(self, cmd = "iTerm.app", appdir = "", path = None):
        MacTermApp.__init__(self, cmd, appdir, path)

TERM_TYPES = {
    "gnome-terminal": GnomeTerminal(),
    "xterm":          Xterm(),
    "kterm":          Kterm(),
    "TeraTerm":       TeraTerm(),
    "Poderosa":       Poderosa(),
    "PuTTY"   :       PuTTY(),
    "Terminal.app":   TerminalApp(),
    "iTerm.app":      iTermApp()
    }

# end of Terminal Launcher
#------------------------------------------------------------

#------------------------------------------------------------
# GUI application body
class App(ttk.Frame):
    def __init__(self, master = None):
        ttk.Frame.__init__(self, master)
        # Member variables
        self.ifaddrs = []
        self.pattern = Tk.StringVar(value = "b8:27:eb:[a-f0-9:]*")
        self.board_types = []
        self.sort_dir = True
        self.scan_type = Tk.StringVar(value = "board")
        self.scanning_on = ""
        self.scanning = False
        self.tselected = None
        self.login_infos = ("User name", "Password", "Port")

        # GUi style configuration
        sty = ttk.Style()
        sty.configure('.', font = ('*', 12))
        self.option_add('*font', '* 12');
        self.option_add('*LabelFrame.font', '* 12');
        self.option_add('*Button.font', '* 12');
        self.option_add('*Entry.font', '* 12');
        self.label_width = 16
        self.radio_width = self.label_width - 2
        self.entry_width = 16

        # Top level frame
        self.master.title('xfinder')
        # left pane
        self.w_fleft = ttk.Frame(self.master, width = 40)
        self.w_fleft.pack(side = Tk.LEFT)
        # left top pane
        self.w_fleft_top = ttk.LabelFrame(self.w_fleft, text = "Scan settings")
        self.w_fleft_top.pack(pady = 10, padx = 10, fill=Tk.X, side = Tk.TOP)
        self.create_left_top(self.w_fleft_top)
        # left bottom pane
        self.w_fleft_bottom = ttk.LabelFrame(self.w_fleft,
                                             text = "Terminal launcher")
        self.w_fleft_bottom.pack(pady = 10, padx = 10, fill=Tk.X, side = Tk.TOP)
        self.create_left_bottom(self.w_fleft_bottom)
        # right pane
        self.w_fright = Tk.LabelFrame(self.master, text = "Found nodes")
        self.w_fright.pack(pady = 10, padx = 10, fill = Tk.Y, side = Tk.LEFT)
        self.create_right(self.w_fright)

    def create_left_top(self, w):
        self.create_ifaddr_combo(w)
        self.create_type_combo(w)
        self.create_pattern_textbox(w)
        self.create_scan_button(w)
        self.create_progressbar(w)

    def create_left_bottom(self, w):
        self.create_login_info(w)
        self.create_term_selector(w)
        self.create_login_button(w)

    def create_right(self, w):
        self.create_node_list(w)

    # left top pane (1)
    def create_ifaddr_combo(self, w):
        self.w_ifaddr_label = ttk.Label(w, text = "Interface address",
                                        width = self.label_width)
        self.w_ifaddr_label.grid(row = 0, column = 0, padx = 10, pady = 5,
                                 sticky = Tk.W + Tk.E)
        iflist = ['ALL'] + get_interfaces()
        self.w_ifaddr = ttk.Combobox(w, values = iflist,
                                     width = self.entry_width,
                                     state = 'readonly')
        self.w_ifaddr.set('ALL')
        self.w_ifaddr.grid(row = 0, column = 1, padx = 10, pady = 5,
                           sticky = Tk.W + Tk.E)
        self.w_ifaddr.bind('<<ComboboxSelected>>', self.select_ifaddr)

    # left top pane (2)
    def create_type_combo(self, w):
        # Radiobutton
        self.w_btype_radio = ttk.Radiobutton(w, text = "Board type",
                                             width = self.radio_width,
                                             variable = self.scan_type,
                                             value = "board")
        self.w_btype_radio.grid(row = 1, column = 0,
                                padx = 10, pady = 5, sticky = Tk.W)
        # Combobox
        types = list(BOARD_TYPES.keys())
        self.w_btype = ttk.Combobox(w, values = types,
                                    width = self.entry_width,
                                    state = 'readonly')
        self.w_btype.set(list(BOARD_TYPES.keys())[0])
        self.w_btype.grid(row = 1, column = 1, padx = 10, pady = 5)
        self.w_btype.bind('<<ComboboxSelected>>', self.select_types)

    # left top pane (3)
    def create_pattern_textbox(self, w):
        # Radiobutton
        self.w_pattern_radio = ttk.Radiobutton(w, text = "Match pattern",
                                               width = self.radio_width,
                                               variable = self.scan_type,
                                               value = "pattern")
        self.w_pattern_radio.grid(row = 2, column = 0,
                                  padx = 10, pady = 5, sticky = Tk.W)
        # Entry
        self.w_pattern = ttk.Entry(w, width = self.entry_width,
                                   textvariable = self.pattern)
        self.w_pattern.grid(row = 2, column = 1, pady = 5, padx = 10,
                            sticky = Tk.W + Tk.E)

    # left top pane (4)
    def create_scan_button(self, w0):
        w = ttk.Frame(w0)
        w.grid(row = 3, column = 0, columnspan = 2, padx = 10, pady = 5)
        self.w_scan = Tk.Button(w, text = 'Scan',
                                width = self.label_width - 1, height = 1,
                                pady = 5, padx = 5,
                                command = self.do_scan)
        self.w_scan.grid(row = 0, column = 0, padx = 0, pady = 5,
                         sticky = Tk.W + Tk.E)
        self.w_abort = Tk.Button(w, text = "Abort",
                                width = self.label_width - 1, height = 1,
                                pady = 5, padx = 5,
                                command = self.do_abort)
        self.w_abort.grid(row = 0, column = 11, padx = 0, pady = 5,
                         sticky = Tk.W + Tk.E)
        self.w_abort["state"] = Tk.DISABLED

    # left top pane (5)
    def create_progressbar(self, w):
        self.w_progress = ttk.Progressbar(w,
                                          orient = "horizontal",
                                          mode = "determinate")
        self.w_progress.grid(row = 4, column = 0, columnspan = 2,
                             padx = 10, pady = 5, sticky = Tk.W + Tk.E)
        self.w_proglabel = ttk.Label(w, anchor = Tk.CENTER,
                                     justify = Tk.CENTER)
        self.w_proglabel.grid(row = 5, column = 0, columnspan = 2,
                             padx = 10, pady = 5, sticky = Tk.W + Tk.E)

    def get_avail_term_types(self):
        types = []
        for ttype in TERM_TYPES.keys():
            if TERM_TYPES[ttype].is_available():
                types.append(ttype)
        types.sort(); types.reverse()
        return types

    # left bottom (1)
    def create_login_info(self, w):
        self.w_llabel = {}
        self.w_lentry = {}
        self.lvar = {}
        for i, l in enumerate(self.login_infos):
            self.w_llabel[l] = ttk.Label(w, text = l, width = self.label_width,
                                         anchor = Tk.W)
            self.w_llabel[l].grid(row = i, column = 0, padx = 10, pady = 5,
                                  sticky = Tk.W + Tk.E)
            self.lvar[l] = Tk.StringVar()
            self.w_lentry[l] = ttk.Entry(w, width = self.entry_width,
                                         textvariable = self.lvar[l])
            self.w_lentry[l].grid(row = i, column = 1, padx = 10, pady = 5,
                                  sticky = Tk.W + Tk.E)

    # left bottom (2)
    def create_term_selector(self, w):
        self.w_tlabel = ttk.Label(w, text = "Terminal App",
                                  width = self.label_width,
                                  anchor = Tk.W)
        self.w_tlabel.grid(row = len(self.login_infos), column = 0,
                           pady = 5, padx = 10,
                           sticky = Tk.W + Tk.E)
        types = self.get_avail_term_types()
        self.w_ttype = ttk.Combobox(w, values = types,
                                    width = self.entry_width,
                                    state = 'readonly')
        if len(types) > 0: 
          self.w_ttype.set(types[0])
        self.w_ttype.grid(row = len(self.login_infos), column = 1,
                          pady = 5, padx = 10,
                          sticky = Tk.W + Tk.E)

    # left bottom (3)
    def create_login_button(self, w):
        self.w_lbutton = Tk.Button(w, text = "Login",
                                    highlightbackground="#ececec",
                                    width = 20, height = 1, pady = 5, padx = 5,
                                    command = self.login)
        self.w_lbutton["state"] = Tk.DISABLED
        self.w_lbutton.grid(row = len(self.login_infos) + 1,
                            column = 0, columnspan = 2,
                            pady = 5, padx = 10, sticky=Tk.W + Tk.E)
        self.select_types() # set login name and password

    # [callback] login button
    def login(self, event = None):
        if len(self.tree.selection()) == 0:
            return
        self.host = self.tree.item(self.tree.selection())["values"][0]
        self.user = self.w_lentry["User name"].get()
        self.passwd = self.w_lentry["Password"].get()
        self.port = self.w_lentry["Port"].get()
        TERM_TYPES[self.w_ttype.get()].launch(self.host, self.user, self.passwd,
                                            self.port)
    # [callback] treeview
    def treeview_press(self, event = None):
        if len(self.tree.selection()) > 0:
            self.tselected = self.tree.selection()[0]
        self.w_lbutton["state"] = Tk.ACTIVE

    # [callback] treeview
    def treeview_release(self, event = None):
        if self.tselected == self.tree.focus():
            self.tree.selection_remove(self.tree.focus())
            self.tselected = None
            self.w_lbutton["state"] = Tk.DISABLED

    # right pane
    def create_node_list(self, w):
        self.dataCols = ('IP address', 'MAC address', 'Host name')
        self.tree = ttk.Treeview(w, columns = self.dataCols,
                                 selectmode = "browse",
                                 show = 'headings')
        self.tree.bind('<Button-1>', self.treeview_press)
        self.tree.bind('<ButtonRelease-1>', self.treeview_release)
        self.tree.bind('<Double-Button-1>', self.login)

        ysb = ttk.Scrollbar(orient = Tk.VERTICAL, command = self.tree.yview)
        xsb = ttk.Scrollbar(orient = Tk.HORIZONTAL, command = self.tree.xview)
        self.tree['yscroll'] = ysb.set
        self.tree['xscroll'] = xsb.set

        # add tree and scrollbars to frame
        self.tree.grid(in_ = w, row = 0, column = 0, sticky = Tk.NSEW)
        ysb.grid(in_ = w, row = 0, column = 1, sticky = Tk.NS)
        xsb.grid(in_ = w, row = 1, column = 0, sticky = Tk.EW)

        # set frame resize priorities
        w.rowconfigure(0, weight = 1)
        w.columnconfigure(0, weight = 1)

        # sort function
        def treeview_sort_column(tree, col, reverse):
            l = [(tree.set(k, col), k) for k in tree.get_children('')]
            l.sort(reverse = reverse)
            # rearrange items in sorted positions
            for index, (val, k) in enumerate(l):
                tree.move(k, '', index)
                # reverse sort next time
                tree.heading(col,
                           command = lambda col_ = col:
                           treeview_sort_column(tree, col_, not reverse))

        for col in self.dataCols:
            self.tree.heading(col, text = col,
                              command = lambda col_ = col:
                              treeview_sort_column(self.tree, col_, False))
            self.tree.column(col, width = 150)

    # [callback] Interface Combobox
    def select_ifaddr(self, event = None):
        value = self.w_ifaddr.get()
        if value == "ALL":
            self.ifaddrs = get_interfaces()
        else:
            self.ifaddrs = [value]
        if len(self.ifaddrs) == 0 or self.ifaddrs == None:
            sys.stderr.write("No available network interfaces.")

    # [callback] Board type Combobox
    def select_types(self, event = None):
        value = self.w_btype.get()
        if value == "ALL":
            self.board_types = BOARD_TYPES.keys()
            self.lvar["User name"].set(BOARD_TYPES["Raspberry"][1]["login"])
            self.lvar["Password"].set(BOARD_TYPES["Raspberry"][1]["passwd"])
            self.lvar["Port"].set(BOARD_TYPES["Raspberry"][1]["port"])
        elif value in BOARD_TYPES:
            self.board_types = [value]
            self.lvar["User name"].set(BOARD_TYPES[value][1]["login"])
            self.lvar["Password"].set(BOARD_TYPES[value][1]["passwd"])
            self.lvar["Port"].set(BOARD_TYPES[value][1]["port"])
        else:
            sys.stderr.write("Invalid board types.\n")
        if len(self.board_types) == 0 or self.board_types == None:
            sys.stderr.write("No available board types.\n")

    # setting host/mac/hostname in the treeview
    def set_scan_data_item(self, ip_addr, mac_addr):
        import socket
        try:
            host_name = socket.gethostbyaddr(ip_addr)[0]
        except:
            host_name = ""
        row_data = (ip_addr, mac_addr, host_name)
        self.tree.insert('', 'end', values = row_data)
        for idx, val in enumerate(row_data):
            tf = tkFont(root)
            iwidth = tf.measure(text = val)
            if self.tree.column(self.dataCols[idx], 'width') < iwidth:
                self.tree.column(self.dataCols[idx], width = iwidth)

    # setting host/mac/hostname in the treeview
    def set_scan_data(self, addr_list):
        for ip_addr, mac_addr in addr_list.items():
            AsyncInvoker(lambda ip_addr_ = ip_addr, mac_addr_ = mac_addr, :
                         self.set_scan_data_item(ip_addr_, mac_addr_)).start()

    # cleanup treeview
    def clear_treeview(self):
        self.tree.delete(*self.tree.get_children())

    # progress bar
    def advance_progress(self):
        pre_val = self.w_progress["value"]
        if PingAgent.max_count == 0:
            val = 100
        else:
            val = (PingAgent.count * 100.0) / PingAgent.max_count

        self.w_progress["value"] = pre_val * 0.8 + val * 0.2
        if val == 100: self.w_progress["value"] = 100
        percent = str(int(val))
        text  = "Scanning on " + self.scanning_on + "  "
        text += " " * ((3 - len(percent)) * 2)
        text += percent + "%"
        self.w_proglabel["text"] = text
        if PingAgent.count < PingAgent.max_count:
            if not self.scanning:
                self.reverse_progress()
                self.w_proglabel["text"] = "Aborting..."
                return
            self.after(20, self.advance_progress)

    def reverse_progress(self):
        self.w_progress["value"] = self.w_progress["value"] - 0.5
        if self.w_progress["value"] > 0:
            self.after(20, self.reverse_progress)

    # [callback] scan button
    def do_scan(self, event = None):
        self.w_scan["state"] = Tk.DISABLED
        self.w_abort["state"] = Tk.ACTIVE
        self.w_progress["value"] = 0
        self.clear_treeview()
        self.select_ifaddr()
        self.scanning = True
        # Scan by board type
        if self.scan_type.get() == "board":
            AsyncInvoker(self.scan_by_boardtype).start()
        elif self.scan_type.get() == "pattern":
            AsyncInvoker(self.scan_by_pattern).start()
        else:
            print("Invalid scan type: ", self.scan_type.get())

    def do_abort(self, event = None):
        if self.scanning:
            Pinger.abort()
            self.scanning = False

    # scanning by board type
    def scan_by_boardtype(self):
        self.select_types()
        for b in self.board_types:
            if not self.scanning: break
            for ip in self.ifaddrs:
                if not self.scanning: break
                self.scanning_on = ip
                self.after(100, self.advance_progress)
                boards = BOARD_TYPES[b][2](ip, self.set_scan_data_item)
                msg = str(len(boards)) + " " + b + " found on " + ip
                self.w_proglabel["text"] = msg
                self.w_progress["value"] = 0
                time.sleep(2)
        self.w_proglabel["text"] = "Done"
        self.w_scan["state"] = Tk.ACTIVE
        self.w_abort["state"] = Tk.DISABLED
        self.scanning = False

    # scanning by MAC pattern
    def scan_by_pattern(self):
        for ip in self.ifaddrs:
            if not self.scanning: break
            self.scanning_on = ip
            self.after(100, self.advance_progress)
            boards = get_mac_matched_ip(ip, self.pattern.get(),
                                        self.set_scan_data_item)
            msg = str(len(boards)) + " boards found on " + ip
            self.w_proglabel["text"] = msg
            time.sleep(2)
        self.w_proglabel["text"] = "Done"
        self.w_scan["state"] = Tk.ACTIVE
        self.w_abort["state"] = Tk.DISABLED
        self.scanning = False

#------------------------------------------------------------
# GUI main function
#------------------------------------------------------------
root = None
def sigint_handler(signum, stack):
    global root
    root.quit()
    root.update()
    root.destroy()

def resource_path(relative):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative)
    return os.path.join(relative)

def gui_main():
    global root
    import signal
    try:
        PingAgent.verbose(False)
        signal.signal(signal.SIGINT, sigint_handler)
        signal.signal(signal.SIGTERM, sigint_handler)
        root =Tk.Tk()
        App(root)
        root.title("xfinder")
        import platform
        pf = platform.system()
        dprint("Platform type is: " + pf)
        if pf == "Windows":
            root.iconbitmap(bitmap = resource_path("icons/raspi.ico"))
        elif pf == "Darwin":
            pass # Mac OS X never appear titlebar icon
        else:
            pass
#            root.iconbitmap(bitmap = resource_path("icons/raspi.png"))
        root.update()
        root.mainloop()
    except:
        print("Unexpected error in gui_main():",
            sys.exc_info()[0])
        raise
    sys.exit(0)

#------------------------------------------------------------
# main function
#------------------------------------------------------------
if __name__ == '__main__':
    import sys
    import getopt
    if not sys.argv[0].find("pifinder") < 0:
        sys.argv.append("-t")
        sys.argv.append("pi")
        sys.exit(cui_main())
    elif not sys.argv[0].find("bbfinder") < 0:
        sys.argv.append("-t")
        sys.argv.append("bb")
        sys.exit(cui_main())
    else:
        if len(sys.argv) == 1:
            sys.exit(gui_main())
        else:
            sys.exit(cui_main())
    sys.exit(-1)
# end of script
#============================================================
