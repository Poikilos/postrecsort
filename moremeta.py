#!/usr/bin/env python
# formerly internaldates.py
from __future__ import print_function
#
# TODO: Rewrite modified date filesystem metadata according to EXIF date

# import EXIF  # requires https://github.com/ianare/exif-py
import os
import shutil
import PIL.Image
import PIL.ExifTags
from datetime import datetime


# NOTE: case matters in html entities:
bad_hex_to_html = {
    'a7': "&sect;",
    'ae': "&reg;",
    'f1': "&ntilde;",
    'a9': "&copy;",
    'cb': "&Euml;",
    'b0': "&deg;",
    'fc': "&uuml;",
    'b7': "&#183;",
    'e8': "&egrave;",
    'e9': "&eacute;",
    'c7': "&Ccedil;",
    'e3': "&atilde;",
    'e5': "&aring;",
    'e7': "&ccedil;",
    'ea': "&ecirc;",
    'c4': "&Auml;",
    'e1': "&aacute;",
    'f4': "&ocirc;"
}
hex_description = {
    'a7': "section sign (double-s)",
    'f1': "Spanish ene (actually en^~e) character aka &#xF1;",
    'b7': "middle dot (small bullet, or dot product operator)",
    'e8': "e with mark down diagonally",
    'e9': "e with accent",
    'e5': "a with ring",
    'ea': "e with caret (pointing up)",
    'f4': "o with caret (pointing up)",
}

def is_jpeg(path):
    path_lower = path.lower()
    ret = False
    if path_lower[-4:] == ".jpg":
        ret = True
    elif path_lower[-4:] == ".jpe":
        ret = True
    elif path_lower[-5:] == ".jpeg":
        ret = True
    return ret

def is_html(path):
    path_lower = path.lower()
    ret = False
    if path_lower[-4:] == ".htm":
        ret = True
    elif path_lower[-5:] == ".html":
        ret = True
    if path_lower[-8:] == ".htm.bak":
        ret = True
    elif path_lower[-9:] == ".html.bak":
        ret = True
    return ret

html_date_patterns = []
html_date_patterns.append({
    "brand:": "GeoCities",
    "opener": "<!-- w17.geo.scd.yahoo.com compressed/chunked ",
    "closer": "-->",
    "format": "%a %b %m %H:%M:%S %Z %Y"  # Thu Sep 18 10:59:24 PDT 2003
})
# NOTE: $m is zero-padded, and GeoCities timestamp may not be
# the date info above is only available on pages downloaded from Yahoo
html_date_patterns.append({
    "brand:": "webbot",
    "opener": 's-format="%m/%d/%y" -->',
    "closer": "<!--",
    "format": "%m/%d/%y"  # 10/17/02
})

def parse_date(dt_s, fmt):
    return datetime.strptime(dt_s, fmt)

def extract_exif_date(path):
    img = PIL.Image.open(path)
    exif_data = img._getexif()
    if exif_data is None:
        # print(",,NO EXIF DATA")
        return None
    # convert numeric tags to dict:
    # (see <https://stackoverflow.com/questions/4764932/in-python-how-do-i-read-the-exif-data-for-an-image>)
    exif = {
        PIL.ExifTags.TAGS[k]: v
        for k, v in exif_data.items()
        if k in PIL.ExifTags.TAGS
    }
    # print()
    # print(path + ":")
    # print(str(exif))
    # EXIF "taken" date:
    t_date = None
    # YES, exif has ':' for date separator:
    fmt = "%Y:%m:%d %H:%M:%S"
    t_date_s = exif.get("DateTimeDigitized")
    if t_date_s is None:
        t_date_s = exif.get("OriginalDateTime")
    if t_date_s is None:
        t_date_s = exif.get("DateTime")
    if t_date_s is not None:
        t_date = datetime.strptime(t_date_s, fmt)
        # if t_date is None:
            # print(",,ERROR: could not read '" + fmt + "' format date"
                  # " from '" + t_date_s)
        # else:
            # print(",,GOT DATE " + t_date.strftime(fmt))
    else:
        print(',' + path + ','
              + '"ERROR: No DateTimeDigitized nor OriginalDateTime in '
              + str(exif) + '"')
    return t_date

enc_pattern = {
    'opener': "decode byte ",
    'closer': " ",
    'description': "hex"
}


