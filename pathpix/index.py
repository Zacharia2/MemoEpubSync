import html
import shutil
import uuid
from bs4 import BeautifulSoup
import re
import os
import time
import requests
from PIL import Image
import urllib


def mkdir(path):
    folder = os.path.exists(path)
    if not folder:
        os.makedirs(path)
        print("创建文件夹:: " + path)


def is_utf8_supported_in_gbk(char):
    code = ord(char)
    try:
        chr(code).encode("gbk")
        return True
    except ValueError:
        print(
            f"Unicode code point: {code}",
            f"无法找到对应的GBK字符, 将使用字符实体 (numeric character reference) '&#x{code};' 替代",
        )
        return (chr(code), f"&#x{code};")


# 最好可以自动将不支持的字符转换为字符实体。
# 挨个读取字符，判断gb2312是否支持，不支持就变成字符实体。
def make_escape_safe(html_str):
    escapeSequence = {
        "EM SPACE": (chr(0x2003), "&ensp;"),
        "COPYRIGHT SIGN": (chr(0x00A9), "&copy;"),
        "EM DASH": (chr(0x2014), "&#8212;"),
        "chapterlast": (chr(0xF108), "&#10048;"),
        "REPLACEMENT CHARACTER": (chr(0xFFFD), "&#65533;"),
        "WHITE FLORETTE": (chr(0x2740), "&#10048;"),
        "START OF SELECTED AREA": (chr(0x0086), "&#x0086;"),
    }
    for escape in escapeSequence.values():
        html_str = html_str.replace(escape[0], escape[1])

    nosupp_char_list = []
    for char in html_str:
        result_bool = is_utf8_supported_in_gbk(char)
        if not result_bool:
            nosupp_char_list.append(result_bool)

    for char_tuple in nosupp_char_list:
        html_str = html_str.replace(char_tuple[0], char_tuple[1])
    return html_str


def is_in_elements_directory(path, directory):
    """判断是否在elements文件夹内。windows路径。

    Args:
        path (str): 任意文件夹路径
        directory (str): SM完整的集合中的元素文件夹路径

    Returns:
        bool: 在, 返回True; 不在, 返回False
    """
    path = path.replace("\\", "/")
    directory = directory.replace("\\", "/")
    # 解码URL路径，转换为文件系统路径
    fs_path = urllib.parse.unquote(path)
    # 获取文件夹路径
    directory_name = os.path.dirname(fs_path)
    # 判断给定路径是否以指定目录开头
    return directory_name.startswith(directory)


def is_html_file(name):
    name = name.lower()
    return name.endswith(".html") or name.endswith(".htm")


def is_url(str):
    v = re.compile(
        "^(?!mailto:)(?:(?:http|https|ftp)://|//)(?:\\S+(?::\\S*)?@)?(?:(?:(?:[1-9]\\d?|1\\d\\d|2[01]\\d|22[0-3])(?:\\.(?:1?\\d{1,2}|2[0-4]\\d|25[0-5])){2}(?:\\.(?:[0-9]\\d?|1\\d\\d|2[0-4]\\d|25[0-4]))|(?:(?:[a-z\\u00a1-\\uffff0-9]+-?)*[a-z\\u00a1-\\uffff0-9]+)(?:\\.(?:[a-z\\u00a1-\\uffff0-9]+-?)*[a-z\\u00a1-\\uffff0-9]+)*(?:\\.(?:[a-z\\u00a1-\\uffff]{2,})))|localhost)(?::\\d{2,5})?(?:(/|\\?|#)[^\\s]*)?$",
        re.IGNORECASE,
    )
    return bool(v.match(str))


def is_relative_path(string):
    # string = "file:///[PrimaryStorage]path/to/file"
    return string.startswith("file:///[PrimaryStorage]")


# 还有这种：'file:///C:/Users/Snowy/Desktop/sm18/必读：旅途的开始.png'
# 'C:/Users/Snowy/Desktop/sm18/systems/Noname/elements/web_pic\\im_2023-11-09-20_39_50_plot_19.jpeg'
def relativized_path(url):
    """将位于sm的elements文件夹中的文件的绝对路径转换为相对路径.

    Args:
        url (str): url =
            "file:///z:/path/systems/collection/elements/path/to/file"

            "z:/path/systems/collection/elements/path/to/file"

    Returns:
        str: file:///[PrimaryStorage]path/to/file
    """
    url = url.replace("\\", "/")
    if not url.startswith("file:///") and os.path.exists(url):
        # 统一为 "file:///.*?elements/"
        url = "file:///" + url

    pattern = re.compile(r"file:///.*?elements/")
    src_path = pattern.sub("file:///[PrimaryStorage]", url)
    return src_path


