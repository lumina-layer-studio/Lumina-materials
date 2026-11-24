# Lumina Materials

[English](README.md) · [简体中文](README_CN.md) · [目录结构](#目录结构) · [离线资源包](#离线资源包) · [数据使用协议](#数据使用协议) · [Lumina Studio](https://github.com/lumina-layer-studio/Lumina-Layers)

[Lumina Studio](https://github.com/lumina-layer-studio/Lumina-Layers) 的公开耗材校准档案与 LUT 预设仓库。

当前目录位于 `public/v1/`。在 Lumina Studio 材料库中可直接预览并按需下载耗材档案与固定色卡 LUT，无需登录 GitHub 账号；导入本机材料库后即可离线配色。

固定色卡与梯度色卡的打印、拍照和取色步骤见 [Lumina Studio Wiki](https://wiki.luminastudio.com.cn/)。

## 收录内容

- 涵盖官方校准、社区投稿以及厂商供稿的耗材档案与 LUT 预设。
- 每条资源保留原作者、供稿来源、原始文件名、资源 ID、修订版本及发布频道（`official` 或 `community`）。
- `activity.json` 记录下载、点赞与收藏的匿名统计快照。

## 目录结构

```text
public/v1/
├── DATA-LICENSE.md          # Lumina 数据使用说明与协议 1.0（中英双语）
├── materials/
│   ├── catalog.json         # 耗材档案索引
│   └── activity.json        # 下载与收藏匿名统计快照
├── packages/                # 耗材档案分发包（ZIP）
└── luts/
    ├── catalog.json         # LUT 预设索引
    ├── activity.json        # 下载与收藏匿名统计快照
    ├── packages/            # LUT 分发包（ZIP）
    └── previews/            # 色板与预览图
```

## 离线资源包

[GitHub Releases](https://github.com/lumina-layer-studio/Lumina-materials/releases) 提供按版本打包的离线合集（`lumina-materials-seed.zip`、`lumina-luts-seed.zip` 与 `resource-release.json`），方便离线浏览和按需导入。

从本地 `public/v1/` 生成离线种子包：

```bash
python scripts/build_public_seeds.py \
  --public-dir public/v1 \
  --dataset-version 2026.11.18.1 \
  --output build/public-resources
```

脚本会在本地核对各包 SHA-256 与清单信息，并将原始分发 ZIP 连同 [DATA-LICENSE.md](DATA-LICENSE.md) 一起打包。运行 `python -m unittest discover -s tests` 可执行本地测试。

## 数据使用协议

标记为 `LicenseRef-Lumina-Data-1.0` 的资源适用 [Lumina 数据使用说明与协议 1.0](DATA-LICENSE.md)：

- **允许：** 下载、修改并在个人或商业打印流程中使用；承接付费代打、销售生成模型或实体打印件；保留原作者、来源与协议声明后免费分享。
- **禁止：** 售卖或转售数据文件与合集、收取下载费，或通过会员、订阅、积分、付费 API 等形式放入收费资源库。
- **既有许可：** 已按 CC BY 4.0 等协议发布的历史资源继续适用原协议。品牌名称、商标与 Logo 归各自权利人所有。

完整条款见 [DATA-LICENSE.md](DATA-LICENSE.md)。
