import logging
from wsgiref.simple_server import make_server, WSGIRequestHandler, demo_app
import ankisyncd
import ankisyncd.config
from ankisyncd.sync_app import SyncApp


def main():
    # 配置日志的输出格式
    logging.basicConfig(level=logging.INFO, format="[%(asctime)s]:%(levelname)s:%(name)s:%(message)s")
    import ankisyncd.config

    class RequestHandler(WSGIRequestHandler):
        logger = logging.getLogger("ankisyncd.http")

        def log_error(self, format, *args):
            self.logger.error("%s %s", self.address_string(), format % args)

        def log_message(self, format, *args):
            self.logger.info("%s %s", self.address_string(), format % args)

    config = ankisyncd.config.load()
    ankiserver = SyncApp(config)
    httpd = make_server(config['host'], int(config['port']), ankiserver, handler_class=RequestHandler)

    try:
        logging.info("Serving HTTP on http://{}:{} ...".format(*httpd.server_address))
        httpd.serve_forever()
    except KeyboardInterrupt:
        logging.info("Exiting...")


if __name__ == '__main__':
    main()
