<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import dayjs from 'dayjs'
import { message } from 'ant-design-vue'

import { generateTripPlan } from '@/services/api'
import type { TripPlanRequest } from '@/types'

const router = useRouter()
const loading = ref(false)

const formData = ref<TripPlanRequest>({
  city: '',
  start_date: '',
  end_date: '',
  days: 3,
  preferences: '\u5386\u53f2\u6587\u5316',
  budget: '\u4e2d\u7b49',
  transportation: '\u516c\u5171\u4ea4\u901a',
  accommodation: '\u7ecf\u6d4e\u578b\u9152\u5e97',
  pace_preference: '\u5e73\u8861',
  safety_preference: '\u7a33\u59a5\u4f18\u5148',
  night_preference: '\u65e9\u5f52\u4f11\u606f'
})

const recalcDays = () => {
  if (!formData.value.start_date || !formData.value.end_date) return
  const start = dayjs(formData.value.start_date)
  const end = dayjs(formData.value.end_date)
  const diff = end.diff(start, 'day') + 1
  formData.value.days = Math.max(1, diff)
}

const travelWindow = computed(() => {
  if (!formData.value.start_date || !formData.value.end_date) return '\u5c1a\u672a\u9009\u62e9\u65e5\u671f'
  return `${formData.value.start_date} ~ ${formData.value.end_date}`
})

