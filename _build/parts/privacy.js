// Единая политика приватности. Подключать синхронно в head до внешних скриптов.
(function(){
  'use strict';
  if (window.RASCHET_PRIVACY) return;
  const sensitiveRoutes = Object.freeze([
    'proverka-nomera-karty', 'proverka-inn', 'proverka-snils',
    'generator-paroley', 'qr-generator', 'generator-promokodov',
    'sluchaynyy-vybor', 'peremeshat-spisok', 'razdelit-na-gruppy',
    'sravnenie-spiskov', 'udalenie-dubley-strok', 'transliteraciya',
    'schetchik-slov', 'feedback', 'doli-v-kvartire'
  ]);
  const legacyRoutes = Object.freeze([
    'calc-bank-card', 'calc-inn', 'calc-snils',
    'calc-password-generator', 'calc-qr-generator', 'calc-promo-generator',
    'calc-random-pick', 'calc-shuffle-list', 'calc-split-groups',
    'calc-compare-lists', 'calc-dedupe-lines', 'calc-translit', 'calc-word-counter',
    'calc-shares-apartment'
  ]);
  const sensitiveNames = new Set(sensitiveRoutes.concat(legacyRoutes));
  const safeURL = (value) => {
    try {
      const url = new URL(value, location.href);
      return /^https?:$/.test(url.protocol) ? url.origin + url.pathname : '';
    } catch (e) { return ''; }
  };
  const isSensitiveRoute = (path) => {
    try {
      const normalized = decodeURIComponent(path).toLowerCase().replace(/\\/g, '/').replace(/\/index\.html\/?$/, '/');
      return normalized.split('/').filter(Boolean).some((name) => sensitiveNames.has(name.replace(/\.html$/, '')));
    } catch (e) { return true; }
  };
  const hasPrivateFields = () => !!document.querySelector(
    '.calc-card textarea, .calc-card input[type="password"], .calc-card input[type="email"], .calc-card input[type="tel"], [data-private]'
  );
  const routeSensitive = isSensitiveRoute(location.pathname);
  // Только разрешённые страницы получают временный снимок параметров для восстановления.
  let shareSearch = routeSensitive ? '' : location.search;
  // Якорь не возвращаем в URL: после загрузки прокручиваем лишь к существующему простому id.
  let anchor = '';
  try {
    const id = decodeURIComponent(location.hash.slice(1));
    if (/^[a-zA-Z][\w:-]{0,63}$/.test(id)) anchor = id;
  } catch (e) {}
  if (anchor){
    document.addEventListener('DOMContentLoaded', () => {
      requestAnimationFrame(() => {
        const target = document.getElementById(anchor);
        if (target) target.scrollIntoView();
      });
    }, { once: true });
  }
  let urlClean = !location.search && !location.hash;
  if (!urlClean){
    try {
      history.replaceState(history.state, '', safeURL(location.href));
      urlClean = !location.search && !location.hash;
    } catch (e) { shareSearch = ''; }
  }
  const canShare = () => !routeSensitive && !hasPrivateFields();
  const numericTextIds = new Set([
    'c-amount', 'm-amount', 'm-down', 'd-amount', 'd-topup',
    'e-amount', 'e-monthly-extra', 'e-once-amount', 'cv-amount', 'ux-ts'
  ]);
  const canShareField = (el) => {
    if (!canShare() || !el || !el.matches('[data-share]')) return false;
    if (el.tagName === 'SELECT') return true;
    if (el.tagName !== 'INPUT') return false;
    if (['number', 'checkbox', 'radio', 'date', 'datetime-local', 'time', 'month', 'week'].includes(el.type)) return true;
    return el.type === 'text' && numericTextIds.has(el.id);
  };
  const shareValue = (el, value) => {
    if (!canShareField(el) || typeof value !== 'string' || value.length > 128) return null;
    if (el.tagName === 'SELECT') return Array.from(el.options).some((o) => o.value === value) ? value : null;
    if (el.type === 'checkbox' || el.type === 'radio') return value === 'true' || value === 'false' ? value : null;
    if (el.type === 'number' || el.type === 'text'){
      const normalized = value.replace(/\s/g, '').replace(',', '.');
      // Форматтер денежных полей удаляет всё, кроме цифр: не передаём ему дроби, знак и exponent.
      const grammar = el.type === 'text'
        ? (el.id === 'ux-ts' ? /^-?\d+$/ : /^\d+$/)
        : /^[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[-+]?\d+)?$/i;
      return grammar.test(normalized) && Number.isFinite(Number(normalized)) ? normalized : null;
    }
    return /^[0-9T: .+-]+$/.test(value) ? value : null;
  };
  window.RASCHET_PRIVACY = Object.freeze({
    sensitiveRoutes, isSensitiveRoute, safeURL, canShare, canShareField, shareValue,
    canTrack: () => urlClean && !location.search && !location.hash && !isSensitiveRoute(location.pathname) && !hasPrivateFields(),
    getShareParams: () => new URLSearchParams(canShare() ? shareSearch : '')
  });
})();