def im_download_and_convert(url, saved_path, collection_temp_path):
    """给定url, 下载图片并转换, 返回保存图片的绝对路径

    Args:
        url (str): img标签中的src值
        saved_path (_type_): 绝对路径, 保存img到指定目录

    Returns:
        str: 绝对路径, drive:/path/sm18/systems/col/elements/path/to/file.ext'
    """
    supports_im_type = ["image/jpeg", "image/jpg", "image/png"]
    response = requests.get(url)
    content_type = response.headers.get("Content-Type")

    now = time.strftime("%Y-%m-%d-%H_%M", time.localtime(time.time()))
    file_name = "im_" + now + "_plot_" + str(uuid.uuid4())

    if content_type and content_type.startswith("image/"):
        im_bytes = response.content
        if content_type not in supports_im_type:
            extension = content_type.split("/")[1]
            try:
                # temp_path = os.path.join(saved_path, "temp")
                mkdir(collection_temp_path)
                temp_file_path = os.path.join(
                    collection_temp_path, file_name + f".{extension}"
                )
                # 先把webp写到temp文件夹，然后再处理。
                with open(temp_file_path, "wb") as f:
                    f.write(im_bytes)

                # 转换图片格式。
                with Image.open(temp_file_path) as im:
                    print(im.format, im.size, im.mode)
                    # 这里是输出路径。
                    mkdir(saved_path)
                    saved_path = os.path.join(saved_path, file_name + ".png")
                    im.save(saved_path, "png")
                    return saved_path
            except IOError:
                print("IOError! Cannot convert", url)
        else:
            extension = content_type.split("/")[1]
            # 如果支持的话，就直接写入的路径中即可。
            mkdir(saved_path)
            saved_path = os.path.join(saved_path, file_name + f".{extension}")
            # 必须先创建文件夹。
            with open(saved_path, "wb") as f:
                f.write(im_bytes)
            return saved_path
    else:
        print("警告！非图片资源链接 ", url)


def modify_src(html_doc, im_saved_path, elements_path, collection_temp_path):
    soup = BeautifulSoup(html_doc, "html.parser")

    img_tags = soup.find_all("img")
    is_modify = False
    for img in img_tags:
        src = img.attrs["src"]
        if is_url(src):
            im_local_path = im_download_and_convert(
                src, im_saved_path, collection_temp_path
            )
            img.attrs["src"] = relativized_path(im_local_path)
            is_modify = True
        elif not is_relative_path(src):
            # 绝对路径
            # 去掉前缀
            src = src.replace("\\", "/")
            if src.startswith("file:///"):
                fs_path = src.split("file:///")[1]
            else:
                fs_path = src
            # 在不在集合的元素文件夹中。
            if is_in_elements_directory(fs_path, elements_path):
                img.attrs["src"] = relativized_path(fs_path)
                is_modify = True
            else:
                # 不在，移动到集合元素文件夹的web_im_saved_path。
                old_full_file_name = os.path.basename(fs_path)
                target = os.path.join(im_saved_path, old_full_file_name)
                shutil.copyfile(fs_path, target)
                img.attrs["src"] = relativized_path(target)
                is_modify = True
        elif is_relative_path(src):
            is_modify = False
    # 删除临时文件夹。
    # print("删除临时文件夹::", collection_temp_path)
    # shutil.rmtree(collection_temp_path)
    if is_modify:
        return make_escape_safe(str(soup))
    else:
        return False


def relative_and_localize(elements_path, web_im_saved_path, collection_temp_path):
    """在遍历查找html文件时, 一个个处理他们，并返回处理后的文件列表。

    Args:
        element_path (str): elements路径

    Returns:
        list: 处理后的文件列表
    """
    failed_process_htm_files = []
    processed_htm_files = []

    def find_htm_files(directory):
        nonlocal failed_process_htm_files
        with os.scandir(directory) as entries:
            for entry in entries:
                if entry.is_file() and is_html_file(entry.name):
                    # todo something
                    try:
                        with open(entry.path, "r+", encoding="GBK") as f:
                            # 转义序列转换为字符。
                            unescape_content = html.unescape(f.read())
                            modified_content = modify_src(
                                unescape_content,
                                web_im_saved_path,
                                elements_path,
                                collection_temp_path,
                            )
                            if modified_content:
                                print("正在处理：", entry.path)
                                f.seek(0)
                                f.write(modified_content)
                                f.truncate()
                                processed_htm_files.append(entry.path)
                    except IOError:
                        failed_process_htm_files.append(entry.path)

                if entry.is_dir():
                    find_htm_files(entry.path)

    find_htm_files(elements_path)
    if len(processed_htm_files) == 0:
        print("PathPix:: 无事可做。")
    else:
        print("以下文件已修改：")
        for item in processed_htm_files:
            print(item)
    return failed_process_htm_files


relative_and_localize(
    "C:/Users/Snowy/Desktop/sm18/systems/ZiBenLun(JiNianBan)QuanSanJuan/elements",
    "C:/Users/Snowy/Desktop/sm18/systems/ZiBenLun(JiNianBan)QuanSanJuan/elements/web_pic",
    "C:/Users/Snowy/Desktop/sm18/systems/ZiBenLun(JiNianBan)QuanSanJuan/temp",
)
