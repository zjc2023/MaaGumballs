<!-- markdownlint-disable MD033 MD041 -->
<p align="center">
  <img alt="LOGO" src="https://cdn.jsdelivr.net/gh/MaaAssistantArknights/design@main/logo/maa-logo_512x512.png" width="256" height="256" />
</p>

<div align="center">

# MaaGumballs

</div>

本仓库为 [MaaFramework](https://github.com/MaaXYZ/MaaFramework) 所提供的项目模板，开发者可基于此模板直接创建自己的 MaaXXX 项目。

> **MaaFramework** 是基于图像识别技术、运用 [MAA](https://github.com/MaaAssistantArknights/MaaAssistantArknights) 开发经验去芜存菁、完全重写的新一代自动化黑盒测试框架。
> 低代码的同时仍拥有高扩展性，旨在打造一款丰富、领先、且实用的开源库，助力开发者轻松编写出更好的黑盒测试程序，并推广普及。

## 即刻开始

- [📄 快速开始](https://github.com/MaaXYZ/MaaFramework/blob/main/docs/zh_cn/1.1-%E5%BF%AB%E9%80%9F%E5%BC%80%E5%A7%8B.md)
- [🎞️ 视频教程](https://www.bilibili.com/video/BV1yr421E7MW)

## 如何开发

0. 使用右上角 `Use this template` - `Create a new repository` 来基于本模板创建您自己的项目。

1. 完整克隆本项目及子项目（地址请修改为您基于本模板创建的新项目地址）。

    ```bash
    git clone --recursive https://github.com/KhazixW2/MaaGumballs.git
    ```

    **请注意，一定要完整克隆子项目，不要漏了 `--recursive`，也不要下载 zip 包！**  
    这步未正确操作会导致所有 OCR（文字识别）失败！

2. 下载 MaaFramework 的 [Release 包](https://github.com/MaaXYZ/MaaFramework/releases)，解压到 `deps` 文件夹中。

3. 配置资源文件。

    ```bash
    python ./configure.py
    ```

4. 按需求修改 `assets` 中的资源文件，请参考 MaaFramework 相关文档。

    - 可使用 [MaaDebugger](https://github.com/MaaXYZ/MaaDebugger) 进行调试；
    - 也可以在本地安装后测试：

        1. 执行安装脚本

            ```bash
            python ./install.py
            ```

        2. 执行`MaaPiCli`

            - **Windows**

                运行 `install/MaaPiCli.exe`

            - **Linux/macOS**

                > 如果提示缺少启动权限，可通过 `chmod a+x install/MaaPiCli` 命令添加

                运行 `install/MaaPiCli`

5. 更多操作，请参考[个性化配置](./docs/zh_cn/个性化配置.md)（可选）

## Todo（先画饼）

- [x]启动
  - [x]进入游戏大厅

- [ ]每日收菜
  - [x]每日签到
  - [x]炼金招牌
  - [x]派遣魔蜥
  - [x]每日扫荡
  - [x]天空探索
  - [x]遗迹探索
  - [x]荒野探索
  - [ ]马戏团任务
  - [ ]其他任务

- [ ]商店购物————
  - [ ]旅游商店——默认购买所有金币商品
  - [ ]佣兵商店——默认全部购买
  - [ ]天空商店——默认购买所有遗迹碎片商品
  - [ ]联盟商店——默认不购买
  - [ ]混沌商店——默认不购买

- [ ]战斗————阵容和地图隐藏可能要单独写，或者合并写
  - [ ]养狗速刷100层
  - [ ]王帝夜100层
  - [ ]白学100层
  - [ ]神锻速刷100层
  - [ ]xx地图隐藏

- [ ]外域探索
  - [ ]每日星域探索/征收——设置资源星/小行星
  - [ ]速刷情报
  - [ ]

- [ ]奖励
  - [ ]联盟任务一键完成
  - [ ]联盟礼包
  - [ ]邮件奖励
  - [ ]地图彩蛋

## 鸣谢

本项目由 **[MaaFramework](https://github.com/MaaXYZ/MaaFramework)** 强力驱动！

感谢以下开发者对本项目作出的贡献:

[![Contributors](https://contrib.rocks/image?repo=KhazixW2/MaaGumballs)](https://github.com/KhazixW2/MaaGumballs/graphs/contributors)
