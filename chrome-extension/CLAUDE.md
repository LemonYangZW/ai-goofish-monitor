[根目录](../CLAUDE.md) > **chrome-extension**

# chrome-extension - 登录态提取扩展

## 模块职责

Chrome/Edge 浏览器扩展，用于从闲鱼（goofish.com）网站提取登录态（cookies + 浏览器环境信息），供爬虫使用。

## 入口与启动

- `background.js` - Service Worker 后台脚本
- `popup.html` + `popup.js` - 扩展弹窗界面
- `manifest.json` - 扩展清单（Manifest V3）

安装方式：Chrome 开发者模式加载此目录即可。

## 对外接口

- 提取的登录态以 JSON 格式导出，保存为 `state.json` 文件
- 爬虫通过 `STATE_FILE` 环境变量指定该文件路径

## 关键依赖与配置

- Manifest V3
- 权限：`activeTab`, `cookies`, `scripting`, `storage`, `tabs`, `webRequest`
- Host 权限：`*://*.goofish.com/*`

## 测试与质量

- 无自动化测试，需手动验证

## 相关文件清单

```
chrome-extension/
├── manifest.json       # 扩展清单
├── background.js       # Service Worker
├── popup.html          # 弹窗 HTML
├── popup.js            # 弹窗逻辑
└── README.md           # 使用说明
```
