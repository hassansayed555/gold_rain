[app]
title = GOLD RAIN
package.name = goldrain
package.domain = com.hassansayed
source.dir = .
source.include_exts = py,txt,png,jpg
version = 1.0
requirements = python3,pygame-ce
orientation = portrait
fullscreen = 1

# Custom Pygame CE recipe used by this project
p4a.local_recipes = p4a-recipes

android.api = 34
android.minapi = 23
android.ndk_api = 23
android.arch = arm64-v8a
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
