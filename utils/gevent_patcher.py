from os import environ
from time import sleep as sync_sleep


patching_result = False
sleep = sync_sleep

if not environ.get("DEBUG"):
    from gevent import monkey
    from gevent.time import sleep as async_sleep
    patching_result = monkey.patch_all()
    sleep = async_sleep
