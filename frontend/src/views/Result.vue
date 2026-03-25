<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import type { Attraction, TransportLeg, TripPlan, WeatherInfo } from '@/types'

const router = useRouter()
const tripPlan = ref<TripPlan | null>(null)

const weatherByDate = computed(() => {
  const map = new Map<string, WeatherInfo>()
  for (const weather of tripPlan.value?.weather_info || []) map.set(weather.date, weather)
  return map
})

const formatWeather = (weather?: WeatherInfo) => {
  if (!weather) return ''
  return `${weather.day_weather} ${weather.day_temp}\u2103 / ${weather.night_weather} ${weather.night_temp}\u2103`
}

const formatDistance = (distanceMeters?: number) => {
  if (!distanceMeters) return ''
  return distanceMeters >= 1000 ? `${(distanceMeters / 1000).toFixed(1)} km` : `${distanceMeters} m`
}

const formatTransportSummary = (leg: TransportLeg) => {
  const parts = [leg.summary, `${leg.duration_minutes} 分钟`]
  const distance = formatDistance(leg.distance_meters)
  if (distance) parts.push(distance)
  if (leg.estimated_cost !== undefined && leg.estimated_cost !== null) parts.push(`约 ${leg.estimated_cost} 元`)
  return parts.join(' · ')
}

const isBadWeather = (weather?: WeatherInfo) => {
  if (!weather) return false
  return /\u96e8|\u96f7|\u96ea|\u66b4/.test((weather.day_weather || '') + (weather.night_weather || ''))
}

const isIndoorAttraction = (attraction: Attraction) => {
  return /\u535a\u7269\u9986|\u7f8e\u672f\u9986|\u827a\u672f\u9986|\u5c55\u89c8|\u4e66\u5e97|\u5546\u573a|\u5ba4\u5185/.test(
    (attraction.name || '') + (attraction.category || '') + (attraction.description || '')
  )
}

const getAttractionTags = (attraction: Attraction, date: string) => {
  const tags: string[] = []
  const weather = weatherByDate.value.get(date)
  if (isIndoorAttraction(attraction)) tags.push('\u5ba4\u5185\u4f18\u5148')
  if (isBadWeather(weather) && isIndoorAttraction(attraction)) tags.push('\u96e8\u5929\u53cb\u597d')
  if (tripPlan.value?.night_preference === '\u591c\u751f\u6d3b\u4f53\u9a8c' && /\u591c|\u706f|\u5e02\u96c6|\u8857\u533a/.test(attraction.name)) tags.push('\u591c\u95f4\u53ef\u53bb')
  if (tripPlan.value?.safety_preference === '\u7a33\u59a5\u4f18\u5148' && /\u5e02\u533a|\u4e2d\u5fc3|\u535a\u7269\u9986|\u4e66\u5e97/.test((attraction.description || '') + (attraction.address || ''))) tags.push('\u8fd4\u7a0b\u66f4\u7a33\u59a5')
  return tags.slice(0, 3)
}

const getDayAdjustments = (date: string) => {
  if (!tripPlan.value) return []
  const tips: string[] = []
  const weather = weatherByDate.value.get(date)
  const weatherText = (weather?.day_weather || '') + (weather?.night_weather || '')
  if (weather && /\u96e8|\u96f7|\u96ea|\u66b4/.test(weatherText)) {
    tips.push('\u4eca\u65e5\u5929\u6c14\u6ce2\u52a8\u8f83\u5927\uff0c\u4f18\u5148\u5ba4\u5185\u666f\u70b9\u6216\u7f29\u77ed\u6237\u5916\u505c\u7559\u65f6\u95f4\u3002')
    tips.push('\u5efa\u8bae\u968f\u8eab\u643a\u5e26\u96e8\u5177\uff0c\u5e76\u63d0\u524d\u786e\u8ba4\u8fd4\u7a0b\u8def\u7ebf\u6216\u6253\u8f66\u70b9\u4f4d\u3002')
  }
  if (tripPlan.value.night_preference === '\u591c\u751f\u6d3b\u4f53\u9a8c') {
    tips.push('\u591c\u95f4\u6d3b\u52a8\u5efa\u8bae\u63a7\u5236\u5728\u4f4f\u5bbf\u70b9 30 \u5206\u949f\u8fd4\u7a0b\u8303\u56f4\u5185\uff0c\u907f\u514d\u4e34\u65f6\u6362\u70b9\u3002')
  } else if (tripPlan.value.night_preference === '\u65e9\u5f52\u4f11\u606f') {
    tips.push('\u4eca\u65e5\u65e5\u7a0b\u5efa\u8bae\u4ee5\u65e9\u5f52\u4f11\u606f\u4e3a\u4e3b\uff0c\u5c3d\u91cf\u5728\u665a\u95f4\u9ad8\u5cf0\u524d\u8fd4\u56de\u4f4f\u5bbf\u70b9\u9644\u8fd1\u3002')
  }
  if (tripPlan.value.safety_preference === '\u7a33\u59a5\u4f18\u5148') {
    tips.push('\u72ec\u81ea\u51fa\u884c\u4f18\u5148\u9009\u62e9\u4eba\u6d41\u8f83\u591a\u3001\u7167\u660e\u8f83\u597d\u7684\u533a\u57df\u6d3b\u52a8\u3002')
  }
  return tips.slice(0, 3)
}