const handleSubmit = async () => {
  if (!formData.value.city.trim()) {
    message.error('\u8bf7\u8f93\u5165\u76ee\u7684\u5730\u57ce\u5e02')
    return
  }

  if (!formData.value.start_date || !formData.value.end_date) {
    message.error('\u8bf7\u9009\u62e9\u5f00\u59cb\u548c\u7ed3\u675f\u65e5\u671f')
    return
  }

  recalcDays()
  if (formData.value.days > 14) {
    message.error('\u884c\u7a0b\u5929\u6570\u4e0d\u80fd\u8d85\u8fc7 14 \u5929')
    return
  }

  loading.value = true
  try {
    const tripPlan = await generateTripPlan(formData.value)
    sessionStorage.setItem('tripPlan', JSON.stringify(tripPlan))
    await router.push({ name: 'result' })
  } catch (error: any) {
    message.error(error?.message || '\u751f\u6210\u884c\u7a0b\u5931\u8d25\uff0c\u8bf7\u7a0d\u540e\u91cd\u8bd5')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="park-page home-page">
    <div class="park-topbar">
      <div class="park-brand">
        <span class="park-brand__dot"></span>
        <span class="park-brand__text">SoloPark</span>
      </div>
      <div class="park-badge">
        <span class="park-badge__icon"></span>
        <span>{{ formData.days }}/14</span>
      </div>
    </div>

    <section class="park-card hero-card">
      <div class="hero-card__grid">
        <div class="hero-card__copy">
          <div class="hero-card__eyebrow">Selected Journey</div>
          <h1 class="hero-card__title">&#x72EC;&#x81EA;&#x65C5;&#x884C;&#x5DE5;&#x4F5C;&#x53F0;</h1>
          <p class="hero-card__subtitle">
            &#x7528;&#x66F4;&#x7A33;&#x5B9A;&#x7684;&#x8282;&#x594F;&#x3001;&#x9884;&#x7B97;&#x548C;&#x591C;&#x95F4;&#x5B89;&#x6392;&#xFF0C;&#x5FEB;&#x901F;&#x751F;&#x6210;&#x4E00;&#x4EFD;&#x53EF;&#x6267;&#x884C;&#x7684;&#x72EC;&#x81EA;&#x65C5;&#x884C;&#x65B9;&#x6848;&#x3002;
          </p>
          <div class="hero-card__facts">
            <div>
              <span class="hero-card__label">Window</span>
              <strong>{{ travelWindow }}</strong>
            </div>
            <div>
              <span class="hero-card__label">Pace</span>
              <strong>{{ formData.pace_preference }}</strong>
            </div>
            <div>
              <span class="hero-card__label">Night</span>
              <strong>{{ formData.night_preference }}</strong>
            </div>
          </div>
        </div>

        <div class="hero-card__badge">
          <div class="hero-card__orb">
            <span>&#x25CF;</span>
          </div>
        </div>
      </div>

      <div class="hero-card__cta-row">
        <button class="park-pill-button" type="button" @click="handleSubmit" :disabled="loading">
          {{ loading ? '&#x751F;&#x6210;&#x4E2D;...' : '&#x751F;&#x6210;&#x72EC;&#x81EA;&#x65C5;&#x884C;&#x884C;&#x7A0B;' }}
        </button>
      </div>
    </section>

    <section class="park-card form-shell">
      <div class="park-section-title">
        <span class="park-section-title__text">Expedition Setup</span>
      </div>

      <a-form layout="vertical" class="home-form">
        <a-form-item label="&#x76EE;&#x7684;&#x5730;&#x57CE;&#x5E02;" required>
          <a-input v-model:value="formData.city" placeholder="&#x4F8B;&#x5982;&#xFF1A;&#x676D;&#x5DDE; / &#x6210;&#x90FD; / &#x6B66;&#x6C49;" />
        </a-form-item>

        <a-row :gutter="16">
          <a-col :xs="24" :md="12">
            <a-form-item label="&#x5F00;&#x59CB;&#x65E5;&#x671F;" required>
              <a-input v-model:value="formData.start_date" type="date" @change="recalcDays" />
            </a-form-item>
          </a-col>
          <a-col :xs="24" :md="12">
            <a-form-item label="&#x7ED3;&#x675F;&#x65E5;&#x671F;" required>
              <a-input v-model:value="formData.end_date" type="date" @change="recalcDays" />
            </a-form-item>
          </a-col>
        </a-row>

        <a-row :gutter="16">
          <a-col :xs="24" :md="12">
            <a-form-item label="&#x884C;&#x7A0B;&#x5929;&#x6570;">
              <a-input-number v-model:value="formData.days" :min="1" :max="14" disabled />
            </a-form-item>
          </a-col>
          <a-col :xs="24" :md="12">
            <a-form-item label="&#x9884;&#x7B97;&#x7B49;&#x7EA7;">
              <a-select v-model:value="formData.budget" :options="[
                { label: '&#x7ECF;&#x6D4E;', value: '\u7ecf\u6d4e' },
                { label: '&#x4E2D;&#x7B49;', value: '\u4e2d\u7b49' },
                { label: '&#x8C6A;&#x534E;', value: '\u8c6a\u534e' }
              ]" />
            </a-form-item>
          </a-col>
        </a-row>

        <a-row :gutter="16">
          <a-col :xs="24" :md="12">
            <a-form-item label="&#x51FA;&#x884C;&#x65B9;&#x5F0F;">
              <a-select v-model:value="formData.transportation" :options="[
                { label: '&#x516C;&#x5171;&#x4EA4;&#x901A;', value: '\u516c\u5171\u4ea4\u901a' },
                { label: '&#x6253;&#x8F66;', value: '\u6253\u8f66' },
                { label: '&#x81EA;&#x9A7E;', value: '\u81ea\u9a7e' }
              ]" />
            </a-form-item>
          </a-col>
          <a-col :xs="24" :md="12">
            <a-form-item label="&#x4F4F;&#x5BBF;&#x504F;&#x597D;">
              <a-select v-model:value="formData.accommodation" :options="[
                { label: '&#x7ECF;&#x6D4E;&#x578B;&#x9152;&#x5E97;', value: '\u7ecf\u6d4e\u578b\u9152\u5e97' },
                { label: '&#x5546;&#x52A1;&#x9152;&#x5E97;', value: '\u5546\u52a1\u9152\u5e97' },
                { label: '&#x7CBE;&#x54C1;&#x9152;&#x5E97;', value: '\u7cbe\u54c1\u9152\u5e97' },
                { label: '&#x6C11;&#x5BBF;', value: '\u6c11\u5bbf' }
              ]" />
            </a-form-item>
          </a-col>
        </a-row>

        <a-row :gutter="16">
          <a-col :xs="24" :md="8">
            <a-form-item label="&#x884C;&#x7A0B;&#x8282;&#x594F;">
              <a-select v-model:value="formData.pace_preference" :options="[
                { label: '&#x8F7B;&#x677E;', value: '\u8f7b\u677e' },
                { label: '&#x5E73;&#x8861;', value: '\u5e73\u8861' },
                { label: '&#x7D27;&#x51D1;', value: '\u7d27\u51d1' }
              ]" />
            </a-form-item>
          </a-col>
          <a-col :xs="24" :md="8">
            <a-form-item label="&#x5B89;&#x5168;&#x504F;&#x597D;">
              <a-select v-model:value="formData.safety_preference" :options="[
                { label: '&#x7A33;&#x59A5;&#x4F18;&#x5148;', value: '\u7a33\u59a5\u4f18\u5148' },
                { label: '&#x5E38;&#x89C4;&#x5373;&#x53EF;', value: '\u5e38\u89c4\u5373\u53ef' },
                { label: '&#x613F;&#x610F;&#x591C;&#x95F4;&#x6D3B;&#x52A8;', value: '\u613f\u610f\u591c\u95f4\u6d3b\u52a8' }
              ]" />
            </a-form-item>
          </a-col>
          <a-col :xs="24" :md="8">
            <a-form-item label="&#x591C;&#x95F4;&#x5B89;&#x6392;">
              <a-select v-model:value="formData.night_preference" :options="[
                { label: '&#x65E9;&#x5F52;&#x4F11;&#x606F;', value: '\u65e9\u5f52\u4f11\u606f' },
                { label: '&#x9002;&#x5EA6;&#x591C;&#x6E38;', value: '\u9002\u5ea6\u591c\u6e38' },
                { label: '&#x591C;&#x751F;&#x6D3B;&#x4F53;&#x9A8C;', value: '\u591c\u751f\u6d3b\u4f53\u9a8c' }
              ]" />
            </a-form-item>
          </a-col>
        </a-row>
      </a-form>
    </section>
  </div>
