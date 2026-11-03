# -*- coding: utf-8 -*-
"""Idempotent CSP injection into an explicit output tree."""
from site_common import html_files, read, site_parser, write

CSP = ('<meta http-equiv="Content-Security-Policy" content="default-src \'self\'; script-src \'self\' \'unsafe-inline\' https://mc.yandex.ru https://www.googletagmanager.com https://yandex.ru https://an.yandex.ru https://yastatic.net https://*.yandex.net; style-src \'self\' \'unsafe-inline\'; img-src \'self\' data: https:; font-src \'self\' https://yastatic.net; connect-src \'self\' https://mc.yandex.ru https://www.google-analytics.com https://www.googletagmanager.com https://yandex.ru https://an.yandex.ru https://*.yandex.net https://yastatic.net; frame-src https://yandex.ru https://an.yandex.ru https://*.yandex.net https://mc.yandex.ru https://yastatic.net; media-src https:; base-uri \'self\'; form-action \'self\'">')

def process(site):
    from site_common import safe_destination
    site = safe_destination(site)
    count = 0
    for path in html_files(site, full=True):
        text = read(path)
        if "Content-Security-Policy" not in text:
            if "</head>" not in text: raise ValueError("Missing head: " + str(path))
            write(path, text.replace("</head>", CSP + "\n</head>", 1))
            count += 1
    print("CSP inserted:", count)

if __name__ == "__main__":
    process(site_parser(__doc__).parse_args().site)
