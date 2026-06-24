<template>
  <main class="app-shell">
    <header class="app-header">
      <div class="brand-row">
        <div class="brand-mark">U</div>
        <div>
          <h1>Universal Problem Optimizer</h1>
          <p>通用问题优化智能体</p>
        </div>
      </div>
      <div class="header-status" :class="statusClass">
        <span class="status-dot" />
        {{ statusText }}
      </div>
    </header>

    <section class="workspace">
      <aside class="input-panel">
        <div class="panel-kicker">
          <div>
            <span class="eyebrow">New Request</span>
            <h2>问题工作区</h2>
          </div>
          <span class="panel-index">01</span>
        </div>

        <el-form label-position="top">
          <el-form-item label="原始问题">
            <el-input
              v-model="question"
              type="textarea"
              :autosize="{ minRows: 10, maxRows: 16 }"
              placeholder="请输入你想优化和求解的问题..."
            />
          </el-form-item>

          <el-form-item label="任务类型">
            <el-select v-model="taskType" class="full-width">
              <el-option v-for="item in taskTypes" :key="item" :label="item" :value="item" />
            </el-select>
          </el-form-item>

          <div class="action-row">
            <el-button type="primary" size="large" :loading="loading" @click="runAgent">
              <el-icon><MagicStick /></el-icon>
              开始优化
            </el-button>
            <el-button size="large" @click="loadSample">
              <el-icon><DocumentCopy /></el-icon>
              填入示例
            </el-button>
          </div>
        </el-form>

        <section class="log-panel">
          <div class="log-heading">
            <div class="panel-title">运行日志</div>
            <span class="log-count">{{ visibleLogs.length }}</span>
          </div>
          <el-timeline v-if="visibleLogs.length">
            <el-timeline-item
              v-for="(log, index) in visibleLogs"
              :key="`${index}-${log}`"
              :timestamp="`Step ${index + 1}`"
              placement="top"
            >
              {{ log }}
            </el-timeline-item>
          </el-timeline>
          <el-empty v-if="visibleLogs.length === 0" description="等待智能体运行" />
        </section>
      </aside>

      <section class="result-panel">
        <div class="result-header">
          <div>
            <span class="eyebrow">Final Workspace</span>
            <h2>{{ result ? '问题求解结果' : '等待新的问题' }}</h2>
          </div>
          <el-button
            v-if="result?.report_id"
            type="success"
            size="large"
            @click="downloadReport"
          >
            <el-icon><Download /></el-icon>
            下载 PDF 报告
          </el-button>
        </div>

        <el-alert
          v-if="error"
          class="alert"
          type="error"
          :title="error"
          show-icon
          :closable="false"
        />

        <div v-if="!result && !loading" class="empty-state">
          <div class="empty-symbol"><MagicStick /></div>
          <h3>准备开始</h3>
          <p>在左侧输入原始问题。</p>
        </div>

        <el-skeleton v-if="loading && !result" :rows="10" animated />

        <template v-if="result">
          <section class="process-section">
            <div class="process-heading">
              <div>
                <span class="eyebrow">Agent Trace</span>
                <h3>过程产物</h3>
              </div>
              <span class="compact-note">默认收起</span>
            </div>

            <el-collapse v-model="activeProcessSections" class="process-collapse">
              <el-collapse-item name="analysis">
                <template #title>
                  <div class="collapse-title">
                    <span class="collapse-badge">01</span>
                    <span>原始问题分析</span>
                    <small>问题诊断</small>
                  </div>
                </template>
                <div class="markdown-body" v-html="renderMarkdown(result.analysis)" />
              </el-collapse-item>

              <el-collapse-item name="prompt">
                <template #title>
                  <div class="collapse-title">
                    <span class="collapse-badge">02</span>
                    <span>问题优化版本</span>
                    <small>可复用提示词</small>
                  </div>
                </template>
                <div class="markdown-body" v-html="renderMarkdown(result.optimized_prompt)" />
              </el-collapse-item>
            </el-collapse>
          </section>

          <section class="output-section">
            <div class="deliverable-label"><el-icon><DocumentChecked /></el-icon> Final Deliverable</div>
            <h3>问题拆解步骤</h3>
            <div class="steps-grid">
              <article v-for="step in result.steps" :key="step.step" class="step-card">
                <span>{{ step.step }}</span>
                <h4>{{ step.title }}</h4>
                <p>{{ step.description }}</p>
              </article>
            </div>
          </section>

          <ResultSection title="推荐求解路径与最终答案" :content="result.solution" />
        </template>
      </section>
    </section>
  </main>
</template>

<script setup>
import { computed, defineComponent, h, ref } from 'vue'
import { marked } from 'marked'
import { ElMessage } from 'element-plus'
import { DocumentChecked, DocumentCopy, Download, MagicStick } from '@element-plus/icons-vue'
import { optimizeQuestion, reportUrl } from './api/agent'

const sampleQuestion = '我想写一份关于“多模态大模型在心理健康辅助诊断中的应用”的研究方案，但不知道怎么拆解研究背景、技术路线、创新点和实验设计，请帮我优化这个问题并给出完整解决方案。'

const question = ref(sampleQuestion)
const taskType = ref('科研类')
const loading = ref(false)
const result = ref(null)
const error = ref('')
const liveLogs = ref([])
const activeProcessSections = ref([])

const taskTypes = ['学习类', '代码类', '写作类', '规划类', '科研类', '通用类']
const visibleLogs = computed(() => result.value?.logs || liveLogs.value)
const statusText = computed(() => (loading.value ? '正在求解' : result.value ? '已完成' : '就绪'))
const statusClass = computed(() => (loading.value ? 'is-running' : result.value ? 'is-complete' : 'is-ready'))

function renderMarkdown(content) {
  return marked.parse(content || '')
}

const ResultSection = defineComponent({
  props: {
    title: { type: String, required: true },
    content: { type: String, required: true }
  },
  setup(props) {
    return () =>
      h('section', { class: 'output-section' }, [
        h('h3', props.title),
        h('div', {
          class: 'markdown-body',
          innerHTML: renderMarkdown(props.content)
        })
      ])
  }
})

function loadSample() {
  question.value = sampleQuestion
  taskType.value = '科研类'
}

async function runAgent() {
  if (!question.value.trim()) {
    ElMessage.warning('请先输入原始问题')
    return
  }

  loading.value = true
  error.value = ''
  result.value = null
  activeProcessSections.value = []
  liveLogs.value = [
    '正在分析问题：检查目标、条件、约束和输出格式。',
    '正在优化提示词：补充角色、任务目标、步骤和质量标准。',
    '正在调用工具：准备摘要、关键词和结构化输出。'
  ]

  try {
    const { data } = await optimizeQuestion({
      question: question.value,
      task_type: taskType.value
    })
    result.value = data
    ElMessage.success('智能体运行完成，PDF 报告已生成')
  } catch (err) {
    error.value = err?.response?.data?.detail || err.message || '请求失败，请检查后端服务。'
  } finally {
    loading.value = false
  }
}

function downloadReport() {
  window.open(reportUrl(result.value.report_id), '_blank')
}
</script>
