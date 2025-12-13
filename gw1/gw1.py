import sys
import warnings

sys.dont_write_bytecode = True
warnings.filterwarnings( 'ignore' )

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
            continue

        ctl.set_name( "ctrl" )
        not_stb = False

    job_soks: list[TelSocket] = []

    while True:
        s = SocketSelect.select(ctl, job_soks)

        if len(s) == 0:
            continue

        for i in s:
            if i.name == "ctrl":
                # 制御ソケットからの受信
                bt_jnum = i.receive_raw(4)
                st_jnum = bt_jnum.decode()

                bt_size = i.receive_raw(8)
                st_size = bt_size.decode()
                it_size = int(st_size)

                if it_size > 0:
                    bt_data = i.receive_raw(it_size)
                    sck: Optional[TelSocket] = None
                    for job_sock in job_soks:
                        if job_sock.name == st_jnum:
                            sck = job_sock
                            break
                    if sck is None:
                        sck = TelSocket()
                        res = sck.connect("127.0.0.1", args.job_port)
                        if res == False:
                            # 処理異常
                            continue
                        sck.set_name(st_jnum)
                        job_soks.append(sck)    
                    sck.send_raw(bt_data)
                else:
                    # ジョブソケットを切断
                    for job_sock in job_soks:
                        if job_sock.name == st_jnum:
                            job_sock.close()
                            job_soks.remove(job_sock)
                            break
            else:
                # ジョブソケットからの受信
                st_jnum = i.name
                bt_jnum = st_jnum.encode()

                bt_data = i.receive_raw(2048)

                if bt_data is None:
                    it_size = 0
                else:
                    it_size = len(bt_data)
                st_size = str(it_size).zfill(8)
                bt_size = st_size.encode()

                ctl.send_raw(bt_jnum)
                ctl.send_raw(bt_size)
                if it_size > 0:
                    ctl.send_raw(bt_data)
                
                if it_size <= 0:
                    i.close()
                    job_soks.remove(i)
    

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
