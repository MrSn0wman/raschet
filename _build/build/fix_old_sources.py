# -*- coding: utf-8 -*-
# Зеркалирование XSS-фиксов в исходники raschet-old (чтобы пересборка не теряла их).
import io

ESC = 'function esc(s){ return String(s).replace(/&/g,\'&amp;\').replace(/</g,\'&lt;\').replace(/>/g,\'&gt;\').replace(/"/g,\'&quot;\'); }\n\n'

def patch(path, pairs, insert_before, name):
    t = io.open(path, encoding="utf-8").read()
    for old, new in pairs:
        if old in t:
            t = t.replace(old, new, 1)
            print("OK patch", name, "|", old[:50])
        else:
            print("MISS", name, "|", old[:50])
    if insert_before:
        if insert_before in t and "function esc(" not in t:
            t = t.replace(insert_before, ESC + insert_before, 1)
            print("OK esc-def", name)
        else:
            print("SKIP/MISS esc-def", name)
    io.open(path, "w", encoding="utf-8", newline="\n").write(t)

patch(r"C:\Kimi\raschet-old\calc-shares-apartment.html",
      [("value=\"' + (name||'') + '\"", "value=\"' + esc(name||'') + '\""),
       ("'<tr><td>' + s.name + '</td>", "'<tr><td>' + esc(s.name) + '</td>")],
      "function addShareRow(", "shares")

patch(r"C:\Kimi\raschet-old\calc-split-groups.html",
      [("g.join('<br>')", "g.map(esc).join('<br>')")],
      "function splitIntoGroups(", "split")

patch(r"C:\Kimi\raschet-old\calc-compare-lists.html",
      [("(onlyA.join('\\n') || '—')", "(onlyA.map(esc).join('\\n') || '—')"),
       ("(common.join('\\n') || '—')", "(common.map(esc).join('\\n') || '—')"),
       ("(onlyB.join('\\n') || '—')", "(onlyB.map(esc).join('\\n') || '—')")],
      "function parseList(", "compare")

# промокоды: crypto в исходнике
patch(r"C:\Kimi\raschet-old\calc-promo-generator.html",
      [("code += charset[Math.floor(Math.random()*charset.length)];",
        "code += charset[secureIndex(charset.length)];")],
      None, "promo-expr")
# secureIndex fn для промокодов
t = io.open(r"C:\Kimi\raschet-old\calc-promo-generator.html", encoding="utf-8").read()
SIF = "function secureIndex(max){const a=new Uint32Array(1);const limit=Math.floor(4294967296/max)*max;let x;do{crypto.getRandomValues(a);x=a[0];}while(x>=limit);return x%max;}\n"
if "function generatePromoCodes(" in t and "secureIndex(max)" not in t:
    t = t.replace("function generatePromoCodes(", SIF + "function generatePromoCodes(", 1)
    io.open(r"C:\Kimi\raschet-old\calc-promo-generator.html", "w", encoding="utf-8", newline="\n").write(t)
    print("OK secureIndex fn promo")
