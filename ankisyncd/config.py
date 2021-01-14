import configparser
import os
import logging
from os.path import dirname, realpath

logger = logging.getLogger("ankisyncd")

paths = [
    "/etc/ankisyncd/ankisyncd.conf",
    os.environ.get("XDG_CONFIG_HOME") and
        (os.path.join(os.environ['XDG_CONFIG_HOME'], "ankisyncd", "ankisyncd.conf")) or
        os.path.join(os.path.expanduser("~"), ".config", "ankisyncd", "ankisyncd.conf"),
    os.path.join(dirname(dirname(realpath(__file__))), "ankisyncd.conf"),
]


def load(path=None):
    choices = paths
    parser = configparser.ConfigParser()
    for path in choices:
        logger.debug("config.location: trying", path)
        try:
            parser.read(path)
            conf = parser['sync_app']
            logger.info("Loaded config from {}".format(path))
            # 命令行里的参数优先级最高，用于替换conf文件里的值
            load_from_env(conf)
            return conf
        except KeyError:
            pass
    raise Exception("No config found, looked for {}".format(", ".join(choices)))


# 只处理以ANKISYNCD_开头的命令行参数
def load_from_env(conf):
    logger.debug("Loading/overriding config values from ENV")
    for env in os.environ:
        if env.startswith('ANKISYNCD_'):
            config_key = env[10:].lower()
            conf[config_key] = os.getenv(config_key)
            logger.info("Setting {} from ENV".format(config_key))