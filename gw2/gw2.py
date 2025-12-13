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
# インターネット上で参照可能なサーバに配置されるプログラム

@dataclass
class Parameters:
    ctrl_port: int
    job_port: int
    
def main() -> None:

    args = parse_args()
    main_proc(args)
    return

def main_proc(args: Parameters) -> None:

    # 制御用のソケットを開く
    ctl: AcpSocket = AcpSocket()
    ctl.open( "127.0.0.1", args.ctrl_port )

    not_stb: bool = True
    while not_stb:
        s = SocketSelect.select(ctl, [])
        if len(s) == 0:
            continue
        for i in s:
            if isinstance(i, AcpSocket):
                ctl_sock = ctl.accept()
                ctl_sock.set_name( "ctrl" )
                ctl.close()
                not_stb = False
                break

    job: AcpSocket = AcpSocket()
    job.open( "0.0.0.0", args.job_port )

    job_soks: list[TelSocket] = []
    job_soks.append(ctl_sock)

    while True:
        s = SocketSelect.select(job, job_soks)
        if len(s) == 0:
            continue

        for i in s:

            # ジョブソケットからの接続受付
            if isinstance(i, AcpSocket):
                job_sock = job.accept()
                job_sock.set_name( "0000" )
                job_soks.append(job_sock)
            
            # メッセージ受信
            elif isinstance(i, TelSocket):
                job_sock = i

                if i.name == "ctrl":
                    # 制御ソケットからの受信
                    bt_jnum = i.receive_raw(4)
                    st_jnum = bt_jnum.decode()

                    bt_size = i.receive_raw(8)
                    st_size = bt_size.decode()
                    it_size = int(st_size)

                    # job_soksの中のTelSocketをチェックし、nameがst_jnumと一致するものを取得
                    for job_sock in job_soks:
                        if job_sock.name == st_jnum:
                            if it_size > 0:
                                bt_data = i.receive_raw(it_size)
                                job_sock.send_raw(bt_data)
                            else:
                                # job_sockを切断
                                job_sock.close()
                                job_soks.remove(job_sock)
                            break

                else:
                    # ジョブソケットからの受信
                    st_jnum = i.name
                    bt_jnum = st_jnum.encode()
                    bt_data = i.receive_raw(2048)
                    it_size = len(bt_data)
                    st_size = str(it_size).zfill(8)
                    bt_size = st_size.encode()

                    job_sock.send_raw(bt_jnum)
                    job_sock.send_raw(bt_size)
                    job_sock.send_raw(bt_data)

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
        ctrl_port=args.ctrl_port,
        job_port=args.job_port,
    )

    return params


if __name__ == "__main__":
    main()
