import os
import logging
from droidbot.droidbot import DroidBot
from droidbot.utils import init_breakpoint
from droidbot.utils_traffic import init_fiddler, init_ip_pkg

# specify True to capture traffic with Fiddler (Windows only)
ad_traffic = True

app_dir = "D:/workplace/in/"
output_dir = "D:/workplace/out/"
traffic_dir = "D:/workplace/traffic/"  # dir to store captured traffic file. must specify full dir

# get from command 'adb devices'
device_serial = '037450b9094061ea'


def main():
    """
    the main function
    it starts a droidbot according to the parameters given
    """
    apk_files = os.listdir(app_dir)
    for apk_file in apk_files:
        if apk_file[-4:].lower() == '.apk':
            breakpoint_path, apk_done = init_breakpoint(app_dir)
            apk_name = apk_file[:-4]
            if apk_name + '\n' not in apk_done:

                with open(breakpoint_path, "a+", encoding='utf-8') as f:
                    f.write(apk_name+'\n')

                if ad_traffic:
                    init_ip_pkg(traffic_dir, device_ip, apk_name, device_serial)
                    traffic_dir_for_app = os.path.join(traffic_dir, device_ip, apk_name)
                else:
                    traffic_dir_for_app = None
                try:
                    print(apk_name)
                    droidbot = DroidBot(
                                        app_path=os.path.join(app_dir, apk_file),
                                        device_serial=device_serial,
                                        is_emulator=False,
                                        output_dir=os.path.join(output_dir, apk_name),
                                        env_policy=None,
                                        policy_name="dfs_ad",
                                        random_input=False,
                                        script_path=None,
                                        event_count=12,
                                        event_interval=10,
                                        timeout=750,
                                        keep_app=False,
                                        keep_env=True,
                                        cv_mode=False,
                                        debug_mode=False,
                                        profiling_method=None,
                                        grant_perm=True,
                                        traffic_dir=traffic_dir_for_app)
                    droidbot.start()
                except:
                    if 'droidbot' in locals().keys():
                        droidbot.stop()
                    print(apk_name + " can not use.")
                    import traceback
                    traceback.print_exc()
    return


if __name__ == "__main__":

    # adb over network
    if ':' in device_serial:
        os.system("adb connect " + device_serial)

    # gain adb root privilege
    # os.system('adb -s ' + device_serial + " root")

    if ad_traffic:
        # get device ip through adb
        wlan0_content = os.popen('adb -s ' + device_serial + ' shell ifconfig wlan0').read()
        # device_ip = wlan0_content.split(' ')[2]   # for 4.4
        device_ip = wlan0_content.split('inet addr:')[1].split(' ')[0]  #for 6.0

        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger('AdTraffic')
        init_fiddler(traffic_dir, device_ip)
        logger.info("Starting Fiddler")

    main()
