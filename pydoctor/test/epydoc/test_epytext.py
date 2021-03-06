from pydoctor.epydoc.markup import epytext, flatten


def epytext2html(s):
    errs = []
    v = flatten(epytext.parse_docstring(s, errs).to_stan(None))
    if errs:
        raise errs[0]
    return (v or '').rstrip()


def parse(s):
    # this strips off the <epytext>...</epytext>
    return ''.join(str(n) for n in epytext.parse(s).children)


def test_basic_list():
    P1 = "This is a paragraph."
    P2 = "This is a \nparagraph."
    LI1 = "  - This is a list item."
    LI2 = "\n  - This is a list item."
    LI3 = "  - This is a list\n  item."
    LI4 = "\n  - This is a list\n  item."
    PARA = ('<para>This is a paragraph.</para>')
    ONELIST = ('<ulist><li><para inline=True>This is a '
               'list item.</para></li></ulist>')
    TWOLIST = ('<ulist><li><para inline=True>This is a '
               'list item.</para></li><li><para inline=True>This is a '
               'list item.</para></li></ulist>')

    for p in (P1, P2):
        for li1 in (LI1, LI2, LI3, LI4):
            assert parse(li1) == ONELIST
            assert parse('%s\n%s' % (p, li1)) == PARA+ONELIST
            assert parse('%s\n%s' % (li1, p)) == ONELIST+PARA
            assert parse('%s\n%s\n%s' % (p, li1, p)) == PARA+ONELIST+PARA

            for li2 in (LI1, LI2, LI3, LI4):
                assert parse('%s\n%s' % (li1, li2)) == TWOLIST
                assert parse('%s\n%s\n%s' % (p, li1, li2)) == PARA+TWOLIST
                assert parse('%s\n%s\n%s' % (li1, li2, p)) == TWOLIST+PARA
                assert parse('%s\n%s\n%s\n%s' % (p, li1, li2, p)) == PARA+TWOLIST+PARA

    LI5 = "  - This is a list item.\n\n    It contains two paragraphs."
    LI5LIST = ('<ulist><li><para inline=True>This is a list item.</para>'
               '<para>It contains two paragraphs.</para></li></ulist>')
    assert parse(LI5) == LI5LIST
    assert parse('%s\n%s' % (P1, LI5)) == PARA+LI5LIST
    assert parse('%s\n%s\n%s' % (P2, LI5, P1)) == PARA+LI5LIST+PARA

    LI6 = ("  - This is a list item with a literal block::\n"
           "    hello\n      there")
    LI6LIST = ('<ulist><li><para inline=True>This is a list item with a literal '
               'block:</para><literalblock>  hello\n    there'
               '</literalblock></li></ulist>')
    assert parse(LI6) == LI6LIST
    assert parse('%s\n%s' % (P1, LI6)) == PARA+LI6LIST
    assert parse('%s\n%s\n%s' % (P2, LI6, P1)) == PARA+LI6LIST+PARA


def test_item_wrap():
    LI = "- This is a list\n  item."
    ONELIST = ('<ulist><li><para inline=True>This is a '
               'list item.</para></li></ulist>')
    TWOLIST = ('<ulist><li><para inline=True>This is a '
               'list item.</para></li><li><para inline=True>This is a '
               'list item.</para></li></ulist>')
    for indent in ('', '  '):
        for nl1 in ('', '\n'):
            assert parse(nl1+indent+LI) == ONELIST
            for nl2 in ('\n', '\n\n'):
                assert parse(nl1+indent+LI+nl2+indent+LI) == TWOLIST


def test_literal_braces():
    """SF bug #1562530 reported some trouble with literal braces.
    This test makes sure that braces are getting rendered as desired.
    """
    assert epytext2html("{1:{2:3}}") == '<p>{1:{2:3}}</p>'
    assert epytext2html("C{{1:{2:3}}}") == '<p><code>{1:{2:3}}</code></p>'
    assert epytext2html("{1:C{{2:3}}}") == '<p>{1:<code>{2:3}</code>}</p>'
    assert epytext2html("{{{}{}}{}}") == '<p>{{{}{}}{}}</p>'
    assert epytext2html("{{E{lb}E{lb}E{lb}}}") == '<p>{{{{{}}</p>'
