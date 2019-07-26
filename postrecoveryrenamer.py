#!/usr/bin/env python
# Purpose: for situations where recovery software leaves underscore
# as first letter of folder or file name, but Mac OS ._ file exists,
# making name recovery possible. Examples:
# * has _ello and ._hello, so rename _ello to hello
# * has _bye and .__bye, so no need to rename _bye since already correct
import os
import shutil
import sys

if len(sys.argv) < 2:
    print("You must specify a directory.")
    exit(1)

# region user settings
# repair_path = "M:\\"
repair_path = sys.argv[1]
# endregion user settings
mangled_fallback_char_string = "_"

def IsNotNull(value):
    return value is not None and len(value) > 0

def is_manged_of(good_needle, mangled_needle):
    result = False
    if good_needle is not None and len(good_needle) > 0 \
       and mangled_needle is not None and len(mangled_needle) > 0:
        matches = 0
        non_mangled = 0
        for i in range(0, len(good_needle)):
            if mangled_needle[i:i+1] == mangled_fallback_char_string:
                matches += 1
            elif mangled_needle[i:i+1] == good_needle[i:i+1]:
                matches += 1
                non_mangled += 1
        if non_mangled > 0 and matches == len(good_needle):
            result = True
    return result

def index_of_nonmangled(good_needles, mangled_needle):
    result = -1
    for i in range(0, len(good_needles)):
        if is_manged_of(good_needles[i], mangled_needle):
            result = i
            break
    return result


def _unmangle_recursively(folder_path, diagnostic_mode_enable=False):
    try:
        if os.path.isdir(folder_path):
            crumb_names = list()
            subs = os.listdir(folder_path)
            # do deepest FIRST to avoid cache of old name being used wrongly:
            for sub_name in subs:
                sub_path = os.path.join(folder_path, sub_name)
                if sub_name[:1] != "." and os.path.isdir(sub_path):
                    _unmangle_recursively(sub_path, diagnostic_mode_enable=diagnostic_mode_enable)
            # print("#found " + str(len(subs)) + " directories in \"" + folder_path + "\"")
            for sub_name in subs:
                sub_path = os.path.join(folder_path, sub_name)
                if sub_name[:2] == "._" and os.path.isfile(sub_path) and len(sub_name) > 2:
                    crumb_names.append(sub_name[2:])
            for sub_name in subs:
                sub_path = os.path.join(folder_path, sub_name)
                if sub_name[:1] != ".":
                    if sub_name[:1] == "_":
                        good_index = index_of_nonmangled(crumb_names, sub_name)
                        if good_index >= 0:
                            good_name = crumb_names[good_index]
                            if good_name != sub_name:
                                repaired_path = os.path.join(folder_path, good_name)
                                if not os.path.exists(repaired_path):
                                    if not diagnostic_mode_enable:
                                        try:
                                            shutil.move(sub_path, repaired_path)
                                            cmd_string = "mv \"" + sub_path + "\" \"" + repaired_path + "\""
                                        except:
                                            cmd_string = "#could_not_finish_mv \"" + sub_path + "\" \"" + repaired_path + "\""
                                        print(cmd_string)
                                else:
                                    # if diagnostic_mode_enable:
                                    print("#mv_not_overwriting \"" + sub_path + "\" \"" + repaired_path + "\"")
        else:
            print("#not_a_directory:\""+folder_path+"\"")
    except:
        print("#skipped_inaccessible:\"" + folder_path + "\"")
        if "system volume information" in folder_path.lower():
            print("#NOTE: System Volume Information only includes Windows metadata, no actual user files")

def unmangle(folder_path, diagnostic_mode_enable=False):
    print("#Starting postrecoveryrenamer.py...")
    print("#diagnostic_mode_enable: " + ("True" if diagnostic_mode_enable else "False") )
    if diagnostic_mode_enable:
        print("#(no changes will be made)")
    print("#(attempts to unmangle file and folder names)")
    print("#repair_path: \"" + repair_path + "\")")
    _unmangle_recursively(folder_path, diagnostic_mode_enable=diagnostic_mode_enable)
    print("#Finished attempting recursive unmangle operation.")

unmangle(repair_path, diagnostic_mode_enable=False)
