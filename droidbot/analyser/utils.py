import os
from urllib import parse as urlparse


def read_xposed_log(xposed_log_path):

    infos = []

    if os.path.exists(xposed_log_path):

        with open(xposed_log_path, "r+", encoding='utf-8') as f:
            lines = f.readlines()

            signals = []
            for i, line in enumerate(lines):
                if line == "#\n":
                    signals.append(i)

            for i in range(0, len(signals) - 1):

                if signals[i + 1] - signals[i] > 1:
                    blocks = lines[signals[i] + 1: signals[i + 1]]
                    info = parse_xposed_block(blocks)
                    if info:
                        infos.append(info)

    return infos


def parse_xposed_block(blocks):

    pkg = ''
    url = ''
    stacks = []
    method = ''
    host = ''
    port = ''
    localPort = -1

    for block in blocks:
        block = block[1:-1]
        if block.startswith('Pkg='):
            pkg = block.replace('Pkg=', '')
        elif block.startswith('Url='):
            url = block.replace('Url=', '')
            if '/' not in url and not url.startswith('Socket['):
                url = ''
        elif block.startswith("Method="):
            method = block.replace("Method=", '')
        elif block.startswith("Stack="):
            stacks.append(block.replace("Stack=", ''))

    if url:
        if url.startswith('Socket'):
            try:
                splits = url.split('[')[1].split(']')[0].split(',')
                if len(splits) == 3:
                    host = splits[0][8:]
                    if host.startswith('/'):
                        host = host[1:]
                    else:
                        host = host.split('/')[0]
                    port = splits[1][5:]
                    localPort = splits[2][10:]
                else:
                    return None
            except:
                pass
        else:
            host = urlparse.urlparse(url).netloc

    info = {'pkg': pkg, "url": url, "stacks": stacks, "method": method, "host": host, "port": port, 'localPort': localPort}

    return info


def get_pkg_layer(pkg_splits, layer=2):
    """
    extract first n layers of the input package
    """
    if len(pkg_splits) <= layer:
        pkg = '.'.join(pkg_splits)
    else:
        pkg = '.'.join(pkg_splits[:layer])
    return pkg


def get_first_level_dirs(path):
    # return first_level dirs from a path
    dirs = []
    if os.path.isdir(path):
        files = os.listdir(path)
        for file in files:
            dir_path = os.path.join(path, file)
            if os.path.isdir(dir_path):
                dirs.append(file)
    return dirs


def get_ignored_pkgs(package_name, main_activity):

    ignored_pkgs = ['java.', 'com.android.', 'de.robv.android.', 'android.', 'dalvik.',
                    'com.google', 'androidx.', 'com.unity3d.player']

    pkg_0 = get_pkg_layer(package_name.split('.'))
    pkg_1 = get_pkg_layer(main_activity.split('.')[:-1])

    ignored_pkgs.append(pkg_0)

    if pkg_1 not in pkg_0 and not pkg_1.startswith('com.unity3d'):
        ignored_pkgs.append(pkg_1)

    return ignored_pkgs


def mkdir(src, dst):
    path = os.path.join(src, dst)
    if not os.path.exists(path):
        os.mkdir(path)
    return path


def read_known_ad_libs():
    import pkg_resources
    ad_lib_path = pkg_resources.resource_filename("droidbot", "resources/Ad_Libraries.csv")

    known_ad_libs = []

    if os.path.exists(ad_lib_path):
        with open(ad_lib_path, 'r+') as f:
            lines = f.readlines()
            for line in lines[1:]:
                known_ad_libs.append(line.split(',')[0])

    return list(set(known_ad_libs))
