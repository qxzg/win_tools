import json
import os
import shutil
from time import time
from zipfile import ZipFile

from requests import request
from win10toast import ToastNotifier

toaster = ToastNotifier()
url = "https://api.github.com/repos/GyanD/codexffmpeg/releases"
local_dir = 'C:\\Program Files\\ffmpeg'
if not os.path.isdir(local_dir):
    os.makedirs(local_dir)
version_file = os.path.join(local_dir, "version.txt")
temp_filename = "temp-" + str(int(time()))
tempdir = os.path.join(local_dir, temp_filename)

try:
    releases = json.loads(request("GET", url, headers={"Accept": "application/vnd.github.v3+json"}).text)
    if "message" in releases:
        raise Exception(str(releases))
except BaseException as err:
    toaster.show_toast("ffmpeg检查更新失败", str(err), duration=30)
    exit()


def get_latest_build():
    max_id = [-1, 0]
    i = 0
    for release in releases:
        if release['tag_name'].find("git") == -1 or release['tag_name'].find('tools') != -1:
            i += 1
            continue
        if release['id'] > max_id[0]:
            max_id[0] = release['id']
            max_id[1] = i
        i += 1
    for assets in releases[max_id[1]]['assets']:
        if assets['name'].find('full_build.zip') != -1:
            asset_url = assets['url']
            asset_name = assets['name']
    return [releases[max_id[1]]['tag_name'], asset_url, asset_name]


def get_asset(asset_url):
    try:
        response = request("GET", asset_url, headers={"accept": "application/octet-stream"}, stream=True)
        with open(os.path.join(tempdir, latest_build[2]), "wb") as fobj:
            for chunk in response.iter_content(chunk_size=10240):
                if chunk:
                    fobj.write(chunk)
        response.close()
    except BaseException as err:
        shutil.rmtree(tempdir)
        toaster.show_toast("ffmpeg下载更新失败", str(err), duration=30)


try:
    with open(version_file, "r", encoding="utf-8") as fobj:
        local_version = fobj.read()[:10].split('-')
        local_version = int(local_version[0]) * 10000 + int(local_version[1]) * 100 + int(local_version[2])
except:
    local_version = 0

latest_build = get_latest_build()
remote_version = latest_build[0][:10].split('-')
remote_version = int(remote_version[0]) * 10000 + int(remote_version[1]) * 100 + int(remote_version[2])
if local_version != remote_version:
    try:
        os.mkdir(tempdir)
        get_asset(latest_build[1])
        archive = ZipFile(os.path.join(tempdir, latest_build[2]), "r")
        archive.extractall(path=tempdir)
        archive.close()
        if os.path.isdir(os.path.join(local_dir, "bin")):
            shutil.rmtree(os.path.join(local_dir, "bin"))
        shutil.move(os.path.join(tempdir, latest_build[2][:-4], "bin"), local_dir)
        with open(version_file, "w", encoding="utf-8") as fobj:
            fobj.write(latest_build[0])
    except BaseException as err:
        toaster.show_toast("ffmpeg更新失败", str(err), threaded=30)
        print(err)
    else:
        toaster.show_toast("ffmpeg更新成功", "ffmpeg已更新至" + latest_build[0], threaded=30)
    shutil.rmtree(tempdir)
