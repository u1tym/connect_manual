# -*- coding: utf-8 -*-

import sys
import warnings

sys.dont_write_bytecode = True
warnings.filterwarnings('ignore')

import os
import time
import datetime
import math
import inspect

from typing import Literal
from typing import Self

class Log:

	def __init__(self: Self, tid: int, name: str, path: str = "") -> None:

		if len( path ) == 0:
			path = os.extsep

		self.tid = tid

		self.path = path + os.sep + "log-" + name + "-" + str(self.tid) + os.extsep + "log"

		self.f = open( self.path, mode='a', encoding='utf-8' )

		self.ondebug = True
		self.outflag = False


	def __del__(self: Self) -> None:
		if self.f:
			self.f.close()


	def output(self: Self, level: Literal["ERR", "INF", "WRN", "DBG"], message: str) -> None:

		if ( self.ondebug == False ) and ( level == "DBG" ):
			return

		filename = ""
		lineno = 0
		cframe = inspect.currentframe()
		if cframe is not None:
			frame = cframe.f_back
			if frame is not None:
				filename = os.path.basename(frame.f_code.co_filename)
				lineno = frame.f_lineno

		tm = time.time()
		tm_int = math.floor( tm )
		tm_mil = math.floor( tm * 1000 ) - tm_int * 1000
		dt = datetime.datetime.fromtimestamp( tm_int )
		dt_str = '{0:%Y-%m-%d %H:%M:%S}'.format( dt ) + '.' + str( tm_mil ).zfill( 3 )

		msg = ( dt_str
			+ ' [' + level + '] '
			+ '(' + str(self.tid) + ') '
			+ filename + ':' + str(lineno) + ' ' + message )
		if self.outflag:
			print( msg )

		self.f.write( msg + '\n' )
		self.f.flush()

	def debug_on(self: Self) -> None:
		self.ondebug = True

	def debug_off(self: Self) -> None:
		self.ondebug = False

	def print_on(self: Self) -> None:
		self.outflag = True

	def print_off(self: Self) -> None:
		self.outflag = False
