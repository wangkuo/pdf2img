<script setup lang="ts">
import { ref } from 'vue';
import { message, Upload, InputNumber, Button, Card } from 'ant-design-vue';
import { InboxOutlined } from '@ant-design/icons-vue';
import type { UploadProps } from 'ant-design-vue';
import * as pdfjsLib from 'pdfjs-dist';

// 初始化 PDF.js worker
pdfjsLib.GlobalWorkerOptions.workerSrc = new URL('pdfjs-dist/build/pdf.worker.min.mjs', import.meta.url).href;

// 配置CMap
const cMapUrl = '/node_modules/pdfjs-dist/cmaps/';
const cMapPacked = true;

// 状态管理
const pdfFiles = ref<File[]>([]);
const previewVisible = ref(false);
const currentPreviewPage = ref(1);
const totalPages = ref(0);
const scale = ref(2.5);
const converting = ref(false);
const previewCanvas = ref<HTMLCanvasElement | null>(null);
const currentPdfIndex = ref(0);

// 文件上传配置
const uploadProps: UploadProps = {
  accept: '.pdf',
  multiple: true,
  fileList: [],
  beforeUpload: (file) => {
    pdfFiles.value.push(file);
    // 自动预览最新上传的文件
    const fileIndex = pdfFiles.value.length - 1;
    previewPdf(fileIndex);
    return false;
  }
};

// 处理文件移除事件
const handleRemove = (file: any) => {
  const index = pdfFiles.value.findIndex(f => f.name === file.name);
  if (index > -1) {
    pdfFiles.value.splice(index, 1);
    // 如果还有文件，预览最后一个文件
    if (pdfFiles.value.length > 0) {
      previewPdf(pdfFiles.value.length - 1);
    } else {
      previewVisible.value = false;
    }
  }
};

// 预览PDF
async function previewPdf(fileIndex: number = 0, pageNum: number = 1) {
  if (!pdfFiles.value[fileIndex]) return;
  
  try {
    const arrayBuffer = await pdfFiles.value[fileIndex].arrayBuffer();
    const pdf = await pdfjsLib.getDocument({
      data: arrayBuffer,
      cMapUrl,
      cMapPacked
    }).promise;
    totalPages.value = pdf.numPages;
    currentPdfIndex.value = fileIndex;
    currentPreviewPage.value = pageNum;

    const page = await pdf.getPage(pageNum);
    const viewport = page.getViewport({ scale: scale.value });

    if (!previewCanvas.value) return;
    const canvas = previewCanvas.value;
    const context = canvas.getContext('2d');
    if (!context) return;

    canvas.height = viewport.height;
    canvas.width = viewport.width;

    await page.render({
      canvasContext: context,
      viewport: viewport
    }).promise;

    previewVisible.value = true;
  } catch (error) {
    message.error('预览PDF时发生错误');
    console.error(error);
  }
}

// 转换PDF为图片
async function convertPdfToImages() {
  if (pdfFiles.value.length === 0) {
    message.warning('请先上传PDF文件');
    return;
  }

  converting.value = true;
  try {
    for (let fileIndex = 0; fileIndex < pdfFiles.value.length; fileIndex++) {
      const file = pdfFiles.value[fileIndex];
      const arrayBuffer = await file.arrayBuffer();
      const pdf = await pdfjsLib.getDocument({
        data: arrayBuffer,
        cMapUrl,
        cMapPacked
      }).promise;

      for (let pageNum = 1; pageNum <= pdf.numPages; pageNum++) {
        const page = await pdf.getPage(pageNum);
        const viewport = page.getViewport({ scale: scale.value });

        const canvas = document.createElement('canvas');
        const context = canvas.getContext('2d');
        if (!context) continue;

        canvas.height = viewport.height;
        canvas.width = viewport.width;

        await page.render({
          canvasContext: context,
          viewport: viewport
        }).promise;

        // 转换为图片并下载
        const image = canvas.toDataURL('image/png');
        const link = document.createElement('a');
        link.href = image;
        // 如果PDF只有一页，则不添加页码到文件名
        const fileName = pdf.numPages === 1
          ? `${file.name.replace(/\.pdf$/i, '')}.png`
          : `${file.name.replace(/\.pdf$/i, '')}_page${pageNum}.png`;
        link.download = fileName;
        link.click();
      }
    }
    message.success('转换完成');
  } catch (error) {
    message.error('转换过程中发生错误');
    console.error(error);
  } finally {
    converting.value = false;
  }
}
</script>

