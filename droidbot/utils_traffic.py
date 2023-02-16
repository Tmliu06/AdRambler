import os
import re
import subprocess


def init_fiddler(traffic_dir, device_ip):
    script_template_path = os.path.dirname(os.path.abspath(__file__)) + '/resources/CustomRules.js'
    script_path_on_windows = '~/Documents/Fiddler2/Scripts/CustomRules.js'

    if not os.path.exists(traffic_dir):
        os.mkdir(traffic_dir)
    if not os.path.exists(os.path.join(traffic_dir, device_ip)):
        os.mkdir(os.path.join(traffic_dir, device_ip))

    # set up and start fiddler
    if not os.path.exists(os.path.expanduser(script_path_on_windows)):
        print('cannot find FiddlerScript, please install fiddler properly on a windows system')
        return False

    with open(script_template_path, "r+", encoding='utf-8') as fiddler_script:
        js = fiddler_script.read()
    traffic_dir_old = re.findall(r'trafficdir = (.+?)";', js)[0]
    if not '"' + traffic_dir == traffic_dir_old:
        js = js.replace('trafficdir = '+traffic_dir_old, 'trafficdir = "'+traffic_dir)
    with open(os.path.expanduser(script_path_on_windows), "w+", encoding='utf-8') as fiddler_script:
        fiddler_script.write(js)

    # run fiddler, please add the path of Fidder to System PATH variable
    subprocess.Popen('fiddler /quiet /noattach /noversioncheck')


def init_ip_pkg(traffic_dir, device_ip, apk_name, device_serial):
    # renew mappings between device_ip and the app being tested
    # this mapping is to support multiple testing devices
    with open(os.path.join(traffic_dir, 'ip_pkg.txt'), "a+", encoding='utf-8') as f:
        pass
    with open(os.path.join(traffic_dir, 'ip_pkg.txt'), "r+", encoding='utf-8') as f:
        lines = f.readlines()
    with open(os.path.join(traffic_dir, 'ip_pkg.txt'), "w+", encoding='utf-8') as f:
        for line in lines:
            if device_ip not in line:
                f.write(line.strip('\n') + '\n')
        f.write(device_ip + ":" + apk_name + '\n')

    with open(os.path.join(traffic_dir, 'device_ip_pkg.txt'), "a+", encoding='utf-8') as f:
        f.write(device_serial + "\t" + device_ip + "\t" + apk_name + '\n')


def quit_fiddler():
    # a method to quit Fiddler
    os.system('execAction quit')
