#!/usr/bin/env python2.7
import sys
import json
import lxml.etree
from lxml.html.builder import E

SVG_NS = {"svg": "http://www.w3.org/2000/svg"}

def main(argv=sys.argv, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr, exit=sys.exit):
    if len(argv) != 3 or argv[1] not in ("dump", "load"):
        stderr.write("Usage: {0} dump slideshow.html > data.json\n"
                     "       {0} load slideshow.html < data.json\n"
                     "       {0} dump old-slideshow.html | {0} load new-slideshow.html\n"
                     .format(argv[0]))
        return exit()

    _, command, filename = argv

    doc = lxml.etree.parse(filename, lxml.etree.HTMLParser(encoding="UTF-8"))

    if command == "dump":
        data = dump_from_document(doc)

        json.dump(data, stdout, sort_keys=True, indent=4)
    else:
        data = json.load(stdin)
        load_into_document(doc, data)

        doc.write(filename, pretty_print=True, method="html")

def dump_from_document(doc):
    audio_sources = [e.attrib["src"] for e in doc.findall(".//audio/source")]
    slides = []

    # Note that we are not searching by class! This is because XPath 1.0
    # makes perfect class matching a mess, not because this is optimal.
    for e in doc.findall(".//*[@popcorn-slideshow]"):
        # prefer to cast times to integer but prepared to handle floats
        time = json.loads(e.attrib["popcorn-slideshow"])

        transcript_e = e.find(".//*[@class='transcript']")
        transcript = get_inner_html(transcript_e)

        slides.append({
            "time": time,
            "transcript": transcript
        })

    return {
        "audio_sources": audio_sources,
        "slides": slides
    }

def load_into_document(doc, data):
    audio_e = doc.find(".//audio")

    for child in audio_e.getchildren():
        audio_e.remove(child)

    for source in data["audio_sources"]:
        audio_e.append(E.source(src=source))

    slide_es = list(doc.findall(".//*[@popcorn-slideshow]"))

    if len(slide_es) != len(data["slides"]):
        sys.stderr.write("Warning: number of slides in document and JSON do not match.\n")
        sys.stderr.write("         some data may be ignored.\n")

    for slide_e, slide_data in zip(slide_es, data["slides"]):
        slide_e.attrib["popcorn-slideshow"] = str(slide_data["time"])

        transcript_e = slide_e.find(".//*[class='transcript']")
        if not transcript_e:
            transcript_e = E.div(**{"class": "transcript"})
            slide_e.append(transcript_e)

        set_inner_html(transcript_e, slide_data["transcript"])

def get_inner_html(e):
    parts = []

    if e.text:
        parts.append(e.text)

    for child in e.getchildren():
        child_source = lxml.etree.tostring(child, method="html", encoding="UTF-8")
        parts.append(child_source)

    return "".join(parts)

def set_inner_html(e, html):
    e.text = None

    for child in e.getchildren():
        e.remove(child)

    new_children = lxml.html.fragments_fromstring(html)
    if isinstance(new_children[0], (str, unicode)):
        e.text = new_children[0]
        new_children = new_children[1:]

    for new_child in new_children:
        e.append(new_child)

if __name__ == "__main__":
    sys.exit(main())