<template>
  <div class="pdf-converter">
    <Card title="PDF转图片工具" class="converter-card">
      <div class="upload-section">
        <Upload v-bind="uploadProps" class="uploader" @remove="handleRemove">
          <div class="upload-drag-area">
            <p class="upload-drag-icon">
              <InboxOutlined />
            </p>
            <p class="upload-text">点击或拖拽PDF文件到此区域</p>
            <p class="upload-hint">支持单个或多个PDF文件</p>
          </div>
        </Upload>
        <div class="scale-setting">
          <span>缩放比例：</span>
          <InputNumber
            v-model:value="scale"
            :min="0.1"
            :max="3"
            :step="0.1"
            style="width: 100px"
            @change="() => pdfFiles.length > 0 && previewPdf(currentPdfIndex, currentPreviewPage)"
          />
        </div>
      </div>

      <div class="file-list" v-if="pdfFiles.length > 0">
        <div v-for="(file, index) in pdfFiles" :key="file.name" 
          class="file-item"
          :class="{ 'active': index === currentPdfIndex }"
          @click="previewPdf(index, 1)"
        >
          <span>{{ file.name }}</span>
          <span>{{ index === currentPdfIndex ? '预览中' : '' }}</span>
        </div>
      </div>

      <div class="preview-section" v-if="pdfFiles.length > 0">
        <div class="preview-container">
          <canvas ref="previewCanvas"></canvas>
          <div class="preview-controls">
            <Button
              :disabled="currentPreviewPage === 1"
              @click="previewPdf(currentPdfIndex, currentPreviewPage - 1)"
            >
              上一页
            </Button>
            <span>{{ currentPreviewPage }} / {{ totalPages }}</span>
            <Button
              :disabled="currentPreviewPage === totalPages"
              @click="previewPdf(currentPdfIndex, currentPreviewPage + 1)"
            >
              下一页
            </Button>
          </div>
        </div>
      </div>

      <div class="action-buttons">
        <Button
          type="primary"
          :loading="converting"
          @click="convertPdfToImages"
          :disabled="pdfFiles.length === 0"
        >
          {{ converting ? '转换中...' : '开始转换' }}
        </Button>
      </div>
    </Card>
  </div>
</template>

<style scoped>
.pdf-converter {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
}

.converter-card {
  margin-bottom: 20px;
  min-width: 400px;
}

.upload-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
  margin-bottom: 20px;
}

.uploader {
  width: 100%;
  max-width: 600px;
}

.upload-drag-area {
  padding: 32px;
  background: #fafafa;
  border: 1px dashed #d9d9d9;
  border-radius: 8px;
  text-align: center;
  transition: border-color 0.3s;
  cursor: pointer;
}

.upload-drag-area:hover {
  border-color: #1890ff;
}

.upload-drag-icon {
  margin-bottom: 16px;
  font-size: 48px;
  color: #40a9ff;
}

.upload-text {
  margin: 0 0 8px;
  color: rgba(0, 0, 0, 0.85);
  font-size: 16px;
}

.upload-hint {
  color: rgba(0, 0, 0, 0.45);
  font-size: 14px;
}

.scale-setting {
  display: flex;
  align-items: center;
  gap: 10px;
}

.file-list {
  margin: 20px 0;
}

.file-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px;
  border-bottom: 1px solid #f0f0f0;
}

.action-buttons {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

.preview-section {
  margin: 20px 0;
  border: 1px solid #f0f0f0;
  padding: 20px;
  border-radius: 8px;
  max-height: 800px;
  overflow: auto;
}

.preview-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
  max-width: 100%;
}

.preview-container canvas {
  max-width: 100%;
  height: auto;
}

.preview-controls {
  display: flex;
  gap: 20px;
  align-items: center;
}

.file-item {
  cursor: pointer;
  transition: background-color 0.3s;
}

.file-item:hover {
  background-color: #f5f5f5;
}

.file-item.active {
  background-color: #e6f7ff;
}
</style>