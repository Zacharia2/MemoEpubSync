import os
import re
import sys

from bs4 import BeautifulSoup

sys.path.insert(0, sys.path[0] + "/../")
from smtk.scripts import config  # noqa: E402


def is_md_ext_file(file_path):
    file_ext = os.path.splitext(file_path)[1].lower()
    return file_ext in [".md"]


def is_start_with_num(path):
    num_partten = r"\d\d"
    basename = os.path.basename(path)
    num = re.findall(num_partten, basename)
    if len(num) > 0 and int(num[0]) > 0:
        return True
    else:
        return False


def iter_dir(folder: str):
    file_list = []
    count_processed = 0

    stack = [folder]
    while stack:
        current_path = stack.pop()
        for entry in os.scandir(current_path):
            if (
                entry.is_file()
                and is_md_ext_file(entry.path)
                and is_start_with_num(entry.path)
            ):
                # 必须是md文件，且文件名称开头首先是数字，其次必须大于1（从01开始）。
                file_list.append(entry.path)
                count_processed += 1
                print(
                    "正在计算文件总数",
                    f"[{count_processed}]",
                    end="\r",
                )
            if entry.is_dir() and is_start_with_num(entry.path):
                stack.append(entry.path)
    print(f"\n共找到 {count_processed} 个文件")
    return file_list


def split_list(split_index: list, target_list: list) -> list:
    # 根据下标分割列表。
    result = list()
    count = 0
    indexs = [0] + split_index + [len(target_list)]
    for index, item in enumerate(indexs):
        # 分割次数 = 索引刀 + 1
        if count < len(split_index) + 1:
            result.append(target_list[indexs[index] : indexs[index + 1]])
            count += 1
    return result


def read_file(path_list):
    filter_list = list()
    result_dict = dict()
    for path in path_list:
        RText = "D:/Dropbox/00-TMP/英语词义分类数据库（大学版）（带词汇表目录）/英语词义分类数据库（大学版）"
        cclass = path.split(RText)[1].split(".")[0].replace("\\", "/")
        with open(path, "r", encoding="utf-8") as f:
            origin_list = f.readlines()
        for item in origin_list:
            if re.search(r"class", item) is not None:
                filter_list.append(item)
        index_category = list()
        for aindex, item in enumerate(filter_list):
            if "category" in item and aindex != 0:
                index_category.append(aindex)
        categorys = split_list(index_category, filter_list)
        index_vocabulary = list()
        vocabulary_list = list()
        for category in categorys:
            for bindex, item in enumerate(category):
                if "vocabulary" in item and bindex != 0:
                    index_vocabulary.append(bindex)
            vocabulary = split_list(index_vocabulary, category)
            vocabulary_list.append(vocabulary)
            index_vocabulary.clear()
        for category in vocabulary_list:
            a_category: str
            for voc in category:
                if len(voc) == 1 and "category" in voc[0]:
                    soup = BeautifulSoup(voc[0], "html.parser")
                    a_category = re.findall(r"\*\*(.*?)\*\*", soup.get_text())
                    if a_category is not None and a_category != []:
                        a_category = a_category[0]
                    if a_category == []:
                        a_category = ""
                if len(voc) == 2 and "vocabulary" in voc[0]:
                    voc.reverse()
                    mvoc = voc.pop()
                    soup = BeautifulSoup(mvoc, "html.parser")
                    voc.append(mvoc)
                    voc.reverse()
                    a_voc = re.findall(r"\*\*(.*?)\*\*", soup.get_text())[0]
                    result_dict.update({a_voc: [cclass + "/" + a_category, voc]})
                    print(cclass + "/" + a_category + a_voc)
    return result_dict


a = iter_dir(
    "D:/Dropbox/00-TMP/英语词义分类数据库（大学版）（带词汇表目录）/英语词义分类数据库（大学版）"
)
b = read_file(a)

config.update_config("./m.json", b)