const timelineSummary = computed(() => {
  if (!tripPlan.value) return []
  return [
    { label: '\u5929\u6570', value: `${tripPlan.value.days.length}\u5929` },
    { label: '\u9884\u7b97', value: `${tripPlan.value.budget?.total || 0}\u5143` },
    { label: '\u8282\u594f', value: tripPlan.value.pace_preference }
  ]
})

const goBack = () => router.push({ name: 'home' })

onMounted(() => {
  try {
    const raw = sessionStorage.getItem('tripPlan')
    if (!raw) {
      message.error('\u672a\u627e\u5230\u884c\u7a0b\u6570\u636e\uff0c\u8bf7\u91cd\u65b0\u751f\u6210')
      goBack()
      return
    }
    const parsed = JSON.parse(raw) as TripPlan
    if (!parsed?.city || !Array.isArray(parsed.days) || parsed.days.length === 0) {
      message.error('\u884c\u7a0b\u6570\u636e\u683c\u5f0f\u9519\u8bef\uff0c\u8bf7\u91cd\u65b0\u751f\u6210')
      goBack()
      return
    }
    tripPlan.value = parsed
  } catch {
    message.error('\u8bfb\u53d6\u884c\u7a0b\u6570\u636e\u5931\u8d25\uff0c\u8bf7\u91cd\u65b0\u751f\u6210')
    goBack()
  }
})
</script>

