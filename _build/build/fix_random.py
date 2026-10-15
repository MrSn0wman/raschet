# -*- coding: utf-8 -*-
# Замена Math.random на crypto.getRandomValues в генераторах случайности.
# Патчит готовый сайт (C:\Kimi\raschet) и исходники (raschet-old).
import io

SIF = "function secureInt(max){const a=new Uint32Array(1);const limit=Math.floor(4294967296/max)*max;let x;do{crypto.getRandomValues(a);x=a[0];}while(x>=limit);return x%max;}\n"

JOBS = [
    # (готовый, исходник, [(old,new)], точка вставки secureInt)
    (r"C:\Kimi\raschet\sluchaynye-chisla\index.html", r"C:\Kimi\raschet-old\calc-random-number.html",
     [("Math.floor(Math.random() * (max - min + 1)) + min", "secureInt(max - min + 1) + min"),
      ("Math.floor(Math.random() * (i + 1))", "secureInt(i + 1)")],
     None),
    (r"C:\Kimi\raschet\sluchaynyy-vybor\index.html", r"C:\Kimi\raschet-old\calc-random-pick.html",
     [("items[Math.floor(Math.random()*items.length)]", "items[secureInt(items.length)]"),
      ("Math.floor(Math.random() * (i + 1))", "secureInt(i + 1)")],
     None),
    (r"C:\Kimi\raschet\peremeshat-spisok\index.html", r"C:\Kimi\raschet-old\calc-shuffle-list.html",
     [("Math.floor(Math.random() * (i + 1))", "secureInt(i + 1)")],
     None),
    (r"C:\Kimi\raschet\razdelit-na-gruppy\index.html", r"C:\Kimi\raschet-old\calc-split-groups.html",
     [("Math.floor(Math.random() * (i + 1))", "secureInt(i + 1)")],
     "function shuffleArray("),
]

for built, old, pairs, anchor in JOBS:
    for path in (built, old):
        t = io.open(path, encoding="utf-8").read()
        if "Math.random" not in t:
            print("skip (clean):", path.split("\\")[-2] if "index" in path else path.split("\\")[-1])
            continue
        ok = True
        for o, n in pairs:
            if o in t:
                t = t.replace(o, n)
            else:
                # в исходниках могут быть вариации пробелов
                o2 = o.replace(" * ", "*").replace(" *", "*").replace("* ", "*")
                if o2 in t:
                    t = t.replace(o2, n)
                else:
                    print("MISS:", path.split("\\")[-1], "|", o[:50])
                    ok = False
        # вставка secureInt: перед первым оставшимся/бывшим местом использования
        if "secureInt(" in t and "function secureInt(" not in t:
            # вставляем в начало последнего <script> с логикой: перед anchor или перед первой функцией
            if anchor and anchor in t:
                t = t.replace(anchor, SIF + anchor, 1)
            else:
                # перед первым "function random" / "function shuffle" / "function pick" — ищем generic
                for cand in ("function random", "function shuffle", "function pick", "function generate", "const "):
                    idx = t.find(cand)
                    if idx > 0:
                        t = t[:idx] + SIF + t[idx:]
                        break
                else:
                    print("NO ANCHOR for secureInt:", path)
                    ok = False
        if "Math.random" not in t:
            io.open(path, "w", encoding="utf-8", newline="\n").write(t)
            print("OK:", path.split("\\")[-2] if "index" in path else path.split("\\")[-1])
        else:
            left = t.count("Math.random")
            print("PARTIAL (%d left):" % left, path.split("\\")[-1])
