1. 登录接口：http://ip:port/sync/hostKey POST --- [sync_hostKey](./api/sync_hostKey.txt)
2. 元数据请求接口：http://ip:port/sync/meta POST --- [meta](api/meta.txt)
3. sqlite下载接口：http://ip:port/sync/download POST --- 全量时才会下载
4. 部分数据更新时：
    1. http://49.235.186.84:27701/sync/start POST --- [sync_start](api/sync_start.txt)
    2. http://49.235.186.84:27701/sync/applyChanges --- [sync_applyChanges](./api/sync_applyChanges.txt)
    3. http://49.235.186.84:27701/sync/chunk --- [sync_chunk](./api/sync_chunk.txt)
    4. http://49.235.186.84:27701/sync/applyChunk --- [sync_applyChunk](./api/sync_applyChunk.txt)
    5. http://49.235.186.84:27701/sync/sanityCheck2 ---- [sync_sanityCheck2](./api/sync_sanityCheck2.txt)
    6. http://49.235.186.84:27701/sync/finish --- [sync_finish](./api/sync_finish.txt)
5. 媒体数据同步接口：http://49.235.186.84:27701/msync/begin POST --- [msync_begin](./api/msync_begin.txt)