<template>
  <div class="park-page result-page" v-if="tripPlan">
    <div class="park-topbar">
      <div class="park-brand">
        <span class="park-brand__dot"></span>
        <span class="park-brand__text">SoloPark</span>
      </div>
      <div class="park-badge">
        <span class="park-badge__icon"></span>
        <span>{{ tripPlan.days.length }}/{{ tripPlan.days.length + 8 }}</span>
      </div>
    </div>

    <section class="park-card result-hero">
      <div class="result-hero__header">
        <div>
          <div class="result-hero__eyebrow">Selected Entry</div>
          <h1 class="result-hero__title">{{ tripPlan.city }}</h1>
          <div class="result-hero__subtitle">&#x25B2; {{ tripPlan.start_date }} ~ {{ tripPlan.end_date }}</div>
        </div>
        <div class="result-hero__seal"></div>
      </div>

      <div class="result-hero__facts">
        <div v-for="item in timelineSummary" :key="item.label">
          <span class="result-hero__label">{{ item.label }}</span>
          <strong>{{ item.value }}</strong>
        </div>
      </div>

      <button class="park-pill-button result-hero__back" type="button" @click="goBack">
        &#x8FD4;&#x56DE;&#x91CD;&#x65B0;&#x89C4;&#x5212;
      </button>
    </section>

    <section v-if="tripPlan.fallback || tripPlan.partial_fallback" class="park-card notice-card">
      <div class="park-section-title">
        <span class="park-section-title__text">Notice</span>
      </div>
      <p v-if="tripPlan.fallback">
        &#x672C;&#x6B21;&#x7ED3;&#x679C;&#x7531;&#x57FA;&#x7840;&#x89C4;&#x5219;&#x751F;&#x6210;&#x3002;&#x68C0;&#x6D4B;&#x5230;&#x6A21;&#x578B;&#x6216;&#x5916;&#x90E8;&#x80FD;&#x529B;&#x4E0D;&#x53EF;&#x7528;&#x65F6;&#xFF0C;&#x7CFB;&#x7EDF;&#x4F1A;&#x4F18;&#x5148;&#x4FDD;&#x8BC1;&#x7ED3;&#x6784;&#x5B8C;&#x6574;&#x548C;&#x884C;&#x524D;&#x53EF;&#x7528;&#x6027;&#x3002;
      </p>
      <p v-else>
        &#x672C;&#x6B21;&#x751F;&#x6210;&#x4FDD;&#x7559;&#x4E86;&#x90E8;&#x5206;&#x771F;&#x5B9E;&#x7ED3;&#x679C;&#xFF0C;&#x4F46;&#x6587;&#x6848;&#x548C;&#x90E8;&#x5206;&#x7EC6;&#x8282;&#x5DF2;&#x4F7F;&#x7528;&#x5FEB;&#x901F;&#x964D;&#x7EA7;&#x7B56;&#x7565;&#x3002;
      </p>
    </section>

    <div class="result-grid">
      <section class="park-card side-card">
        <div class="park-section-title">
          <span class="park-section-title__text">Solo Notes</span>
        </div>
        <ul class="note-list">
          <li v-for="note in tripPlan.solo_reminders" :key="note">{{ note }}</li>
        </ul>
      </section>

      <section class="park-card side-card" v-if="tripPlan.budget">
        <div class="park-section-title">
          <span class="park-section-title__text">Budget Log</span>
        </div>
        <div class="budget-grid">
          <div class="budget-item">
            <span>&#x666F;&#x70B9;</span>
            <strong>{{ tripPlan.budget.total_attractions || 0 }}</strong>
          </div>
          <div class="budget-item">
            <span>&#x9152;&#x5E97;</span>
            <strong>{{ tripPlan.budget.total_hotels || 0 }}</strong>
          </div>
          <div class="budget-item">
            <span>&#x9910;&#x996E;</span>
            <strong>{{ tripPlan.budget.total_meals || 0 }}</strong>
          </div>
          <div class="budget-item">
            <span>&#x4EA4;&#x901A;</span>
            <strong>{{ tripPlan.budget.total_transportation || 0 }}</strong>
          </div>
        </div>
        <div class="budget-total">
          <span>&#x603B;&#x8BA1;</span>
          <strong>{{ tripPlan.budget.total || 0 }} &#x5143;</strong>
        </div>
      </section>
    </div>

    <section class="park-card timeline-card">
      <div class="park-section-title">
        <span class="park-section-title__text">Expedition Log</span>
      </div>

      <div class="timeline">
        <article v-for="(day, idx) in tripPlan.days" :key="day.date + idx" class="timeline-row">
          <div class="timeline-marker" :class="{ 'timeline-marker--active': idx === 0 }"></div>
          <div class="timeline-entry">
            <div class="timeline-entry__meta">{{ day.date }} &#x2022; {{ formatWeather(weatherByDate.get(day.date)) || '&#x5929;&#x6C14;&#x5F85;&#x66F4;&#x65B0;' }}</div>
            <h3 class="timeline-entry__title">{{ idx + 1 }}. {{ day.attractions?.[0]?.name || '&#x5F53;&#x65E5;&#x65E5;&#x7A0B;' }}</h3>
            <p class="timeline-entry__body">{{ day.description }}</p>

            <div v-if="getDayAdjustments(day.date).length" class="timeline-entry__tips">
              <span v-for="tip in getDayAdjustments(day.date)" :key="tip">{{ tip }}</span>
            </div>

            <div v-if="day.attractions?.length" class="detail-block">
              <h4>&#x666F;&#x70B9;&#x5B89;&#x6392;</h4>
              <div class="chip-list">
                <div v-for="item in day.attractions" :key="item.name + item.address" class="chip-card">
                  <div class="chip-card__title-row">
                    <strong>{{ item.name }}</strong>
                    <div class="chip-tags" v-if="getAttractionTags(item, day.date).length">
                      <span v-for="tag in getAttractionTags(item, day.date)" :key="tag">{{ tag }}</span>
                    </div>
                  </div>
                  <p>{{ item.address }}</p>
                  <small>{{ item.description }}</small>
                </div>
              </div>
            </div>

            <div v-if="day.transport_legs?.length" class="detail-block">
              <h4>&#x4EA4;&#x901A;&#x8DEF;&#x7EBF;</h4>
              <div class="route-list">
                <div v-for="leg in day.transport_legs" :key="`${leg.from_name}-${leg.to_name}-${leg.mode}`" class="route-item">
                  <div class="route-item__header">
                    <strong>{{ leg.from_name }} → {{ leg.to_name }}</strong>
                    <span>{{ leg.mode }}</span>
                  </div>
                  <p>{{ formatTransportSummary(leg) }}</p>
                </div>
              </div>
            </div>

            <div v-if="day.meals?.length" class="detail-block">
              <h4>&#x9910;&#x996E;&#x5B89;&#x6392;</h4>
              <div class="meal-list">
                <div v-for="meal in day.meals" :key="meal.type + meal.name" class="meal-item">
                  <span>{{ meal.type }}</span>
                  <strong>{{ meal.name }}</strong>
                  <em>{{ meal.estimated_cost }} &#x5143;</em>
                </div>
              </div>
            </div>
          </div>
        </article>
      </div>
    </section>
  </div>
