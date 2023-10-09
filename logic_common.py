import ntpath
import re
import sys
from typing import Optional

# third-party
import requests

apikey = "1e7952d0917d6aab1f0293a063697610"
ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36 Edg/93.0.961.38"

os_mode = None  # Can be 'windows', 'mac', 'linux' or None. None will auto-detect os.
# Replacement order is important, don't use dicts to store
platform_replaces = {
    "windows": [
        ['[:*?"<>| ]+', " "],  # Turn illegal characters into a space
        [r"[\.\s]+([/\\]|$)", r"\1"],  # Dots cannot end file or directory names
    ],
    "mac": [["[: ]+", " "]],  # Only colon is illegal here
    "linux": [],  # No illegal chars
}


def pathscrub(dirty_path: str, os: Optional[str] = None, filename: bool = False) -> str:
    """
    Strips illegal characters for a given os from a path.
    :param dirty_path: Path to be scrubbed.
    :param os: Defines which os mode should be used, can be 'windows', 'mac', 'linux', or None to auto-detect
    :param filename: If this is True, path separators will be replaced with '-'
    :return: A valid path.
    """

    # See if global os_mode has been defined by pathscrub plugin
    if os_mode and not os:
        os = os_mode

    if not os:
        # If os is not defined, try to detect appropriate
        drive, path = ntpath.splitdrive(dirty_path)
        if sys.platform.startswith("win") or drive:
            os = "windows"
        elif sys.platform.startswith("darwin"):
            os = "mac"
        else:
            os = "linux"
    replaces = platform_replaces[os]

    # Make sure not to mess with windows drive specifications
    drive, path = ntpath.splitdrive(dirty_path)

    if filename:
        path = path.replace("/", " ").replace("\\", " ")
    for search, replace in replaces:
        path = re.sub(search, replace, path)
    # Remove spaces surrounding path components
    path = "/".join(comp.strip() for comp in path.split("/"))
    if os == "windows":
        path = "\\".join(comp.strip() for comp in path.split("\\"))
    path = path.strip()
    # If we stripped everything from a filename, complain
    if filename and dirty_path and not path:
        raise ValueError(f"Nothing was left after stripping invalid characters from path `{dirty_path}`!")
    return drive + path


def get_session():
    sess = requests.Session()
    sess.headers.update({"User-Agent": ua, "Referer": "https://www.tving.com/"})
    return sess


def tving_global_search(keyword, category, page="1", session=None):
    sess = get_session() if session is None else session
    api_url = "https://search-api.tving.com/search/getSearch.jsp"
    params = {
        "kwd": keyword,
        "category": "TOTAL",
        # 'category': 'PROGRAM',
        "pageNum": page,
        "screenCode": "CSSD0100",
        "networkCode": "CSND0900",
        "osCode": "CSOD0900",
        "teleCode": "CSCD0900",
        "apiKey": apikey,
        "notFoundText": keyword,
        # "userId": "",
        "siteName": "TVING_WEB",
        "pageSize": "20",
        "indexType": "both",
        "methodType": "allwordthruindex",
        "payFree": "ALL",
        "runTime": "ALL",
        "grade": "ALL",
        "genre": "ALL",
        "sort1": "NO",
        # "sort1": "score",
        # 'sort1': 'ins_dt',
        "sort2": "NO",
        # 'sort2': 'frequency',
        "sort3": "NO",
        "type1": "desc",
        "type2": "desc",
        "type3": "desc",
        "fixedType": "Y",
        "spcMethod": "someword",
        "spcSize": "0",
        "schReqCnt": "20",
        "vodBCReqCnt": "20",
        "programReqCnt": "20",
        "vodMVReqCnt": "20",
        "aloneReqCnt": "20",
        "smrclipReqCnt": "0",
        "pickClipReqCnt": "0",
        "cSocialClipCnt": "0",
        "boardReqCnt": "0",
        "talkReqCnt": "0",
        "nowTime": "",
        "mode": "normal",
        "adult_yn": "",
        "reKwd": "",
        "xwd": "",
    }
    if category.lower() == "tvp":
        pagesize = params["programReqCnt"]
        params.update({"category": "PROGRAM"})
        data_key = "programRsb"
    elif category.lower() == "mov":
        pagesize = params["vodMVReqCnt"]
        params.update({"category": "VODMV"})
        data_key = "vodMVRsb"
    else:
        raise NotImplementedError(f"Unknown category: {category}")

    res = sess.get(api_url, params=params)
    res.raise_for_status()
    data = res.json()[data_key]

    page = int(page)
    total = int(data["count"])
    pagesize = int(pagesize)
    currsize = len(data["dataList"])
    return {"list": data["dataList"], "nomore": currsize == 0 or total == pagesize * (page - 1) + currsize}
