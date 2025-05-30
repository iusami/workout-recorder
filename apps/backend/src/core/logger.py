import logging
import sys

from src.core.config import settings

# アプリケーション全体で使うロガーの名前を定義
# これにより、他のモジュールから同じ名前でロガーを取得できます
APP_LOGGER_NAME = 'WorkoutRecorderAPI'


def setup_logger():
    """
    アプリケーション用の共通ロガーを設定します。
    """
    # APP_LOGGER_NAME でロガーインスタンスを取得
    logger = logging.getLogger(APP_LOGGER_NAME)

    # 既にハンドラが設定されている場合は、重複を避けるために一度クリアする
    # (特にUvicornのリロード時などに有効)
    if logger.hasHandlers():
        logger.handlers.clear()

    # 設定ファイルからログレベルを取得し、大文字に変換
    # loggingモジュールで使えるように数値レベルに変換
    log_level_str = str(settings.LOG_LEVEL).upper()
    numeric_level = getattr(logging, log_level_str, logging.INFO)
    logger.setLevel(numeric_level)

    # フォーマッターを定義
    # %(asctime)s: ログ記録時刻
    # %(name)s: ロガー名
    # %(levelname)s: ログレベル名
    # %(filename)s:%(lineno)d: ファイル名と行番号
    # %(module)s: モジュール名
    # %(funcName)s: 関数名
    # %(message)s: ログメッセージ
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d %(funcName)s] - %(message)s'  # noqa: E501
    )

    # コンソール出力用のハンドラ (StreamHandler) を作成
    # Docker環境では sys.stdout を使うのが一般的
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    # (オプション) ファイル出力ハンドラも追加できます
    # file_handler = logging.FileHandler("app.log")
    # file_handler.setFormatter(formatter)
    # logger.addHandler(file_handler)

    # (オプション) このロガーのメッセージがルートロガーに伝播しないようにする
    # logger.propagate = False

    logger.info("Logger '%s' configured with level %s", APP_LOGGER_NAME, log_level_str)