</template>

<style scoped>
.result-page { display: flex; flex-direction: column; gap: 22px; }
.result-hero__header { display: flex; align-items: center; justify-content: space-between; gap: 20px; }
.result-hero__eyebrow, .timeline-entry__meta { color: var(--park-green-soft); font-size: 0.95rem; font-weight: 800; letter-spacing: 0.12em; text-transform: uppercase; line-height: 1.35; }
.result-hero__title { margin: 10px 0 8px; font-family: var(--park-serif); font-size: clamp(2.8rem, 6vw, 4.4rem); line-height: 0.96; letter-spacing: -0.05em; }
.result-hero__subtitle { color: var(--park-muted); font-size: 1.15rem; }
.result-hero__seal {
  width: 86px; height: 86px; border-radius: 999px; background: linear-gradient(180deg, rgba(248, 242, 232, 0.96), rgba(238, 228, 207, 0.9));
  box-shadow: inset 0 0 0 8px rgba(249, 243, 233, 0.85), 0 12px 24px rgba(98, 124, 95, 0.14); position: relative;
}
.result-hero__seal::after {
  content: ""; position: absolute; inset: 18px; border-radius: 999px; background: radial-gradient(circle at 30% 30%, #58a17c 0%, #d8af4e 32%, #3e86a8 72%, #1d617d 100%);
}
.result-hero__facts { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 18px; margin: 24px 0 28px; padding-top: 18px; border-top: 2px dashed rgba(154, 182, 148, 0.34); }
.result-hero__facts span { display: block; color: var(--park-green-soft); font-size: 0.84rem; font-weight: 800; letter-spacing: 0.16em; text-transform: uppercase; }
.result-hero__facts strong { display: block; margin-top: 8px; font-family: var(--park-serif); font-size: 1.75rem; }
.result-hero__back { width: min(420px, 100%); }
.notice-card p { margin: 0; color: var(--park-muted); line-height: 1.8; }
.result-grid { display: grid; grid-template-columns: 1.1fr 0.9fr; gap: 22px; }
.note-list { margin: 0; padding-left: 20px; color: var(--park-muted); line-height: 1.9; }
.note-list li + li { margin-top: 10px; }
.budget-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }
.budget-item, .budget-total, .chip-card, .meal-item, .timeline-entry { background: rgba(255, 251, 244, 0.78); border: 1px solid rgba(228, 220, 203, 0.8); box-shadow: var(--park-card-shadow); }
.budget-item { padding: 18px; border-radius: 18px; }
.budget-item span, .budget-total span { display: block; color: var(--park-green-soft); font-size: 0.84rem; font-weight: 800; letter-spacing: 0.12em; text-transform: uppercase; }
.budget-item strong, .budget-total strong { display: block; margin-top: 10px; font-family: var(--park-serif); font-size: 1.7rem; }
.budget-total { margin-top: 16px; padding: 20px; border-radius: 22px; }
.timeline { position: relative; padding-left: 28px; }
.timeline::before { content: ""; position: absolute; left: 11px; top: 10px; bottom: 10px; border-left: 3px dashed rgba(132, 171, 132, 0.55); }
.timeline-row { position: relative; display: grid; grid-template-columns: 28px 1fr; gap: 18px; align-items: start; }
.timeline-row + .timeline-row { margin-top: 18px; }
.timeline-marker { width: 24px; height: 24px; border-radius: 999px; background: #f7f1e5; border: 4px solid rgba(138, 178, 134, 0.72); box-shadow: 0 0 0 5px rgba(249, 243, 233, 0.86); margin-top: 16px; }
.timeline-marker--active { border-color: var(--park-gold); }
.timeline-entry { padding: 22px; border-radius: 24px; }
.timeline-entry__title { margin: 10px 0 10px; font-size: 1.9rem; line-height: 1.1; letter-spacing: -0.04em; }
.timeline-entry__body { margin: 0; color: #4f524d; font-size: 1.05rem; line-height: 1.8; }
.timeline-entry__tips { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 16px; }
.timeline-entry__tips span, .chip-tags span { display: inline-flex; align-items: center; min-height: 32px; padding: 6px 12px; border-radius: 999px; background: rgba(145, 180, 143, 0.12); color: var(--park-green-deep); font-size: 0.85rem; font-weight: 700; }
.detail-block { margin-top: 18px; }
.detail-block h4 { margin: 0 0 12px; color: var(--park-green-deep); font-size: 0.92rem; letter-spacing: 0.14em; text-transform: uppercase; }
.chip-list, .meal-list { display: flex; flex-direction: column; gap: 12px; }
.route-list { display: flex; flex-direction: column; gap: 12px; }
.chip-card { padding: 16px 18px; border-radius: 18px; }
.route-item { padding: 14px 18px; border-radius: 18px; background: rgba(255, 251, 244, 0.78); border: 1px solid rgba(228, 220, 203, 0.8); box-shadow: var(--park-card-shadow); }
.route-item__header { display: flex; justify-content: space-between; gap: 12px; align-items: center; }
.route-item__header strong { font-size: 1rem; }
.route-item__header span { color: var(--park-green-soft); font-weight: 800; letter-spacing: 0.08em; text-transform: uppercase; }
.route-item p { margin: 8px 0 0; color: var(--park-muted); line-height: 1.7; }
.chip-card__title-row { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; justify-content: space-between; }
.chip-card strong { font-size: 1.08rem; }
.chip-card p, .chip-card small { display: block; margin: 8px 0 0; color: var(--park-muted); line-height: 1.7; }
.chip-tags { display: flex; flex-wrap: wrap; gap: 8px; }
.meal-item { display: grid; grid-template-columns: 128px minmax(0, 1fr) auto; gap: 16px; align-items: center; padding: 14px 18px; border-radius: 18px; }
.meal-item span { color: var(--park-green-soft); font-weight: 800; letter-spacing: 0.08em; text-transform: uppercase; }
.meal-item strong { padding-left: 4px; }
.meal-item em { color: var(--park-muted); font-style: normal; }
@media (max-width: 960px) { .result-grid { grid-template-columns: 1fr; } }
@media (max-width: 768px) {
  .result-hero__header { flex-direction: column; align-items: flex-start; }
  .result-hero__eyebrow { font-size: 0.78rem; letter-spacing: 0.1em; }
  .result-hero__title { line-height: 1.02; }
  .result-hero__facts { grid-template-columns: 1fr; }
  .timeline { padding-left: 18px; }
  .timeline::before { left: 9px; }
  .timeline-row { grid-template-columns: 20px 1fr; gap: 12px; }
  .timeline-marker { width: 18px; height: 18px; border-width: 3px; box-shadow: 0 0 0 4px rgba(249, 243, 233, 0.86); }
  .meal-item { grid-template-columns: 1fr; gap: 8px; }
  .meal-item strong { padding-left: 0; }
}
</style>
