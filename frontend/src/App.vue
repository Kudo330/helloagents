<script setup lang="ts">
import { RouterView } from 'vue-router'
</script>

<template>
  <div class="app-shell">
    <div class="app-shell__veil"></div>
    <div class="app-shell__stem app-shell__stem--left"></div>
    <div class="app-shell__stem app-shell__stem--right"></div>
    <RouterView />
  </div>
</template>

<style>
:root {
  --park-bg: #eef0e8;
  --park-surface: rgba(247, 242, 232, 0.94);
  --park-surface-strong: #f6f0e4;
  --park-paper-dot: rgba(187, 172, 144, 0.16);
  --park-green: #5b8c63;
  --park-green-deep: #39684a;
  --park-green-soft: #9ab694;
  --park-gold: #c9a537;
  --park-ink: #2e302d;
  --park-muted: #6d7169;
  --park-shadow: 0 18px 50px rgba(75, 99, 77, 0.12);
  --park-card-shadow: 0 10px 28px rgba(90, 115, 90, 0.12);
  --park-radius-xl: 32px;
  --park-radius-lg: 24px;
  --park-radius-md: 18px;
  --park-serif: "Georgia", "Times New Roman", serif;
  --park-sans: "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
}

* { box-sizing: border-box; }
html, body, #app { min-height: 100%; }
body {
  margin: 0;
  color: var(--park-ink);
  font-family: var(--park-sans);
  background:
    radial-gradient(circle at top left, rgba(162, 192, 163, 0.22), transparent 30%),
    radial-gradient(circle at top right, rgba(209, 174, 62, 0.18), transparent 24%),
    linear-gradient(180deg, #edf0e8 0%, #e7ebe2 56%, #eff3eb 100%);
}
body::before {
  content: "";
  position: fixed;
  inset: 0;
  pointer-events: none;
  background:
    radial-gradient(circle at 15% 12%, rgba(255, 255, 255, 0.75), transparent 22%),
    radial-gradient(circle at 82% 16%, rgba(255, 255, 255, 0.45), transparent 18%),
    radial-gradient(circle at 50% 100%, rgba(255, 255, 255, 0.32), transparent 18%);
  z-index: 0;
}
#app { position: relative; }
.app-shell { position: relative; min-height: 100vh; isolation: isolate; overflow: hidden; }
.app-shell__veil {
  position: fixed; inset: 0; pointer-events: none; z-index: 0;
  background:
    radial-gradient(circle at 24% 20%, rgba(255, 255, 255, 0.6), transparent 24%),
    radial-gradient(circle at 76% 20%, rgba(255, 255, 255, 0.52), transparent 20%);
}
.app-shell__stem {
  position: fixed; width: 14px; height: 110vh; top: -6vh; border-radius: 999px;
  background: linear-gradient(180deg, rgba(147, 177, 142, 0) 0%, rgba(147, 177, 142, 0.78) 16%, rgba(147, 177, 142, 0.38) 78%, rgba(147, 177, 142, 0) 100%);
  opacity: 0.66; z-index: 0;
}
.app-shell__stem::before, .app-shell__stem::after {
  content: ""; position: absolute; width: 30px; height: 12px; border-radius: 999px; background: rgba(147, 177, 142, 0.66);
}
.app-shell__stem::before { left: -18px; top: 16%; transform: rotate(-62deg); }
.app-shell__stem::after { right: -18px; top: 48%; transform: rotate(62deg); }
.app-shell__stem--left { left: 19%; transform: rotate(5deg); }
.app-shell__stem--right { right: 14%; transform: rotate(-6deg); }
.park-page { position: relative; z-index: 1; width: min(1120px, calc(100vw - 32px)); margin: 0 auto; padding: 20px 0 44px; }
.park-topbar { display: flex; align-items: center; justify-content: space-between; gap: 16px; margin-bottom: 20px; }
.park-brand, .park-badge {
  display: inline-flex; align-items: center; gap: 12px; min-height: 58px; padding: 12px 22px; border-radius: 999px;
  background: rgba(248, 242, 232, 0.92); border: 1px solid rgba(255, 255, 255, 0.72); box-shadow: 0 8px 22px rgba(113, 133, 110, 0.14); backdrop-filter: blur(8px);
}
.park-brand__dot { width: 28px; height: 28px; border-radius: 10px; background: var(--park-green); position: relative; box-shadow: inset 0 -3px 0 rgba(44, 80, 53, 0.22); }
.park-brand__dot::after { content: ""; position: absolute; inset: 7px; border-radius: 999px; background: #f5f0e5; }
.park-brand__text { font-family: var(--park-serif); font-size: 1.95rem; line-height: 1; font-weight: 700; letter-spacing: -0.03em; }
.park-badge { background: linear-gradient(180deg, #d7b24a 0%, #c49f32 100%); color: #2f2a18; font-weight: 800; box-shadow: 0 12px 22px rgba(173, 136, 32, 0.24); }
.park-badge__icon { width: 24px; height: 24px; border-radius: 999px; border: 2px solid currentColor; position: relative; }
.park-badge__icon::after {
  content: ""; position: absolute; width: 9px; height: 5px; border-left: 3px solid currentColor; border-bottom: 3px solid currentColor; transform: rotate(-45deg); left: 5px; top: 5px;
}
.park-card, .park-card :where(.ant-card-body), .park-card :where(.ant-card-head) { border: none; }
.park-card {
  border-radius: var(--park-radius-xl) !important;
  background:
    radial-gradient(circle at 1px 1px, var(--park-paper-dot) 1.1px, transparent 0) 0 0/14px 14px,
    linear-gradient(180deg, rgba(249, 244, 236, 0.95), rgba(247, 241, 232, 0.98));
  border: 1px solid rgba(250, 248, 242, 0.95) !important;
  box-shadow: var(--park-shadow); overflow: hidden;
}
.park-card:not(.ant-card) { padding: 30px; }
.park-card :where(.ant-card-body) { padding: 30px; }
.park-card :where(.ant-card-head) { min-height: auto; padding: 24px 30px 0; background: transparent; }
.park-card :where(.ant-card-head-title) {
  padding: 0; color: var(--park-green-soft); font-size: 0.92rem; font-weight: 800; letter-spacing: 0.18em; text-transform: uppercase;
}
.park-section-title { display: flex; align-items: center; gap: 14px; margin-bottom: 18px; }
.park-section-title__text { font-family: var(--park-serif); font-weight: 700; font-size: 1.65rem; letter-spacing: -0.03em; line-height: 1.08; }
.park-section-title::after { content: ""; flex: 1; border-bottom: 2px dashed rgba(132, 171, 132, 0.45); }
.park-pill-button, .park-page :where(.ant-btn-primary) {
  height: 66px; border-radius: 20px; border: none; background: linear-gradient(180deg, var(--park-green) 0%, #4f845b 100%);
  box-shadow: inset 0 -5px 0 rgba(45, 89, 57, 0.44), 0 10px 24px rgba(72, 110, 76, 0.18); color: #f6f1e6; font-weight: 800; font-size: 1.1rem; cursor: pointer;
}
.park-page :where(.ant-btn-primary:not(:disabled):hover), .park-pill-button:hover { background: linear-gradient(180deg, #628f68 0%, #4d7c58 100%); color: #fff8ed; }
.park-page :where(.ant-input), .park-page :where(.ant-input-number), .park-page :where(.ant-input-number-input), .park-page :where(.ant-picker), .park-page :where(.ant-select-selector) {
  border-radius: 18px !important; border-color: rgba(132, 152, 120, 0.18) !important; background: rgba(255, 251, 244, 0.92) !important; box-shadow: inset 0 0 0 1px rgba(250, 248, 241, 0.6);
}
.park-page :where(.ant-input), .park-page :where(.ant-picker), .park-page :where(.ant-select-selector) { min-height: 54px; padding-top: 10px !important; padding-bottom: 10px !important; }
.park-page :where(.ant-input-number) { width: 100%; }
.park-page :where(.ant-form-item-label > label) { color: var(--park-muted); font-size: 0.92rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; }
@media (max-width: 768px) {
  .park-page { width: min(100vw - 20px, 100%); padding-top: 14px; }
  .park-topbar { flex-direction: column; align-items: stretch; }
  .park-brand, .park-badge { justify-content: center; }
  .park-card:not(.ant-card) { padding: 22px; }
  .park-card :where(.ant-card-body) { padding: 22px; }
  .park-card :where(.ant-card-head) { padding: 20px 22px 0; }
}
</style>
