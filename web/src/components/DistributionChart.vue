<template>
  <div ref="chartRef" class="chart-box" />
</template>

<script setup lang="ts">
import * as echarts from 'echarts'
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'

import { useI18n } from '@/composables/useI18n'
import type { DashboardTrendPoint } from '@/types/domain'

const props = defineProps<{
  data: DashboardTrendPoint[]
  seriesName: string
  color: string[]
}>()

const chartRef = ref<HTMLDivElement>()
let chart: echarts.ECharts | null = null
let resizeObserver: ResizeObserver | null = null
const { t } = useI18n()

const translatedData = computed(() =>
  props.data.map((item) => ({
    value: item.value,
    name: translateLabel(item.label),
  })),
)

function readCssVar(name: string, fallback: string) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim() || fallback
}

function translateLabel(label: string) {
  const normalized = label.trim().toLowerCase()
  const labelMap: Record<string, string> = {
    low_battery: 'alarms.types.low_battery',
    low_voltage: 'alarms.types.low_voltage',
    high_voltage: 'alarms.types.high_voltage',
    disconnect: 'alarms.types.disconnect',
    pressure_abnormal: 'alarms.types.pressure_abnormal',
    queued: 'status.command.queued',
    pending: 'status.command.pending',
    dispatched: 'status.command.dispatched',
    success: 'status.command.success',
    failed: 'status.command.failed',
    active: 'status.device.active',
    inactive: 'status.device.inactive',
    other: 'status.device.other',
    all_online: 'status.device.all_online',
    all_offline: 'status.device.all_offline',
    part_online: 'status.device.part_online',
    no_modules: 'status.device.no_modules',
  }

  const labelKey = labelMap[normalized]
  if (!labelKey) {
    return label
  }

  const translated = t(labelKey)
  return translated === labelKey ? label : translated
}

function renderChart() {
  if (!chartRef.value) {
    return
  }

  if (!chart) {
    chart = echarts.init(chartRef.value)
  }

  const textColor = readCssVar('--pal-text', '#12303b')
  const mutedTextColor = readCssVar('--pal-text-muted', '#4a6570')
  const panelLineColor = readCssVar('--pal-panel-border', 'rgba(16, 55, 74, 0.12)')
  const emptyColor = readCssVar('--pal-text-faint', '#6b8590')
  const chartData = translatedData.value.length
    ? translatedData.value
    : [{ value: 1, name: t('common.noChartData'), itemStyle: { color: emptyColor } }]

  chart.setOption({
    tooltip: {
      trigger: 'item',
      borderColor: panelLineColor,
      backgroundColor: readCssVar('--pal-panel', 'rgba(255, 255, 255, 0.94)'),
      textStyle: {
        color: textColor,
      },
      formatter: (params: { name: string; value: number; percent: number }) =>
        `${props.seriesName}<br/>${params.name} : ${params.value} (${params.percent}%)`,
    },
    color: props.color,
    legend: {
      bottom: 0,
      icon: 'roundRect',
      itemWidth: 18,
      itemHeight: 10,
      textStyle: {
        color: mutedTextColor,
        fontSize: 13,
      },
      formatter: (name: string) => name,
    },
    series: [
      {
        name: props.seriesName,
        type: 'pie',
        radius: '76%',
        center: ['50%', '42%'],
        avoidLabelOverlap: true,
        itemStyle: {
          borderRadius: 6,
          borderColor: readCssVar('--pal-panel', '#ffffff'),
          borderWidth: 2,
          shadowBlur: 18,
          shadowOffsetY: 6,
          shadowColor: 'rgba(12, 34, 46, 0.16)',
        },
        padAngle: 0,
        minAngle: 5,
        selectedMode: false,
        emphasis: {
          scale: true,
          scaleSize: 10,
        },
        label: {
          color: textColor,
          formatter: '{b}\n{c}',
          fontSize: 14,
          fontWeight: 600,
          lineHeight: 18,
        },
        labelLine: {
          length: 16,
          length2: 14,
          lineStyle: {
            color: mutedTextColor,
            width: 1.5,
          },
        },
        data: chartData,
      },
    ],
  })
}

onMounted(() => {
  renderChart()
  if (chartRef.value) {
    resizeObserver = new ResizeObserver(() => chart?.resize())
    resizeObserver.observe(chartRef.value)
  }
})

watch(() => [props.data, props.seriesName, props.color], renderChart, { deep: true })

onBeforeUnmount(() => {
  resizeObserver?.disconnect()
  chart?.dispose()
  chart = null
})
</script>
