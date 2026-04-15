<template>
  <button class="app-button" :class="[`app-button--${variant}`]" :disabled="disabled">
    <slot />
  </button>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    variant?: "primary" | "secondary" | "danger";
    disabled?: boolean;
  }>(),
  {
    variant: "primary",
    disabled: false,
  }
);
</script>

<style lang="scss" scoped>
.app-button {
  padding: 0.5rem 1.25rem;
  border: none;
  border-radius: $radius-md;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;

  &--primary {
    background-color: $color-primary;
    color: #fff;
    &:hover { background-color: darken($color-primary, 8%); }
  }

  &--secondary {
    background-color: $color-secondary;
    color: #fff;
    &:hover { background-color: darken($color-secondary, 8%); }
  }

  &--danger {
    background-color: $color-danger;
    color: #fff;
    &:hover { background-color: darken($color-danger, 8%); }
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
}
</style>
