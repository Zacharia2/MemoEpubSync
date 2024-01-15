import os
import re
import sys
import xml.etree.ElementTree as ET
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup, Doctype
import pypinyin

sys.path.insert(0, sys.path[0] + "/../")
from epub2sm.toc_units import org_toc, check_toc  # noqa: E402


def mkdir(path):
    folder = os.path.exists(path)
    if not folder:
        os.makedirs(path)
        print("创建文件夹:: " + path)


def create_supermemo_element(parent_element, element_data):
    supermemo_element = ET.SubElement(parent_element, "SuperMemoElement")

    for key, value in element_data.items():
        if key == "SuperMemoElement":
            for sub_element_data in value:
                create_supermemo_element(supermemo_element, sub_element_data)
        elif key == "Content":
            content = ET.SubElement(supermemo_element, "Content")
            for sub_key, sub_value in value.items():
                sub_element = ET.SubElement(content, sub_key)
                sub_element.text = str(sub_value)
        else:
            sub_element = ET.SubElement(supermemo_element, key)
            sub_element.text = str(value)


def create_xml(data, target_file):
    """输入data, 创建SuperMemo-XML-Book

    Args:
        data (_type_): _description_
        target_file (_type_): SuperMemo-XML书籍文件的绝对路径
    """

    root = ET.Element("SuperMemoCollection")

    count = ET.SubElement(root, "Count")
    count.text = str(count_ids(data))

    for element_data in data:
        create_supermemo_element(root, element_data)

    tree = ET.ElementTree(root)
    tree.write(target_file, encoding="utf-8", xml_declaration=True)


def count_ids(data):
    count = 0
    for item in data:
        if "ID" in item:
            count += 1
        if "SuperMemoElement" in item:
            count += count_ids(item["SuperMemoElement"])
    return count


def set_unique_id(data):
    """为SuperMemo元素设置id

    Args:
        data (_type_): _description_
    """
    count = 1

    def recursively_set_id(element):
        nonlocal count
        element["ID"] = count
        count += 1

        if "SuperMemoElement" in element:
            for sub_element in element["SuperMemoElement"]:
                recursively_set_id(sub_element)

    for element in data:
        recursively_set_id(element)


def makeNameSafe(name):
    illegalFilenameCharacters = r"/<|>|\:|\"|\/|\\|\||\?|\*|\^|\s/g"
    fixedTitle = re.sub(illegalFilenameCharacters, "_", name)
    return fixedTitle


# 全角转半角
def full_to_half(text: str):  # 输入为一个句子
    _text = ""
    for char in text:
        inside_code = ord(
            char
        )  # 以一个字符（长度为1的字符串）作为参数，返回对应的 ASCII 数值
        if inside_code == 12288:  # 全角空格直接转换
            inside_code = 32
        elif 65281 <= inside_code <= 65374:  # 全角字符（除空格）根据关系转化
            inside_code -= 65248
        _text += chr(inside_code)
    return _text


def trans_pinyin(str):
    trans_list = []
    half_text = full_to_half(str)
    for pinyin_name in pypinyin.pinyin(half_text, style=pypinyin.NORMAL):
        for pinyin_name_ in pinyin_name:
            pinyin_name__ = pinyin_name_.capitalize()
            trans_list.append(pinyin_name__)
    return "".join(trans_list)


# resolved：空格变问号的问题
# https://blog.csdn.net/u013778905/article/details/53177042
# 符号库：https://www.fuhaoku.net/U+00A9
def make_escape_safe(html_str):
    escapeSequence = {
        "EM SPACE": (chr(0x2003), "&ensp;"),
        "COPYRIGHT SIGN": (chr(0x00A9), "&copy;"),
        "EM DASH": (chr(0x2014), "&#8212;"),
        "chapterlast": (chr(0xF108), "&#10048;"),
        "REPLACEMENT CHARACTER": (chr(0xFFFD), "&#65533;"),
    }
    for escape in escapeSequence.values():
        html_str = html_str.replace(escape[0], escape[1])
    return html_str


# 写入数据结构时，必要调用的函数之一。
def modify_img_url(doc, foldername):
    soup = BeautifulSoup(doc, "html.parser")
    # 删除DOCTYPE定义
    for item in soup.contents:
        if isinstance(item, Doctype):
            item.extract()
            break
    # 处理图片
    imgs = soup.find_all("img")
    for img in imgs:
        # 新的图片将会放在一个全英文下面的文件中，文件夹名字以书名命名。
        img_name = img.attrs["src"].split("/")[-1]
        img.attrs["src"] = f"file:///[PrimaryStorage]local_pic/{foldername}/{img_name}"
    return make_escape_safe(str(soup))


def write_imgfile(ebook, target_folder, imgs_folder_name):
    """写出img文件到SuperMemo-XML-Book文件旁边的文件夹中。

    Args:
        ebook (_type_): epub实例
        target_folder (str): 目标文件夹
        imgs_folder_name (str): SuperMemo-XML-Book文件旁边的文件夹。
    """
    for image in ebook.get_items_of_type(ebooklib.ITEM_IMAGE):
        # 可以得到image.file_name 和 image.content二进制数据、image.media_type
        # os.path.abspath(".")
        folder_path = os.path.join(target_folder, imgs_folder_name)
        mkdir(folder_path)
        if (image.file_name).find("/") != -1:
            filename = image.file_name.split("/")[-1]
            file_path = os.path.join(folder_path, filename)
        else:
            file_path = os.path.join(folder_path, image.file_name)
        with open(file_path, "wb") as f:
            f.write(image.content)


