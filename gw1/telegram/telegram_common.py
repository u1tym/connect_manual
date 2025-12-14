import sys
import warnings

sys.dont_write_bytecode = True
warnings.filterwarnings('ignore')

import socket
import select

from typing import Optional
from typing import Union
from typing import Tuple

class TelSocket:

    def __init__(self) -> None:
        self.name: str = "noname"
        self.sock: Optional[socket.socket] = None
        self.siz_msgsiz = 8

    def connect(self, ip: str = "127.0.0.1", port: int = 50001) -> bool:
        """接続処理

        Args:
            ip (str): 接続先IPアドレス
            port (int): 接続先ポート番号

        Returns:
            True: 正常終了
            False: 異常終了
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect((ip, port))
        except:
            return False
        self.build(sock)
        return True

    def close(self) -> None:
        """切断処理

        Args:
            なし

        Returns:
            なし
        """
        if self.sock is not None:
            self.sock.close()
        self.sock = None

    def build(self, sock: socket.socket) -> None:
        """構築処理"""
        self.sock = sock

    def set_name(self, name: str) -> None:
        """命名処理"""
        self.name = name

    def send_raw(self, data: bytes) -> None:
        """生送信

        Args:
            data (bytes): 送信データ
        Returns:
            なし
        """
        if self.sock is None:
            return
        self.sock.sendall(data)

    def receive_raw(self, length: int) -> Optional[bytes]:
        """生受信

        Args:
            length (int): 受信バイト数
        Returns:
            data (bytes): 受信データ
        """
        if self.sock is None:
            return None
        data = self.sock.recv(length)
        if not data:
            return None
        return data

    def receive(self) -> Tuple[str, int, bytes]:
        """受信処理

        Args:
            なし

        Returns:
            None: 受信処理異常
            data (str): 受信文字列
        """

        bt_unit = self.receive_raw(4)
        if bt_unit is None:
            return ("", 0, b"")
        st_unit = bt_unit.decode()

        bt_size = self.receive_raw(8)
        if bt_size is None:
            return (st_unit, 0, b"")
        st_size = bt_size.decode()
        it_size = int(st_size)

        rem_size = it_size
        bt_data = b""
        while rem_size > 0:
            d = self.receive_raw(rem_size)
            bt_data += d
            rem_size -= len(d)
            if rem_size <= 0:
                break

        return (st_unit, it_size, bt_data)
    
    def send(self, unit: str, bt_data: bytes) -> None:
        """送信処理

        Args:
            unit (str): ユニット文字列
            message (bytes): 送信データ

        Returns:
            なし
        """

        bt_unit = unit.encode()
        st_size = str(len(bt_data)).zfill(8)
        bt_size = st_size.encode()

        self.send_raw( bt_unit + bt_size + bt_data )

        return

class AcpSocket:
    """接続受付ソケットのクラス"""

    def __init__(self) -> None:
        """コンストラクタ"""

        self.ip: str = ""
        self.port: int = 0
        self.listen_count: int = 0
        self.sock: Optional[socket.socket] = None
        return

    def open(self, ip: str = "127.0.0.1", port: int = 50001, num: int = 64) -> bool:
        """接続受付開始

        Args:
            ip (str): 接続受付IPアドレス
            port (int): 接続受付ポート番号
            num (int): 同時接続受付数

        Returns:
            bool: 処理結果
        """

        self.ip = ip
        self.port = port
        self.listen_count = num

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind((self.ip, self.port))

        sock.listen(self.listen_count)
        self.sock = sock

        return True

    def accept(self) -> Optional[TelSocket]:
        """接続受付

        Args:
            なし

        Returns
            None: 異常終了
            TelSockdt: 正常終了
        """

        if self.sock is None:
            return None
        conn, _ = self.sock.accept()

        res = TelSocket()
        res.build(conn)

        return res

    def close(self) -> None:
        if self.sock is None:
            return
        
        self.sock.close()
        self.sock = None
        

class SocketSelect:

    @classmethod
    def select(cls, srv: Optional[AcpSocket], clts: list[TelSocket], timeout: float = 5) -> list[Union[AcpSocket, TelSocket]]:
        lst: list[socket.socket] = []
        if srv is not None and srv.sock is not None:
            lst.append(srv.sock)
        for clt in clts:
            if clt.sock is not None:
                lst.append(clt.sock)

        rs, _, _ = select.select(lst, [], [], timeout)

        if len(rs) == 0:
            return []

        filterd_clts: list[Union[AcpSocket, TelSocket]] = [clt for clt in clts if clt.sock in rs]
        if srv is not None and srv.sock in rs:
            filterd_clts.append(srv)
        return filterd_clts
