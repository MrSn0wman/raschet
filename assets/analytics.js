// Расчёт.net — только обезличенные просмотры. Политика privacy.js обязательна.
var YM_ID = '113965438';
var GA_ID = '';
(function(){
  'use strict';
  const privacy = window.RASCHET_PRIVACY;
  if (!privacy || !privacy.canTrack()) return;
  const pageURL = privacy.safeURL(location.href);
  const referrer = document.referrer ? privacy.safeURL(document.referrer) : '';
  if (YM_ID){
    (function(m,e,t,r,i,k,a){
      m[i]=m[i]||function(){(m[i].a=m[i].a||[]).push(arguments)};
      m[i].l=1*new Date();
      for (var j = 0; j < document.scripts.length; j++) {if (document.scripts[j].src === r) return;}
      k=e.createElement(t); a=e.getElementsByTagName(t)[0]; k.async=1; k.src=r;
      k.referrerPolicy='no-referrer';
      a.parentNode.insertBefore(k,a);
    })(window, document,'script','https://mc.yandex.ru/metrika/tag.js?id='+encodeURIComponent(YM_ID), 'ym');
    window.ym(Number(YM_ID), 'init', {
      ssr:true, webvisor:false, clickmap:false, trackLinks:false,
      referrer:referrer, url:pageURL, accurateTrackBounce:true
    });
  }
  if (GA_ID){
    var s=document.createElement('script'); s.async=true;
    s.src='https://www.googletagmanager.com/gtag/js?id='+encodeURIComponent(GA_ID);
    s.referrerPolicy='no-referrer';
    document.head.appendChild(s);
    window.dataLayer=window.dataLayer||[];
    window.gtag=function(){window.dataLayer.push(arguments)};
    window.gtag('js',new Date());
    window.gtag('config',GA_ID,{page_location:pageURL, page_referrer:referrer, allow_google_signals:false});
  }
})();
