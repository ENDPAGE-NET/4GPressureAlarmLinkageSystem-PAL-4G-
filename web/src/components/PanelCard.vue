<template>
  <section class="panel-card">
    <div class="panel-card__inner">
      <header v-if="title || description || $slots.header" class="panel-card__head">
        <div>
          <h3 v-if="title" class="panel-card__title">{{ title }}</h3>
          <p v-if="description" class="panel-card__description">{{ description }}</p>
        </div>
        <slot name="header" />
      </header>

      <slot />
    </div>
  </section>
</template>

<script setup lang="ts">
defineProps<{
  title?: string
  description?: string
}>()
</script>
