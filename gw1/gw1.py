import sys
import warnings

sys.dont_write_bytecode = True
warnings.filterwarnings( 'ignore' )

import argparse

from dataclasses import dataclass
from typing import Optional

from log.log import Log
from socket.telegram_common import TelSocket
from socket.telegram_common import AcpSocket

@dataclass
class Parameters:
    ctrl_ip: str
    ctrl_port: int
    job_port: int
    
def main() -> None:

    args = parse_args()

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
