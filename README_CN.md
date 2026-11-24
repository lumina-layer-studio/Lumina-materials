# Lumina Materials

[English](README.md) · [简体中文](README_CN.md) · [目录结构](#目录结构) · [离线资源包](#离线资源包) · [数据使用协议](#数据使用协议) · [Lumina Studio](https://github.com/lumina-layer-studio/Lumina-Layers)

[Lumina Studio](https://github.com/lumina-layer-studio/Lumina-Layers) 的公开耗材校准档案与 LUT 预设仓库。

当前可下载目录位于 `public/v1/`。Lumina Studio 可直接预览并按需下载其中的耗材档案与固定色卡 LUT，无需登录 GitHub 账号。

## 收录内容

- **662 份耗材档案**与 **99 个 LUT 预设**，涵盖官方校准、社区投稿以及厂商供稿数据（包括[六朔 PETG CMYW 校准数据](docs/manufacturer-sources.md)）。
- 每条资源完整保留原作者、供稿来源、原始文件名、资源 ID、修订版本及实际发布频道（`official` 或 `community`）。
- `activity.json` 记录目录同步时的下载、点赞与收藏匿名统计快照。

## 在 Lumina Studio 中使用

在 Lumina Studio 的材料库中，可以先浏览色板和参数预览，再挑自己手头在用的耗材档案或 LUT 单独下载。导入本机材料库后即可离线参与分层混色计算。

固定色卡与梯度色卡的打印、拍照和取色方法，可参考 [Lumina Studio Wiki](https://wiki.luminastudio.com.cn/)。

## 目录结构

```text
public/v1/
├── DATA-LICENSE.md          # Lumina 数据使用说明与协议 1.0（中英双语）
├── materials/
│   ├── catalog.json         # 已公开耗材档案索引
│   └── activity.json        # 下载与收藏匿名统计快照
├── packages/                # 耗材档案分发包（ZIP）
└── luts/
    ├── catalog.json         # 已公开 LUT 预设索引
    ├── activity.json        # 下载与收藏匿名统计快照
    ├── packages/            # LUT 分发包（ZIP）
    └── previews/            # 色板与预览图
```

仓库根目录下的 `materials-src/`、`packages/`、`luts-src/`、`lut-packages/` 和 `seed/` 为早期源文件与历史构建记录，保留用于溯源；当前目录与离线打包均以 `public/v1/` 为准。

## 离线资源包

本仓库 [GitHub Releases](https://github.com/lumina-layer-studio/Lumina-materials/releases) 提供按版本打包的完整离线合集（`lumina-materials-seed.zip`、`lumina-luts-seed.zip` 与 `resource-release.json`），收录该版本全部已公开的官方与社区条目，方便离线浏览和按需导入。

如需在本地从 `public/v1/` 重新生成离线种子包，可运行：

```bash
python scripts/build_public_seeds.py \
  --public-dir public/v1 \
  --dataset-version 2026.11.18.1 \
  --output build/public-resources
```

构建脚本直接读取本地 `public/v1/` 快照，逐包核对 SHA-256 校验值与包内清单身份，原样保留原始分发 ZIP，并一并写入 [DATA-LICENSE.md](DATA-LICENSE.md)。

运行本地测试：

```bash
python -m unittest discover -s tests
```

## 数据使用协议

标记为 `LicenseRef-Lumina-Data-1.0` 的资源适用 [Lumina 数据使用说明与协议 1.0](DATA-LICENSE.md)：

- **允许的用途：** 下载、研究、修改并在个人或商业工作流中使用；承接付费代打、销售生成的模型或实体打印作品；在保留原作者、来源与协议声明的前提下免费分享原数据或修改版。
- **禁止的用途：** 售卖或转售数据文件与合集、收取下载费用，或以会员、订阅、积分、付费 API 等形式将本数据放入收费资源库。
- **既有许可：** 已按 CC BY 4.0 等协议发布的历史版本继续适用原协议。品牌名称、商标与 Logo 归各自权利人所有。

完整条款请查阅 [DATA-LICENSE.md](DATA-LICENSE.md)。
