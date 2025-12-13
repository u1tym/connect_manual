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
from typing import Optional

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

	def output_dump(self: Self, level: Literal["ERR", "INF", "WRN", "DBG"], message: Optional[bytes]) -> None:

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
			+ filename + ':' + str(lineno) + ' Dump' )
		msg += '\n'

		chs: list[str] = []
		chs2: list[str] = []

		mlen: int = 0
		if message is not None:
			mlen = len(message)
		# messageを1バイトずつ取得して繰り返し処理する。
		for i in range(0, mlen):
			# i を16進数で2桁に変換して、chsに追加
			chs.append( format(message[i], '02X') )
			# 文字コードが表示可能な範囲の場合、その文字をchs2に追加。そうでない場合はドットを追加
			if (message[i] >= 0x20) and (message[i] <= 0x7E):
				chs2.append( chr(message[i]) )
			else:
				chs2.append( '.' )
		
		l1: str = ''
		l2: str = ''
		for c in range(0, len(chs)):
			l1 += chs[c]
			l2 += chs2[c]
			if (c + 1) % 16 == 0:
				msg += l1 + '    ' + l2 + '\n'
				l1 = ''
				l2 = ''
			elif (c + 1) % 8 == 0:
				l1 += '  '
				l2 += ' '
			else:
				l1 += ' '
				l2 += ' '
		if len(l1) > 0:
			msg += l1.ljust(16 * 3 + 2, ' ') + '    ' + l2 + '\n'

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
