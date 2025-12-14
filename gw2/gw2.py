import sys
import warnings

sys.dont_write_bytecode = True
warnings.filterwarnings( 'ignore' )

import argparse

from dataclasses import dataclass
from typing import Optional
from typing import List

from log.log import Log
from telegram.telegram_common import TelSocket
from telegram.telegram_common import AcpSocket
from telegram.telegram_common import SocketSelect

# メモ
# インターネット上で参照可能なサーバに配置されるプログラム

lg: Log = None
nm: int = 0

@dataclass
class Parameters:
    ctrl_port: int
    job_port: int
    debug: bool
    logfile: str

def main() -> None:

    global lg

    args = parse_args()
    lg = Log(0, args.logfile)
    lg.debug_off()

    if args.debug:
        lg.debug_on()
    main_proc(args)
    return

def main_proc(args: Parameters) -> None:

    global nm

    ctl: AcpSocket = None
    ctl_sock: TelSocket = None

    job: AcpSocket = None

    job_soks: List[TelSocket] = []


    # 制御用のソケットを開く
    ctl = AcpSocket()
    ctl.open("0.0.0.0", args.ctrl_port)
    lg.output("INF", "制御用ソケット受付開始")

    not_stb: bool = True
    while not_stb:
        s = SocketSelect.select(ctl, [])
        if len(s) == 0:
            continue
        for i in s:
            if isinstance(i, AcpSocket):
                ctl_sock = ctl.accept()
                ctl_sock.set_name("ctrl")
                ctl.close()
                lg.output("INF", "制御用ソケット受付接続成功")
                not_stb = False
                break

    job = AcpSocket()
    job.open("0.0.0.0", args.job_port)
    lg.output("INF", "ジョブ用ソケット受付開始 port=" + str(args.job_port))

    job_soks.append(ctl_sock)

    while True:
        s = SocketSelect.select(job, job_soks)
        if len(s) == 0:
            continue

        for i in s:

            # ジョブソケットからの接続受付
            if isinstance(i, AcpSocket):
                job_sock = job.accept()
                nm += 1
                name: str = str(nm).zfill(4)
                job_sock.set_name( name )
                job_soks.append(job_sock)
                lg.output("INF", "ジョブ用ソケット受付接続成功 name=" + name)
            
            # メッセージ受信
            elif isinstance(i, TelSocket):
                job_sock = i

                if i.name == "ctrl":
                    lg.output("INF", "制御ソケットからの受信 name=" + i.name)

                    # 制御ソケットからの受信
                    bt_jnum = i.receive_raw(4)
                    lg.output_dump("INF", bt_jnum)
                    st_jnum = bt_jnum.decode()

                    bt_size = i.receive_raw(8)
                    lg.output_dump("INF", bt_size)
                    st_size = bt_size.decode()
                    it_size = int(st_size)

                    # job_soksの中のTelSocketをチェックし、nameがst_jnumと一致するものを取得
                    for job_sock in job_soks:
                        if job_sock.name == st_jnum:
                            if it_size > 0:
                                bt_data = i.receive_raw(it_size)
                                lg.output_dump("DBG", bt_data)
                                lg.output("INF", "ジョブソケットに送信 name=" + i.name)
                                job_sock.send_raw(bt_data)
                                lg.output_dump("DBG", bt_data)
                            else:
                                # job_sockを切断
                                job_sock.close()
                                job_soks.remove(job_sock)
                                lg.output("INF", "ジョブソケット切断 name=" + i.name)
                            break

                else:
                    # ジョブソケットからの受信
                    lg.output("INF", "ジョブソケットからの受信 name=" + i.name)

                    st_jnum = i.name
                    bt_jnum = st_jnum.encode()
                    bt_data = i.receive_raw(-1)

                    lg.output_dump("DBG", bt_data)
                    it_size = 0
                    if bt_data is not None:
                        it_size = len(bt_data)
                    st_size = str(it_size).zfill(8)
                    bt_size = st_size.encode()

                    lg.output("INF", "制御ソケットに送信 name=" + job_sock.name)
                    ctl_sock.send_raw(bt_jnum)
                    lg.output_dump("INF", bt_jnum)
                    ctl_sock.send_raw(bt_size)
                    lg.output_dump("INF", bt_size)
                    if it_size > 0:
                        ctl_sock.send_raw(bt_data)
                        lg.output_dump("DBG", bt_data)

    return

def parse_args() -> Parameters:
    """コマンドライン引数解析処理

    Returns:
        Parameters: 解析結果格納オブジェクト
    """

    parser = argparse.ArgumentParser()

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
    parser.add_argument(
        "--debug",
        type=bool,
        default=False,
        help="デバッグモード",
    )
    parser.add_argument(
        "--logfile",
        type=str,
        default="gw2",
        help="ログファイル名",
    )

    args = parser.parse_args()

    params = Parameters(
        ctrl_port=args.ctrl_port,
        job_port=args.job_port,
        debug=args.debug,
        logfile=args.logfile,
    )

    return params


if __name__ == "__main__":
    main()
