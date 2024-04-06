# vim:fileencoding=utf-8:noet
from __future__ import (unicode_literals, division, absolute_import, print_function)

import re
import os
import subprocess

from collections import namedtuple

from powerline.lib.shell import run_cmd


TmuxVersionInfo = namedtuple('TmuxVersionInfo', ('major', 'minor', 'suffix'))


def get_tmux_executable_name():
	'''Returns tmux executable name

	It should be defined in POWERLINE_TMUX_EXE environment variable, otherwise 
	it is simply “tmux”.
	'''

	return os.environ.get('POWERLINE_TMUX_EXE', 'tmux')


def _run_tmux(runner, args):
	return runner([get_tmux_executable_name()] + list(args))


def run_tmux_command(*args):
	'''Run tmux command, ignoring the output'''
	_run_tmux(subprocess.check_call, args)


def get_tmux_output(pl, *args):
	'''Run tmux command and return its output'''
	return _run_tmux(lambda cmd: run_cmd(pl, cmd), args)


def set_tmux_environment(varname, value, remove=True):
	'''Set tmux global environment variable

	:param str varname:
		Name of the variable to set.
	:param str value:
		Variable value.
	:param bool remove:
		True if variable should be removed from the environment prior to 
		attaching any client (runs ``tmux set-environment -r {varname}``).
	'''
	run_tmux_command('set-environment', '-g', varname, value)
	if remove:
		try:
			run_tmux_command('set-environment', '-r', varname)
		except subprocess.CalledProcessError:
			# On tmux-2.0 this command may fail for whatever reason. Since it is 
			# critical just ignore the failure.
			pass


def source_tmux_file(fname):
	'''Source tmux configuration file

	:param str fname:
		Full path to the sourced file.
	'''
	run_tmux_command('source', fname)


def build_tmux_output_re():
	pattern = '^' # begin of tmux version output

	pattern += '\s*' # optionnal undefined number of spaces/tabs
	pattern += '\w+' # tmux binary name (ie: "tmux")
	pattern += '\s+' # undefined number of spaces/tabs

	pattern += '(?P<version>' # named group for VERSION (ie: "3.4", "next-3.4", "master", ...)

	pattern += '(?:'                   # non-capturing group for major.minor part
	pattern += '(?:.*?-)?'             # optionnal version prefix (ie: "next-")
	pattern += '(?P<major>\d+)'        # major part of version (ie: "3")
	pattern += '(?:\.(?P<minor>\d+))?' # optional minor part of version (ie: "4")
	pattern += ')'                     # end of non-capturing group

	pattern += '|'                     # or

	pattern += 'master'                # allow "master" as a valid version

	pattern += ')'            # end of VERSION group

	pattern += '\s*'              # optionnal undefined number of spaces/tabs
	pattern += '(?P<suffix>\w+)?' # suffix
	pattern += '\s*'              # optionnal undefined number of spaces/tabs

	pattern += '$'            # end of tmux version output

	return re.compile(pattern)

TMUX_OUTPUT_RE = build_tmux_output_re()

def get_tmux_version(pl):
	version_string = get_tmux_output(pl, '-V')

	m = TMUX_OUTPUT_RE.match(version_string)
	if m.group('version') == 'master':
	    return TmuxVersionInfo(float('inf'), 0, m.group('version'))
	major = m.group('major')
	minor = m.group('minor')
	minor = 0 if minor is None else minor
	suffix = m.group('suffix')
	return TmuxVersionInfo(int(major), int(minor), suffix)
