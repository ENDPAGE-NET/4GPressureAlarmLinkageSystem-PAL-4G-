<template>
  <div ref="chartRef" class="chart-box" />
</template>

<script setup lang="ts">
import * as echarts from 'echarts'
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'

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

function renderChart() {
  if (!chartRef.value) {
    return
  }

  if (!chart) {
    chart = echarts.init(chartRef.value)
  }

  chart.setOption({
    tooltip: {
      trigger: 'item',
    },
    color: props.color,
    legend: {
      bottom: 0,
      textStyle: {
        color: '#8faab6',
      },
    },
    series: [
      {
        name: props.seriesName,
        type: 'pie',
        radius: ['45%', '72%'],
        center: ['50%', '44%'],
        itemStyle: {
          borderRadius: 12,
          borderColor: '#081a22',
          borderWidth: 4,
        },
        label: {
          color: '#d7e2e9',
          formatter: '{b}\n{c}',
        },
        data: props.data.length
          ? props.data.map((item) => ({
              value: item.value,
              name: item.label,
            }))
          : [{ value: 1, name: t('common.noChartData'), itemStyle: { color: '#31505c' } }],
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