</template>

<style scoped>
.home-page { display: flex; flex-direction: column; gap: 22px; }
.hero-card__grid { display: grid; grid-template-columns: 1fr 112px; gap: 22px; align-items: center; }
.hero-card__eyebrow { margin-bottom: 16px; color: var(--park-green-soft); font-size: 0.95rem; font-weight: 800; letter-spacing: 0.18em; text-transform: uppercase; }
.hero-card__title { margin: 0; font-family: var(--park-serif); font-size: clamp(2.6rem, 5vw, 4rem); line-height: 0.98; letter-spacing: -0.05em; }
.hero-card__subtitle { max-width: 640px; margin: 18px 0 24px; color: var(--park-muted); font-size: 1.02rem; line-height: 1.75; }
.hero-card__facts { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 18px; padding-top: 18px; border-top: 2px dashed rgba(154, 182, 148, 0.34); }
.hero-card__facts strong { display: block; margin-top: 8px; font-family: var(--park-serif); font-size: 1.55rem; font-weight: 700; }
.hero-card__label { color: var(--park-green-soft); font-size: 0.84rem; font-weight: 800; letter-spacing: 0.14em; text-transform: uppercase; }
.hero-card__badge { display: flex; justify-content: center; }
.hero-card__orb { display: grid; place-items: center; width: 78px; height: 78px; border-radius: 999px; background: linear-gradient(180deg, rgba(250, 244, 232, 0.8), rgba(237, 225, 205, 0.92)); box-shadow: inset 0 0 0 8px rgba(249, 242, 230, 0.8), 0 10px 28px rgba(104, 128, 98, 0.18); }
.hero-card__orb span { display: grid; place-items: center; width: 44px; height: 44px; border-radius: 999px; background: radial-gradient(circle at 30% 30%, #56a26f, #2f7f5f 48%, #e7c76d 78%, #4c81a8 100%); color: transparent; }
.hero-card__cta-row { margin-top: 28px; }
.hero-card__cta-row .park-pill-button { width: min(520px, 100%); }
.home-form :deep(.ant-input-number-input) { height: 52px; }
@media (max-width: 768px) {
  .hero-card__grid { grid-template-columns: 1fr; }
  .hero-card__badge { justify-content: flex-start; }
  .hero-card__facts { grid-template-columns: 1fr; }
}
</style>
