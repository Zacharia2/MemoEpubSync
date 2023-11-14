# encoding:utf-8
#!/usr/bin/env python
"""SMKit CLI Tool
Usage:
    smkit set config <key> <value>
    smkit get config --all
    smkit e2sm <epub-path> <targetfolder>
    smkit pathpix <collection>
    smkit clist
    smkit indexer <epub> <output>

Options:
    -h --help       Show Help doc.
    -v --version    Show Version.
"""
import shutil
import docs.conf
from docopt import docopt
from epub2sm import epub2sm
from pathpix import index as pathpix
import os


def move_to_primaryStorage(source_folder_name, target_folder):
    shutil.move(source_folder_name, target_folder)


# Main
# 需要填写sm的位置
# sm_location = "C:/Users/Snowy/Desktop/sm18"

# def set_sm_location(sm_path):
#     global sm_location
#     sm_location = sm_path


def cmd():
    args = docopt(__doc__)
    this_folder = os.path.dirname(os.path.abspath(__file__))
    conf_path = os.path.join(this_folder, "conf.json")
    m_conf = docs.conf.read_config(conf_path)
    sm_location = m_conf["program"]

    if args.get("set") and args.get("config"):
        if args["<key>"] == "program":
            m_conf["program"] = args["<value>"]
            docs.conf.update_config(conf_path, m_conf)
            m_conf = docs.conf.read_config(conf_path)
            print(m_conf)

    elif args.get("get") and args.get("config"):
        print(docs.conf.read_config(conf_path))

    elif args.get("e2sm"):
        # python index.py e2s a b
        epub2sm.start(args["<epub-path>"], args["<targetfolder>"])

    elif args.get("pathpix"):
        # smkit pathpix --least-col
        # sm_system1 = docs.conf.read_sm_system1(sm_location)
        # least_used_col = docs.conf.get_collection_primaryStorage(
        #     sm_location, sm_system1
        # )
        # save_img_folder = os.path.join(least_used_col, "web_pic")
        # # if args['<collection>']
        # print(least_used_col)
        # print(save_img_folder)
        # pathpix.relative_and_localize(least_used_col, save_img_folder)
        col_folder = docs.conf.get_collection_primaryStorage(
            sm_location, args["<collection>"]
        )
        collection_temp_path = docs.conf.get_collections_temp(
            os.path.join(sm_location, "systems", args["<collection>"])
        )
        save_img_folder = os.path.join(col_folder, "web_pic")
        print("集合元素：", col_folder)
        print("图片位置：", save_img_folder)
        print("临时文件：", collection_temp_path)
        pathpix.start(col_folder, save_img_folder, collection_temp_path)
    elif args.get("clist"):
        # python index.py e2s a
        # print("#" * 100)
        # print(args["<valueA>"])
        # epub2sm.test()
        col_list = docs.conf.get_collections_primaryStorage(sm_location)
        for col_name in col_list:
            print("集合名称：", col_name)


if __name__ == "__main__":
    cmd()
