import sys
import warnings

sys.dont_write_bytecode = True
warnings.filterwarnings( 'ignore' )

import time
import argparse

from dataclasses import dataclass
from typing import Optional

from log.log import Log
from telegram.telegram_common import TelSocket
from telegram.telegram_common import AcpSocket
from telegram.telegram_common import SocketSelect

# メモ
# ラズベリーパイの中で稼働する

@dataclass
class Parameters:
    ctrl_ip: str
    ctrl_port: int
    job_port: int

lg: Log = Log(0, "gw1")

def main() -> None:

    args = parse_args()
    main_proc(args)

    return


def main_proc(args: Parameters) -> None:

    # 制御用のソケットを開く
    not_stb: bool = True
    while not_stb:
        ctl: TelSocket = TelSocket()
        res = ctl.connect(args.ctrl_ip, args.ctrl_port)
        if res == False:
            lg.output("ERR", "制御ソケット接続失敗")
            time.sleep(5)
            continue

        lg.output("INF", "制御ソケット接続成功")
        ctl.set_name( "ctrl" )
        not_stb = False

    job_soks: list[TelSocket] = []
    job_soks.append(ctl)

    while True:
        s = SocketSelect.select([], job_soks)

        if len(s) == 0:
            continue

        for i in s:
            if i.name == "ctrl":
                lg.output("INF", "制御ソケットからの受信")

                # 制御ソケットからの受信
                bt_jnum = i.receive_raw(4)
                lg.output_dump("DBG", bt_jnum)
                st_jnum = bt_jnum.decode()

                bt_size = i.receive_raw(8)
                lg.output_dump("DBG", bt_size)
                st_size = bt_size.decode()
                it_size = int(st_size)

                if it_size > 0:
                    bt_data = i.receive_raw(it_size)
                    lg.output_dump("DBG", bt_data)

                    sck: Optional[TelSocket] = None
                    for job_sock in job_soks:
                        if job_sock.name == st_jnum:
                            sck = job_sock
                            lg.output("INF", "既存ジョブソケット [" + st_jnum + "]")
                            break
                    if sck is None:
                        sck = TelSocket()
                        res = sck.connect("127.0.0.1", args.job_port)
                        if res == False:
                            # 処理異常
                            lg.output("ERR", "ジョブソケット接続失敗")
                            continue
                        lg.output("INF", "ジョブソケット接続成功 [" + st_jnum + "]")
                        sck.set_name(st_jnum)
                        job_soks.append(sck)    
                    sck.send_raw(bt_data)
                    lg.output("INF", "ジョブソケットに送信 [" + st_jnum + "]")
                    lg.output_dump("DBG", bt_data)
                else:
                    # ジョブソケットを切断
                    for job_sock in job_soks:
                        if job_sock.name == st_jnum:
                            job_sock.close()
                            lg.output("INF", "ジョブソケット切断 [" + st_jnum + "]")
                            job_soks.remove(job_sock)
                            break
            else:
                lg.output("INF", "ジョブソケットからの受信 [" + i.name + "]")

                # ジョブソケットからの受信
                st_jnum = i.name
                bt_jnum = st_jnum.encode()

                bt_data = i.receive_raw(2048)
                lg.output_dump("DBG", bt_data)

                if bt_data is None or len(bt_data) == 0:
                    it_size = 0
                else:
                    it_size = len(bt_data)
                st_size = str(it_size).zfill(8)
                bt_size = st_size.encode()

                lg.output("INF", "制御ソケットに送信")
                ctl.send_raw(bt_jnum)
                lg.output_dump("DBG", bt_jnum)
                ctl.send_raw(bt_size)
                lg.output_dump("DBG", bt_size)
                if it_size > 0:
                    ctl.send_raw(bt_data)
                    lg.output_dump("DBG", bt_data)
                if it_size <= 0:
                    i.close()
                    job_soks.remove(i)
                    lg.output("INF", "ジョブソケット切断 [" + st_jnum + "]")
    

    return


def parse_args() -> Parameters:
    """コマンドライン引数解析処理

    Returns:
        Parameters: 解析結果格納オブジェクト
    """

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--ctrl_ip",
        type=str,
        required=True,
        help="コントロール用IPアドレス",
    )
    parser.add_argument(
        "--ctrl_port",
        type=int,
        required=True,
        help="コントロール用ポート番号",
    )
    parser.add_argument(
        "--job_port",
        type=int,
        required=True,
        help="ジョブ用ポート番号",
    )

    args = parser.parse_args()

    params = Parameters(
        ctrl_ip=args.ctrl_ip,
        ctrl_port=args.ctrl_port,
        job_port=args.job_port,
    )

    return params


if __name__ == "__main__":
    main()
