import os
from .adguard import AdGuard
from .utils import get_first_level_dirs, read_known_ad_libs


class Analyser:

    def __init__(self, app_dir, output_dir, traffic_dir, start_point=None, single_analysis=False):

        self.app_dir = app_dir
        self.output_dir = output_dir
        self.traffic_dir = traffic_dir
        self.known_ad_libs = read_known_ad_libs()

        self.ip_pkgs = {}
        self.get_ip_pkgs()

        should_start = False

        for apk_file in os.listdir(app_dir):
            if start_point:
                if apk_file == start_point + '.apk':
                    should_start = True
            else:
                should_start = True
            if should_start:
                if apk_file.endswith(".apk"):
                    print(apk_file[:-4])
                    AdGuard(self, apk_file[:-4])

                    if single_analysis:
                        break

    def get_ip_pkgs(self):

        traffic_dir = self.traffic_dir

        ip_pkgs = {}
        ips = get_first_level_dirs(traffic_dir)
        for ip in ips:
            ip_path = os.path.join(traffic_dir, ip)
            ip_pkgs[ip] = get_first_level_dirs(ip_path)

        self.ip_pkgs = ip_pkgs

