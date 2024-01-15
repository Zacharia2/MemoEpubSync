# supermemo-toolkit(smtk)

SuperMemo工具组件，增强工具。


## PathPix

> supermemo图链整理工具。

PathPix功能说明、下载安装使用文档：https://docs.qq.com/doc/DQnRpb0VNUEVvR3dl

网页内嵌图片由pathpix管理，元素注册表图片由图片注册表管理。pathpix管理的图片文件，可以导入图片注册表中。

## E2SM

从epub图书生成xml格式的sm-book图书。

生成的书籍图片文件夹放到elements/local_pic文件夹下即可。

```pwsh
smtk e2sm -t epub_file out_folder  #（需要图书有良好的目录，没有需使用calibre生成并整理目录）
smtk e2sm -l epub_file out_folder  #（有书即可，按照图书文档文件的线性顺序生成）
```

## Install

进入项目根目录，然后执行

```py
pip install .
```

## LICENSE

本软件遵守开源协议，协议类型为：GPLv2。

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=Zacharia2/SuperMemo-Toolkit&type=Date)](https://star-history.com/#Zacharia2/SuperMemo-Toolkit&Date)