def extract_html_date(path):
    ins = open(path, encoding='utf-8')
    # utf-8 supposedly allows non-ascii <https://stackoverflow.com/\
    # questions/35028683/\
    # python3-unicodedecodeerror-with-readlines-method>, but still fails
    # on characters in bad_hex_to_html dict above
    # NOTE: , errors="ignore" will throw away out-of-range bytes
    pattern = None
    collect = ""
    result = None
    start_line = None
    closed = False
    line_number = 0
    while True:
        line_number += 1
        line = False
        # line = ins.readline()
        try:
            line = ins.readline()
        except UnicodeDecodeError as e:
            msg = ("," + path + ",(line " + str(line_number) + "): "
                  + "ERROR: bad character")
            e_s = str(e)

            opener = enc_pattern['opener']
            closer = enc_pattern['closer']
            o_i = e_s.find(opener)
            byte_found = False
            if o_i >= 0:
                start_i = o_i + len(opener)
                c_i = e_s.find(closer, start_i)
                if c_i >=0:
                    byte_found = True
                    hex_s = e_s[start_i:c_i]
                    if hex_s[:2] == "0x":
                        hex_s = hex_s[2:]
                    hex_s = hex_s.lower()
                    html_s = bad_hex_to_html.get(hex_s)
                    if html_s is None:
                        html_s = "&#x" + hex_s.upper() + ";"
                    msg += ("--Symbol '0x" + hex_s + "' is not allowed"
                           + " in HTML--change it to " + html_s)
                    print(msg + "  " + e_s)
            if not byte_found:
                msg += ("--WARNING: Unable to read hex from error:")
                msg += (" " + e_s)
                print(msg)

            # False: print("  " + str(line))
            # break
            continue
        if line:
            line = line.strip()
            # if line_number == 1:
                # print("line 1 is: " + line)
            if pattern is not None:
                closer_i = line.find(pattern['closer'])
                if closer_i >= 0:
                    collect += line[:closer_i]
                    result = collect
                    break
            else:
                for pattern_i in range(len(html_date_patterns)):
                    try_pattern = html_date_patterns[pattern_i]
                    opener_i = line.find(try_pattern['opener'])
                    if opener_i >= 0:
                        pattern = try_pattern
                        start_i = opener_i + len(pattern['opener'])
                        closer_i = line.find(pattern['closer'], start_i)
                        if closer_i >= 0:
                            result = line[start_i:closer_i]
                            closed = True
                        else:
                            collect = line[start_i:]
                        break
            if closed:
                break
        else:
            break
    if (len(collect) > 0) and (result is None):
        print("ERROR: found " + pattern['opener'] + "' without '"
              + pattern['closer'])
    ins.close()
    dt = None
    if result is not None:
        dt = parse_date(result, pattern['format'])
    return dt

def process_files(folder_path, op, more_results=None):
    unknown_type = None
    unknown_type_count = None
    missing_meta_count = None
    missing_meta = None
    processed_count = None
    # checked_count = None

    results = {}

    if more_results is not None:
        results = more_results
    unknown_type = results.get('unknown_type', [])
    unknown_type_count = results.get('unknown_type_count', 0)
    missing_meta = results.get('missing_meta', [])
    missing_meta_count = results.get('missing_meta_count', 0)
    processed_count = results.get('processed_count', 0)
    # checked_count = results.get('checked_count', 0)

    if os.path.isdir(folder_path):
        for sub_name in os.listdir(folder_path):
            sub_path = os.path.join(folder_path, sub_name)
            if sub_name[:1] == ".":
                continue
            if os.path.isdir(sub_path):
                process_files(sub_path, op, more_results=results)
            elif os.path.isfile(sub_path):
                t_date = None
                type_mark = None
                if is_jpeg(sub_path):

                    t_date = extract_exif_date(sub_path)
                    # if processed_count == 0:
                        # outs = open("example.exif.dict.txt", 'w')
                        # outs.write(str(exif))
                        # outs.close()
                    type_mark = "JPEG"
                elif is_html(sub_path):
                    t_date = extract_html_date(sub_path)
                    type_mark = "HTML"
                else:
                    unknown_type_count += 1
                    unknown_type.append(sub_path)
                    continue

                if t_date is not None:
                    taken_s = t_date.strftime("%Y-%m-%d")
                    # print(taken_s)
                    if op == 'move':
                        target_dir_path = os.path.join(folder_path, taken_s)
                        if not os.path.isdir(target_dir_path):
                            os.makedirs(target_dir_path)
                        new_path = os.path.join(target_dir_path, sub_name)
                        shutil.move(sub_path, new_path)
                    elif op == 'show':
                        print(taken_s + "," + sub_path)
                        # print("  - IS " + type_mark)
                    processed_count += 1
                else:
                    missing_meta_count += 1
                    missing_meta.append(sub_path)
    else:
        print(",,ERROR: '" + folder_path + "' is not a directory.")
    results['unknown_type_count'] = unknown_type_count
    results['unknown_type'] = unknown_type
    results['missing_meta'] = missing_meta
    results['missing_meta_count'] = missing_meta_count
    results['processed_count'] = processed_count
    return results

if __name__ == "__main__":
    # results = process_files("/home/owner/ownCloud/www/NeoArmor-older", 'show')
    results = process_files("/home/owner/ownCloud/www/expertmultimedia/besidethevoid", 'show')
    print("")
    print("unknown_type_count: " + str(results.get('unknown_type_count')))
    for path in results.get('unknown_type'):
        print("  - " + path)
    print("missing_meta_count: " + str(results.get('missing_meta_count')))
    missing_meta_non_html_only_count = 0
    print("missing_meta_non_html_only:")
    for path in results.get('missing_meta'):
        if not is_html(path):
            print("  - " + path)
            missing_meta_non_html_only_count += 1
    print("missing_meta_non_html_only_count:"
          + str(missing_meta_non_html_only_count))
    print("processed_count: " + str(results.get('processed_count')))

    # not tried yet:
        # with open('image.jpg', 'rb') as fh:
            # tags = EXIF.process_file(fh, stop_tag="EXIF DateTimeOriginal")
            # dateTaken = tags["EXIF DateTimeOriginal"]
            # return dateTaken