def getContent(book, href):
    if href.find("#") != -1:
        doc_href = href.split("#")[0]
        doc = book.get_item_with_href(doc_href)
        Content = doc.content.decode("utf-8") if doc else ""
    else:
        # 没有锚点。说明是一个文件。
        doc = book.get_item_with_href(href)
        Content = doc.content.decode("utf-8") if doc else ""
    return Content


# {"Question": modify_img_url(section, foldername)}
# {"Question": ""}
def get_documents_by_toc(book, chapters, foldername):
    mList = []
    for chapter in chapters:
        # 把这一层处理好，再去处理下一层。
        # 这一层和下一层的逻辑一致。
        if isinstance(chapter, epub.Link):
            title = chapter.title
            href = chapter.href
            Content = {"Question": modify_img_url(getContent(book, href), foldername)}
            element = {"Title": title, "Type": "Topic", "Content": Content}
            mList.append(element)
        # 是元组的时候就说明是有子集的数据。这个元组代表当前的数据。元组的内容代表下一层数据。
        # 在元组中，其中第一个元素是本层的数据，第二个元素是下一层的数据，也是入口。
        # 这个的子元素的入口、以及超子集元素之间的关联位点。
        if isinstance(chapter, tuple):
            if isinstance(chapter[0], epub.Section):
                title = chapter[0].title
                href = chapter[0].href
                Content = {
                    "Question": modify_img_url(getContent(book, href), foldername)
                }
                element = {
                    "Title": title,
                    "Type": "Topic",
                    "Content": Content,
                    # "SuperMemoElement": SuperMemoElement,
                }
                mList.append(element)
            # 当元组的第二个元素有子元素的时候。
            if isinstance(chapter[1], list):
                SubElementList = get_documents_by_toc(book, chapter[1], foldername)
                element["SuperMemoElement"] = SubElementList
    return mList


def get_documents_by_docList(book, foldername):
    mList = []
    docList = book.get_items_of_type(ebooklib.ITEM_DOCUMENT)
    for doc in docList:
        href = doc.file_name
        Content = {"Question": modify_img_url(getContent(book, href), foldername)}
        element = {"Type": "Topic", "Content": Content}
        mList.append(element)
    return mList


def create_sm_book_by_toc(book, book_f_name, target_folder=os.getcwd()):
    # 创建数据结构
    toc = org_toc.merge_doc(book)
    diff_list = check_toc.contrast_diff_toc(toc, book)
    if len(diff_list) == 0:
        print("内容完整性: True")
        res = get_documents_by_toc(book, toc, book_f_name)
        # 这个是Collection下的第一个SuperMemoElement
        rootElement = [
            {"Title": book.title, "Type": "Concept", "SuperMemoElement": res}
        ]
        set_unique_id(rootElement)
        sm_book_file_path = os.path.join(target_folder, book_f_name + ".xml")

        # 根据数据结构创建XML文件
        create_xml(rootElement, sm_book_file_path)
        img_folder_name = book_f_name
        write_imgfile(book, target_folder, img_folder_name)
    else:
        print("内容完整性: False;/n", diff_list)


def create_sm_book_by_docList(book, book_f_name, target_folder=os.getcwd()):
    # 创建数据结构
    res = get_documents_by_docList(book, book_f_name)
    rootElement = [{"Title": book.title, "Type": "Concept", "SuperMemoElement": res}]
    set_unique_id(rootElement)

    # 根据数据结构创建XML文件
    sm_book_file_path = os.path.join(target_folder, book_f_name + ".xml")
    create_xml(rootElement, sm_book_file_path)
    img_folder_name = book_f_name
    write_imgfile(book, target_folder, img_folder_name)


def start_with_toc(epubfile, savefolder):
    # UserWarning: In the future version we will turn default option ignore_ncx to True.
    #   warnings.warn('In the future version we will turn default option ignore_ncx to True.')
    book = epub.read_epub(epubfile, {"ignore_ncx": True})
    book_img_folder_name = makeNameSafe(trans_pinyin(book.title))
    print("开始处理书籍：", book_img_folder_name)
    # 可以自定义输出路径。
    create_sm_book_by_toc(book, book_img_folder_name, savefolder)
    print("转换完成，已存储至：", savefolder)


def start_with_linear(epubfile, savefolder):
    book = epub.read_epub(epubfile, {"ignore_ncx": True})
    book_img_folder_name = makeNameSafe(trans_pinyin(book.title))
    print("开始处理书籍：", book_img_folder_name)
    create_sm_book_by_docList(book, book_img_folder_name, savefolder)
    print("转换完成，已存储至：", savefolder)


# start_with_toc("C:/Users/Snowy/Desktop/资本论.epub", "C:/Users/Snowy/Desktop")
