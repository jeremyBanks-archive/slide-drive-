#!/usr/bin/env python2.7
import sys
import lxml.etree
from copy import deepcopy

SVG_NS = {'svg': "http://www.w3.org/2000/svg"}

def main(*argv):
    if len(argv) < 2:
        sys.stderr.write("Usage: {0} slides.svg > slideshow.html\n"
                         .format(argv[0]))
        sys.exit()

    filename = argv[1]

    svg_doc = lxml.etree.parse(filename, lxml.etree.XMLParser())

    for slide_title in svg_doc.findall(".//svg:g[@class='com.sun.star.presentation.TitleTextShape']", namespaces=SVG_NS):
        title = get_text(slide_title).strip()
        break
    else:
        title = None
    
    sys.stderr.write("Loaded presentation: " + title + "\n")
    
    processed_slides = process_svg(svg_doc)
    
    html_doc = prepare_html(processed_slides, title)
    
    sys.stdout.write(lxml.etree.tostring(html_doc, encoding='UTF-8',  pretty_print=True, method="html"))
    sys.exit(0)

def process_svg(svg_doc):
    """Processes an SVG document of slides and returns a list of processed individual slide documents.
    
    Processing includes removing embedded fonts and rewriting references to them.
    """
    sys.stderr.write("Stripping embedded fonts.\n")
    for font in svg_doc.findall(".//svg:font", namespaces=SVG_NS):
        if font.tail.strip():
            sys.stderr.write("Warning: trailing text being deleted along with font element.")
        font.getparent().remove(font)

    sys.stderr.write("Rewriting references to embedded fonts.\n")

    for embedded_font_using in svg_doc.findall(".//*[@font-family]", namespaces=SVG_NS):
        if not embedded_font_using.attrib["font-family"].endswith(" embedded"):
            continue
    
        embedded_font_using.attrib["font-family"] = embedded_font_using.attrib["font-family"][:-len(" embedded")]
    
    processed_slides = []
    
    sys.stderr.write("Generating individual SVG documents for each slide.\n")
    
    for slide in svg_doc.findall(".//svg:g[@class='Slide']", namespaces=SVG_NS):
        slide_doc = deepcopy(svg_doc)
    
        for potential_slide in slide_doc.findall(".//svg:g[@class='Slide']", namespaces=SVG_NS):
            if potential_slide.attrib["id"] != slide.attrib["id"]:
                potential_slide.getparent().remove(potential_slide)
            else:
                potential_slide.attrib["visibility"] = "visible"
        
        processed_slides.append(slide_doc)
    
    return processed_slides

def prepare_html(slides, title=None):
    """Takes a list of SVG documents and produces an HTML document presenting them."""
    
    sys.stderr.write("Importing template\n")
    html_doc = lxml.etree.parse("../index.html", lxml.etree.HTMLParser(recover=True, encoding="UTF-8"))
    
    html_doc.find(".//title").text = title or "Untitled Presentation"
    
    container = html_doc.find("//*[@class='deck-container']")
    
    for element in container.getchildren():
        if "slide" in element.attrib["class"]:
            container.remove(element)
    
    for i, slide in enumerate(slides):
        htmlized_slide =  lxml.html.fragment_fromstring(
            lxml.etree.tostring(slide), lxml.etree.HTMLParser())
            
        htmlized_slide.attrib["class"] = "slide"
        htmlized_slide.attrib["popcorn-slideshow"] = str(i)
        
        container.insert(i, htmlized_slide)
    
    return html_doc

def get_text(node, include_trailing=False):
    """Gets the text content of a node and its children, ignoring node-trailing text by default.
    
    Intended for use on SVG text."""
    parts = []
    if node.text is not None:
        parts.append(node.text)
    for child in node.getchildren():
        parts.append(get_text(child, include_trailing))
    if include_trailing and node.tail:
        parts.append(node.tail)
    return "".join(parts)

if __name__ == "__main__":
    sys.exit(main(*sys.argv[:]))
