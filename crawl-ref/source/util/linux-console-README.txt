DCSS 中文字符版（Linux x86_64）

此包在 Ubuntu 22.04 x86_64 上构建。解压后在支持 UTF-8 的终端内进入目录：

    cd stone_soup-console-0.34
    ./crawl

请使用 UTF-8 locale 和支持中文的等宽终端字体；地图以字符显示，界面仍为中文。
不要将 crawl 单独移出目录，dat、docs 和 settings 是运行所需的数据。
存档位于包内 saves/，战报位于 morgue/；升级前请备份旧目录。

Ubuntu 22.04 的运行依赖（其他发行版请安装等价软件包）：
    sudo apt install libncursesw6 libtinfo6 liblua5.4-0 libsqlite3-0 zlib1g

还需要系统自带的 glibc 与 libstdc++；若报告 GLIBC/GLIBCXX 版本不足，请使用
较新的发行版，或从本项目源码自行编译。本包不支持 ARM 或 32 位 Linux。
可用 ldd ./crawl 查看当前系统尚缺少的动态库。
