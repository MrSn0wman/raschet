// Расчёт.net — аналитика. ID счётчиков зашиты здесь, больше ничего менять не надо.
// Яндекс.Метрика: https://metrika.yandex.ru → Счётчики → ID счётчика (число)
// GA4: https://analytics.google.com → Администратор → Потоки данных → G-XXXXXXX
var YM_ID = '113965438';   // Яндекс.Метрика, raschet.net
var GA_ID = '';   // например 'G-ABC123DEF4'
(function(){
  if (YM_ID){
    (function(m,e,t,r,i,k,a){
        m[i]=m[i]||function(){(m[i].a=m[i].a||[]).push(arguments)};
        m[i].l=1*new Date();
        for (var j = 0; j < document.scripts.length; j++) {if (document.scripts[j].src === r) { return; }}
        k=e.createElement(t),a=e.getElementsByTagName(t)[0],k.async=1,k.src=r,a.parentNode.insertBefore(k,a)
    })(window, document,'script','https://mc.yandex.ru/metrika/tag.js?id='+encodeURIComponent(YM_ID), 'ym');
    ym(Number(YM_ID), 'init', {ssr:true, webvisor:true, clickmap:true, ecommerce:'dataLayer', referrer: document.referrer, url: location.href, accurateTrackBounce:true, trackLinks:true});
  }
  if (GA_ID){
    var s=document.createElement('script'); s.async=true;
    s.src='https://www.googletagmanager.com/gtag/js?id='+encodeURIComponent(GA_ID);
    document.head.appendChild(s);
    window.dataLayer=window.dataLayer||[];
    window.gtag=function(){dataLayer.push(arguments)};
    gtag('js',new Date()); gtag('config',GA_ID);
  }
})();
