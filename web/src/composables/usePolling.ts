import { onBeforeUnmount } from 'vue'

export function usePolling(task: () => void | Promise<void>, delay = 30000) {
  let timer: number | null = null

  function start() {
    stop()
    timer = window.setInterval(() => {
      void task()
    }, delay)
  }

  function stop() {
    if (timer !== null) {
      window.clearInterval(timer)
      timer = null
    }
  }

  onBeforeUnmount(() => {
    stop()
  })

  return {
    start,
    stop,
  }
}
