import os
import json
import re
import time
from urllib import parse as urlparse
from androguard.core.bytecodes.apk import APK
from shutil import copyfile
from .utils import get_ignored_pkgs, read_xposed_log, mkdir
import xml.dom.minidom

OUTPUT_DIR_CONTENT = 'D:\\workplace\\adguard_output\\'


class AdGuard:

    def __init__(self, analyser, apk_name):

        self.analyser = analyser
        self.xposed_infos = []
        self.fiddler_infos = []
        self.states = {}
        self.traffic_dir = None

        for ip, pkgs in analyser.ip_pkgs.items():
            if apk_name in pkgs:
                self.traffic_dir = os.path.join(analyser.traffic_dir, ip, apk_name)
                break

        self.output_dir = os.path.join(analyser.output_dir, apk_name)

        apk = APK(os.path.join(analyser.app_dir, apk_name + '.apk'))
        self.pkg = apk.get_package()
        self.main_activity = apk.get_main_activity()

        self.ignored_pkgs = get_ignored_pkgs(self.pkg, self.main_activity)

        self.ad_clicks = []

        self.get_ad_content(get_file=True)
        self.get_ad_behavior()

    def get_ad_content(self, get_file=False):

        self.xposed_infos = read_xposed_log(os.path.join(self.output_dir, "xposed.log"))
        self.get_clicks()

        if self.ad_libs:

            self.read_fiddler()
            self.match_socket_proxy()

            self.get_ad_clicks()

            for ad_click in self.ad_clicks:
                self.get_ad_click_contents(ad_click)
                if get_file:
                    self.get_ad_files(ad_click)

    def get_clicks(self):

        clicked_path = os.path.join(self.output_dir, "clicked.json")

        clicks = []
        ad_libs = []
        if os.path.exists(clicked_path):
            with open(clicked_path, 'r+', encoding='utf-8') as f:
                content = f.read()
                json_list = content.split('}\n')
                for json_str in json_list:
                    if json_str:
                        json_str = json_str + '}'
                        click_dict = json.loads(json_str)
                        if click_dict['ad_feature']:
                            if click_dict['ad_feature'] not in ad_libs:
                                ad_libs.append(click_dict['ad_feature'])
                        clicks.append(click_dict)

        self.clicks = clicks
        self.ad_libs = ad_libs

    def read_fiddler(self):

        infos = []
        if self.traffic_dir:
            if os.path.exists(self.traffic_dir):
                sessions = os.listdir(self.traffic_dir)
                sessions = list(map(int, sessions))
                sessions.sort()
                for session_id in sessions:
                    info = self.read_fiddler_session(session_id)
                    if info and 'url' in info.keys():
                        infos.append(info)

        self.fiddler_infos = infos

    def read_fiddler_session(self, session_id):

        path = os.path.join(self.traffic_dir, str(session_id))

        info = {'sid': session_id, 'localPort': -1, 'ad_libs': set()}

        session = os.path.join(path, 'Session.txt')
        metadata = os.path.join(path, 'Metadata.txt')

        if os.path.exists(metadata):

            dom = xml.dom.minidom.parse(metadata)
            root = dom.documentElement
            elements_1 = root.getElementsByTagName('SessionFlag')
            for ele in elements_1:
                if ele.getAttribute('N') == "x-clientport":
                    info['localPort'] = ele.getAttribute("V")
                    break
            # elements_2 = root.getElementsByTagName('SessionTimers')
            # request_times = elements_2[0].getAttribute('ClientDoneRequest').split('.')[0].split('T')
            # timestamp = time.mktime(time.strptime(request_times[0] + ' ' + request_times[1], '%Y-%m-%d %H:%M:%S'))
            # info['timestamp'] = timestamp

        if os.path.exists(session):

            with open(session, "r+", encoding='utf-8') as f:

                content = f.read()
                splits = content.split('\n\n')
                requests = splits[0].strip('\n').split('\n')
                responses = splits[1].strip('\n').split('\n')

                url = requests[0].split(' ')[1]
                info['url'] = url
                for i in range(1, len(requests)):
                    key_value = requests[i].split(': ')
                    info[key_value[0]] = key_value[1]

                try:
                    code = responses[0].split(' ')[1]
                    info['code'] = code
                    if len(responses) > 1:
                        for i in range(1, len(responses)):
                            key_value = responses[i].split(': ')
                            info[key_value[0]] = key_value[1]
                    return info

                except:
                    return info

    def match_socket_proxy(self):

        if self.fiddler_infos and self.xposed_infos:
            for xposed_info in self.xposed_infos:
                ad_libs_within_stacks = set()
                if xposed_info['pkg'] == 'com.android.webview' or xposed_info['pkg'] == self.pkg:
                    for ad_lib in self.ad_libs:
                        for stack in xposed_info['stacks']:
                            if stack.startswith(ad_lib + '.'):
                                ad_libs_within_stacks.add(ad_lib)
                                break
                if ad_libs_within_stacks:
                    if xposed_info['localPort'] != -1 and xposed_info['port'] == '8888':
                        for fiddler_info in self.fiddler_infos:
                            if fiddler_info['localPort'] == xposed_info['localPort']:
                                # fiddler_info['stacks'] = xposed_info['stacks']
                                fiddler_info['ad_libs'] = fiddler_info['ad_libs'].union(ad_libs_within_stacks)

    def get_ad_clicks(self):

        clicks = self.clicks

        ad_clicks = []

        for i in range(0, len(clicks)):
            click = clicks[i]

            if click['ad_feature']:

                ad_load_urls = []
                ad_click_urls = []

                for fiddler_info in self.fiddler_infos:

                    try:
                        # traffic before ad click
                        if fiddler_info['sid'] <= click['sid']:
                            if click['ad_feature'] in fiddler_info['ad_libs']:
                                ad_load_urls.append(fiddler_info)
                        # traffic after the ad click, before the next two click
                        elif i != len(clicks) - 2:
                            if click['sid'] < fiddler_info['sid'] <= clicks[i + 2]['sid']:
                                ad_click_urls.append(fiddler_info)
                        elif  click['sid'] < fiddler_info['sid']:
                            ad_click_urls.append(fiddler_info)
                    except:
                        pass

                click['ad_load_urls'] = ad_load_urls
                click['ad_click_urls'] = ad_click_urls
                ad_clicks.append(click)

        self.ad_clicks = ad_clicks

    def get_ad_click_contents(self, ad_click):

        gplay_pkgs = set()
        webview_urls = []
        browser_urls = []
        webview_pages = []
        browser_pages = []

        for info in ad_click['ad_click_urls']:

            if "android.clients.google.com" in info['url']:
                app = ""
                if 'doc' in info['url']:
                    try:
                        app = info['url'].split('doc=')[1].split('&')[0]
                    except:
                        pass
                if 'id%3D' in info['url']:
                    app = info['url'].split('id%3D')[1].split('%')[0]
                if app and app != 'com.google.android.play.games' and app != self.pkg:
                    gplay_pkgs.add(app)

            if 'X-Requested-With' in info.keys():
                apk = info['X-Requested-With']

                if apk == self.pkg:
                    webview_urls.append(info)
                    if 'Content-Type' in info.keys():
                        if '/' in info['Content-Type']:
                            file_type = info['Content-Type'].split('/')[1].split(';')[0]
                            if file_type == 'html':
                                webview_pages.append(info['url'])

                elif apk == 'com.android.browser' or apk == 'org.lineageos.jelly':
                    browser_urls.append(info)
                    if 'Content-Type' in info.keys():
                        if '/' in info['Content-Type']:
                            file_type = info['Content-Type'].split('/')[1].split(';')[0]
                            if file_type == 'html':
                                browser_pages.append(info['url'])

        ad_click_contents = {'gplay_pkgs': list(gplay_pkgs),
                             # 'webview_urls': webview_urls,
                             # 'browser_urls': browser_urls,
                             'webview_pages': webview_pages,
                             'browser_pages': browser_pages}

        ad_click_contents_verbose = {'gplay_pkgs': list(gplay_pkgs),
                                     'webview_urls': webview_urls,
                                     'browser_urls': browser_urls,
                                     'webview_pages': webview_pages,
                                     'browser_pages': browser_pages}

        ad_click['ad_click_contents'] = ad_click_contents
        ad_click['ad_click_contents_verbose'] = ad_click_contents_verbose

    def get_ad_files(self, ad_click):
        ad_load_dir = mkdir(OUTPUT_DIR_CONTENT, 'ad_load')
        ad_click_dir = mkdir(OUTPUT_DIR_CONTENT, 'ad_click')
        ad_load_files = []
        ad_click_files = []

        # 如果ad_view不是由已知ad_lib加载的，则必须点击后有可能是广告的内容，如推广app或跳转网页
        if ad_click['ad_feature'] in self.analyser.known_ad_libs or ad_click['ad_click_contents']['gplay_pkgs'] or ad_click['ad_click_contents']['browser_pages']:

            for info in ad_click['ad_load_urls']:
                sid = info['sid']
                src = os.path.join(self.traffic_dir, str(sid), "ResponseBody.txt")
                if os.path.exists(src):
                    if os.path.getsize(src):
                        if 'Content-Type' not in info.keys():
                            file_type = "other"
                        else:
                            try:
                                file_type = info['Content-Type'].split('/')[1].split(';')[0]
                            except:
                                file_type = info['Content-Type']
                        if file_type:
                            # if file_type == 'html':
                            #     # TODO:: dump base64 images within html files
                            #     pass
                            if file_type in ['jpg', 'jpeg', 'gif', 'png', 'webp', 'html', 'zip', 'mp4']:
                                dst = os.path.join(ad_load_dir, file_type, self.pkg + '-' + str(sid) + '.' + file_type)
                                mkdir(ad_load_dir, file_type)
                                copyfile(src, dst)
                                ad_load_files.append(self.pkg + '-' + str(sid) + '.' + file_type)

            for info in ad_click['ad_click_contents_verbose']['browser_urls']:
                sid = info['sid']
                src = os.path.join(self.traffic_dir, str(sid), "ResponseBody.txt")
                if os.path.exists(src):
                    if os.path.getsize(src):
                        if 'Content-Type' not in info.keys():
                            file_type = "other"
                        else:
                            try:
                                file_type = info['Content-Type'].split('/')[1].split(';')[0]
                            except:
                                file_type = info['Content-Type']
                        if file_type:
                            if file_type in ['html']:
                                dst = os.path.join(ad_click_dir, file_type, self.pkg + '-' + str(sid) + '.' + file_type)
                                mkdir(ad_click_dir, file_type)
                                copyfile(src, dst)
                                ad_click_files.append(self.pkg + '-' + str(sid) + '.' + file_type)

            with open(os.path.join(os.path.dirname(OUTPUT_DIR_CONTENT), 'ad_clicks_info.txt'), 'a+') as f:
                result = {'pkg': self.pkg, 'ad_feature': ad_click['ad_feature'],
                          'sid': ad_click['sid'], 'state': ad_click['state'], 'view': ad_click['view'],
                          'ad_load_files': ad_load_files, 'ad_click_files': ad_click_files,
                          'ad_click_contents': ad_click['ad_click_contents']}
                f.write(json.dumps(result) + '\n')

    def get_ad_behavior(self):

        utg_path = os.path.join(self.output_dir, "utg.js")
        if os.path.exists(utg_path):
            self.utg = eval(open(utg_path).read()[11:])
        else:
            self.utg = None

        self.get_states()

    def get_states(self):

        state_dir = os.path.join(self.output_dir, "states")
        states = {}

        if os.path.exists(state_dir):
            for file in os.listdir(state_dir):
                if file.endswith(".json"):
                    with open(os.path.join(state_dir, file), "r") as f:
                        state_info = json.load(f)
                        if state_info['foreground_activity'].startswith(self.pkg):
                            states[state_info["state_str"]] = state_info

        self.states = states
