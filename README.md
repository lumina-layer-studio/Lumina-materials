# Lumina Materials

Lumina Studio 的公开耗材档案与 LUT 数据仓库。当前可下载目录在 `public/v1`；历史源文件和旧构建材料保留用于溯源，不代表当前推荐目录。

The public material and LUT data repository for Lumina Studio. `public/v1` is the current approved download catalog. Historical source directories are retained for provenance.

## 当前目录 / Current catalog

- 662 份耗材档案、99 个 LUT，包括六朔厂商直接提供的 PETG CMYW 校准。
- 保留原作者、供稿来源、原文件名、资源 ID、修订和实际发布频道；厂商供稿不自动变成官方认证。
- Studio 可先预览，按项下载；源码版默认读取本目录，用户无需 GitHub 账号。
- 点赞、收藏和下载量是目录发布时的匿名统计快照，实时账号操作由独立耗材服务提供。

## 使用许可 / Data terms

允许接单打印、销售打印作品；采用新协议的数据禁止倒卖、收费分发和搭收费资源库。详见 [数据使用说明与协议](DATA-LICENSE.md)。已有许可的历史资源继续按原条款；公开不撤销旧许可，也不把未知署名改写为原创。商标与 Logo 不属于数据授权。

Paid printing and the sale of produced works are allowed. Resources expressly carrying the new Lumina data license may not be resold or distributed through paid data libraries. Existing per-resource licenses remain valid. See [the data terms](DATA-LICENSE.md).

## 离线包 / Offline collections

固定版本资源包含全部已审核公开的官方与社区条目，保持各自的实际频道。两包用于浏览和按项添加，不在启动时安装全库。

```sh
python scripts/build_public_seeds.py --public-dir public/v1 --dataset-version 2026.11.18.1 --output build/public-resources
```

构建只读取本地公开快照，逐包校验哈希和身份，原始分发 ZIP 保持不变。同名耗材独立保存，避免覆盖。包内保留使用说明。下载固定版本请见本仓库 Releases。

`materials-src`、`packages`、`luts-src`、`lut-packages`、`seed` 及旧构建脚本用于历史重建；当前完整离线包以 `public/v1` 为输入。资源审核、账号与软件部署代码在各自仓库维护，不进入本仓库。
