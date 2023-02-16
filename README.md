# AdBot

## About

AdBot is a dynamic exploration tool for automated testing of in-app advertisement in Android apps based on [DroidBot](https://github.com/honeynet/droidbot/).  

## Requirements

1. Python 3.7, Java 8, Android SDK
2. Add `platform_tools` directory in Android SDK to `PATH`
3. Install prerequisites with:

```shell
pip install androguard>=3.4.0a1 networkx Pillow
```

## How to use

1. Make sure a testing Android device or emulator installed with Xposed is connected via `adb`.
2. Change the parameters accordingly in `loader_single.py`（`loader.py` for batch run）.
3. Run `loader_single.py` or `loader.py`. (Users can customize the number and interval time of input events in the loader.)

# Capturing Traffic with AdTraffic

AdTraffic is designed to harvest all the ad-related traffic at runtime and further collect ad contents, which runs in parallel with AdBot.  

## Requirements

Supported OS: Windows XP or higher  

AdTraffic utilizes [Fiddler](https://www.telerik.com/fiddler) and [FidderScript](https://www.telerik.com/blogs/understanding-fiddlerscript) to capture and organize general traffic, which currently support Windows OS only.  


## How to use

1. Make sure a testing Android device or emulator installed with Xposed is connected via `adb`.  
2. Setting up Fiddler to capture the traffic of your testing device (including HTTPS messages) according to [this article](https://docs.telerik.com/fiddler/Configure-Fiddler/Tasks/ConfigureForAndroid).  
3. Specify `ad_traffic = True` in `loader_single.py` or `loader.py`.
4. Run `loader_single.py` or `loader.py`.

## Acknowledgement

[DroidBot](https://github.com/honeynet/droidbot/)  
[Fiddler](https://www.telerik.com/fiddler)  
