# MaaPiCli 操作说明~~（翻译文档）~~

- [MaaPiCli 操作说明~~~~](#maapicli-操作说明翻译文档)
  - [选择ADB](#选择adb)
  - [选择设备](#选择设备)
  - [选择资源](#选择资源)
  - [添加任务](#添加任务)
  - [功能菜单](#功能菜单)
  - [进阶使用](#进阶使用)

## 选择ADB

当您初次下载，没有配置时会出现下面界面：

```plaintext
Welcome to use Maa Project Interface CLI!
MaaFramework: v4.3.2

Version: v0.0.1

### Select ADB ###

        1. Auto detect
        2. Manual input

Please input [1-2]:
```

这里 Version 后跟着的是当前资源版本。  
`### Select ADB ###` 翻译过来是当前操作为 `选择 ADB（Android Debug Bridge，这里一般用来操作模拟器）`。  
后面列出选项：

1. 自动检测（推荐，在目标模拟器启动时选择）
2. 手动输入（参考[ADB 路径](连接设置.md#adb-路径)和[ADB 连接地址](连接设置.md#连接地址)填写）

后面 `Please input [1-2]:` 翻译过来是 `请输入 [选项范围]`，请根据需要选择。

这里我们输入 1 后回车，进入下一步。

## 选择设备

紧跟上一步，选择自动检测可到此步骤，显示为：

```plaintext
Finding device...

## Select Device ##

        1. MuMuPlayer12
                F:/Program Files/Netease/MuMu Player 12/shell/adb.exe
                127.0.0.1:16384

Please input [1-1]:
```

这里因为只开了一个模拟器，只显示一条选项，直接输入 1 后回车，完成此步骤

## 选择资源

```plaintext
### Select resource ###

        1. 官服        
        2. xiaomi      
        3. huawei      
        4. oppo        
        5. vivo        
        6. 4399
        7. bilibili
        8. 港台服

Please input [1-8]
```

这里根据需要的资源进行选择，主要和 `启动游戏`和`登陆方式有关` 等各个服务器有所区别的功能有关。

## 添加任务

这里是添加任务，显示如下：

```plaintext
### Add task ###

        1. 启动游戏
        2. 每日收菜
        3. 联盟奖励
        4. 商店自动购物
        5. 一键领取好友礼物
        6. 刷竞技场
        7. 刷竞技场_局内
        8. 自动叫狗
        9. 黑永恒
        10. 黑日光
        11. 黑水池
        12. 神锻测序(测试)
        13. 退出游戏

Please input multiple [1-13]:
```

首先显示的总菜单，根据需求选择，这里可以同时选多个功能，像：

```plaintext
Please input multiple [1-15]: 1 2 3 4 5 13
```

## 功能菜单

初次启动配置完，或者之前配置过的，便会到当前界面，内容如下：

```plaintext
Controller:

        ADB 默认方式
                D:/Program Files/Netease/MuMu Player 12/shell/adb.exe
                127.0.0.1:16384

Resource:

        官服

Tasks:

        - 启动游戏
        - 神锻测序(测试)
                - 目标日光数及自动熔设定: 18日光/自动熔至3星用完

### Select action ###

        1. Switch controller
        2. Switch resource
        3. Add task
        4. Move task
        5. Delete task
        6. Run tasks
        7. Exit

Please input [1-7]:
```

展示了 Controller（当前控制器，于选择设备设置）、Resource（当前资源）、Tasks（当前待执行任务列表）。  
并给出功能菜单（Select action），依次为：  

1. 更换控制器
2. 更换资源
3. 添加任务
4. 移动任务
5. 删除任务
6. 运行任务
7. 退出

确定 Tasks 部分配置完成便可在输入 6 并回车后运行任务。

## 进阶使用

- 在命令行中添加 `-d` 参数运行即可跳过交互直接运行任务，如 `./MaaPiCli.exe -d`
- 2.0 版本已支持 mumu 后台保活，会在 run task 时获取 mumu 最前台的 tab，并始终使用这个 tab（即使之后被切到后台了）
