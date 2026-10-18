/*
 * amz-geo-router.js — 亚马逊联盟地理路由（TechPassive 静态站）
 *
 * 设计原则（2026-10-18）：
 *  - amazon.co.jp 链接 = 日本独占商品（如蝴蝶乒乓球拍），对所有访客保持 co.jp，
 *    不跳转到美站（美站无同款 ASIN）。新加坡等访客点进去直接在 co.jp 下单
 *    （支持国际配送），站长赚 JP 佣金。
 *  - amazon.com 链接 = 通用/多站都有的商品（工具箱、鼠标、书），按访客国家路由：
 *      JP  → amazon.co.jp  + tag=techpassive-22
 *      其他 → amazon.com   + tag=techpassive-20
 *
 * 失败安全：任何网络/超时/解析异常都「不改链接」，链接保持原样（= 当前行为），
 * 不会破坏购买链路。国家码缓存在 localStorage，减少重复请求。
 */
(function () {
  'use strict';
  var JP_TAG = 'techpassive-22';
  var US_TAG = 'techpassive-20';

  function rehost(href, host) {
    return href.replace(/https?:\/\/(www\.)?amazon\.(com|co\.jp)/i, function (m, p, www, h) {
      return p + 'www.amazon.' + host;
    });
  }

  function setTag(href, tag) {
    if (/[?&]tag=techpassive-\d+/i.test(href)) {
      return href.replace(/tag=techpassive-\d+/i, 'tag=' + tag);
    }
    return href + (href.indexOf('?') >= 0 ? '&' : '?') + 'tag=' + tag;
  }

  function apply(country) {
    if (!country) return; // 安全默认：不动链接
    var isJP = country.toUpperCase() === 'JP';
    var links = document.querySelectorAll('a[href*="tag=techpassive"]');
    for (var i = 0; i < links.length; i++) {
      var a = links[i];
      var href = a.href;
      var m = href.match(/amazon\.(com|co\.jp)/i);
      if (!m) continue;
      var host = m[1].toLowerCase();
      if (host === 'co.jp') {
        // 日本独占商品：任何人都不跳，锁 co.jp
        a.href = rehost(setTag(href, JP_TAG), 'co.jp');
      } else {
        // 通用链接：按国家路由
        if (isJP) {
          a.href = rehost(setTag(href, JP_TAG), 'co.jp');
        } else {
          a.href = rehost(setTag(href, US_TAG), 'com');
        }
      }
    }
  }

  function getCountry() {
    try {
      var c = localStorage.getItem('amz_cc');
      if (c !== null && c !== '') return Promise.resolve(c);
    } catch (e) {}
    var ctrl = new AbortController();
    var timer = setTimeout(function () { ctrl.abort(); }, 1500);
    return fetch('https://ipwho.is/', { signal: ctrl.signal })
      .then(function (r) { return r.json(); })
      .then(function (d) {
        var cc = (d && d.country_code) ? d.country_code : '';
        try { localStorage.setItem('amz_cc', cc || ''); } catch (e) {}
        return cc;
      })
      .catch(function () {
        // 兜底：ipapi.co
        return fetch('https://ipapi.co/json/')
          .then(function (r) { return r.json(); })
          .then(function (d) {
            var cc = (d && d.country_code) ? d.country_code : '';
            try { localStorage.setItem('amz_cc', cc || ''); } catch (e) {}
            return cc;
          })
          .catch(function () { return ''; });
      })
      .finally(function () { clearTimeout(timer); });
  }

  function init() { getCountry().then(apply); }

  if (document.readyState !== 'loading') { init(); }
  else { document.addEventListener('DOMContentLoaded', init); }
})();
