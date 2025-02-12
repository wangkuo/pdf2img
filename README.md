# PDF转图片工具

一个基于Vue 3的PDF转图片工具，支持PDF文件预览和批量转换为PNG图片格式。

## 主要功能

- 支持单个或多个PDF文件上传
- PDF文件实时预览功能
- 支持多页PDF文档的页面切换
- 可自定义输出图片的缩放比例（0.1-3倍）
- 批量转换PDF为PNG图片
- 自动文件命名（单页PDF直接使用原文件名，多页PDF自动添加页码）

## 技术栈

- Vue 3
- TypeScript
- Vite
- PDF.js - PDF渲染引擎
- Ant Design Vue - UI组件库

## 安装

```bash
# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build
```

## 使用说明

1. 点击「选择PDF文件」按钮上传一个或多个PDF文件
2. 上传后可以在预览区查看PDF内容
3. 使用预览区域下方的按钮切换PDF页面
4. 通过缩放比例设置调整输出图片的大小
5. 点击「开始转换」按钮将PDF转换为PNG图片
6. 转换完成后图片会自动下载到本地

## 注意事项

- 支持的文件格式：PDF
- 输出格式：PNG
- 建议的浏览器：Chrome、Firefox、Safari最新版本
- 文件大小：建议单个PDF文件不超过50MB
- 转换过程中请勿关闭浏览器窗口
