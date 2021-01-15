from webob.dec import wsgify
from webob import Response
from webob.exc import HTTPForbidden, HTTPNotFound, HTTPInternalServerError
from ankisyncd.users import get_user_manager
from ankisyncd.sessions import get_session_manager
import os
import gzip
import io
import json
import time
import random
import anki.utils


class SyncApp:
    # 支持的所有的
    valid_urls = ['hostKey', 'upload', 'download'] + ["meta"] # + SyncCollectionHandler.operations + SyncMediaHandler.operations

    def __init__(self, config):

        self.data_root = os.path.abspath(config['data_root'])
        self.base_url  = config['base_url']
        self.base_media_url = config['base_media_url']

        self.user_manager = get_user_manager(config)
        self.session_manager = get_session_manager(config)
        self.collection_manager = None  # get_collection_manager(config)
        self.setup_new_collection = None

    def create_session(self, username, user_path):
        return SyncUserSession(username, user_path, self.collection_manager, self.setup_new_collection)

    @wsgify
    def __call__(self, req):
        try:
            hkey = req.POST['k']
        except KeyError:
            hkey = None

        session = self.session_manager.load(hkey, self.create_session)

        # if session is None:
        #     try:
        #         skey = req.POST['sk']
        #         session = self.session_manager.load_from_skey(skey, self.create_session)
        #     except KeyError:
        #         skey = None

        # gzip解压请求json数据
        try:
            compression = int(req.POST['c'])
        except KeyError:
            compression = 0
        try:
            data = req.POST['data'].file.read()
            data = self._decode_data(data, compression)
        except KeyError:
            data = {}

        if req.path.startswith(self.base_url):
            url = req.path[len(self.base_url):]
            if url not in self.valid_urls:
                raise HTTPNotFound()

            # 登录接口，生成新的session，存入session.db中，返回hkey值
            if url == 'hostKey':
                result = self.operation_hostKey(data.get("u"), data.get("p"))
                print(result)
                if result is None:
                    raise HTTPForbidden('null')

                return json.dumps(result)

            if session is None:
                raise HTTPForbidden()

            # 同步请求
            if url in SyncCollectionHandler.operations + SyncMediaHandler.operations:
                if url == 'meta':
                    if session.skey == None and 's' in req.POST:
                        session.skey = req.POST['s']
                    if 'v' in data:
                        session.version = data['v']
                    if 'cv' in data:
                        session.client_version = data['cv']

                        self.session_manager.save(hkey, session)
                        session = self.session_manager.load(hkey, self.create_session)

                # thread = session.get_thread()

                # if url in self.prehooks:
                #     thread.execute(self.prehooks[url], [session])

                result = self._execute_handler_method_in_thread(url, data, session)

                # If it's a complex data type, we convert it to JSON
                # if type(result) not in (str, bytes, Response):
                #     result = json.dumps(result)

                # if url in self.posthooks:
                #     thread.execute(self.posthooks[url], [session])

                return result

            elif url == 'upload':  # 客户端整体上传
                pass
            elif url == 'download':  # 首次整体下载
                pass

            # This was one of our operations but it didn't get handled... Oops!
            raise HTTPInternalServerError()

        # media sync
        elif req.path.startswith(self.base_media_url):
            pass

        return "Anki Sync Server"

    def operation_hostKey(self, username, password):
        if not self.user_manager.authenticate(username, password):
            return

        dirname = self.user_manager.userdir(username)
        if dirname is None:
            return

        hkey = self.generateHostKey(username)
        user_path = os.path.join(self.data_root, dirname)
        session = self.create_session(username, user_path)
        self.session_manager.save(hkey, session)

        return {'key': hkey}

    def generateHostKey(self, username):
        """Generates a new host key to be used by the given username to identify their session.
        This values is random."""

        import hashlib, time, random, string
        chars = string.ascii_letters + string.digits
        val = ':'.join([username, str(int(time.time())), ''.join(random.choice(chars) for x in range(8))]).encode()
        return hashlib.md5(val).hexdigest()

    def _decode_data(self, data, compression=0):
        if compression:
            with gzip.GzipFile(mode="rb", fileobj=io.BytesIO(data)) as gz:
                data = gz.read()

        try:
            data = json.loads(data.decode())
        except (ValueError, UnicodeDecodeError):
            data = {'data': data}

        return data


class SyncUserSession:
    def __init__(self, name, path, collection_manager, setup_new_collection=None):
        self.skey = self._generate_session_key()
        self.name = name
        self.path = path
        self.collection_manager = collection_manager
        self.setup_new_collection = setup_new_collection
        self.version = None
        self.client_version = None
        self.created = time.time()
        self.collection_handler = None
        self.media_handler = None

        # make sure the user path exists
        if not os.path.exists(path):
            os.mkdir(path)

    def _generate_session_key(self):
        return anki.utils.checksum(str(random.random()))[:8]

class SyncCollectionHandler:
    operations = ['meta']

class SyncMediaHandler:
    operations = []