import re
import unicodedata

SLUG_OK = '-_~'

def slugify(s, ok=SLUG_OK, lower=True, spaces=False):
    # L and N signify letter/number.
    # http://www.unicode.org/reports/tr44/tr44-4.html#GC_Values_Table
    rv = []
    s = re.sub('\s*&\s*', ' and ', s)
    for c in unicodedata.normalize('NFKC', s):
        cat = unicodedata.category(c)[0]
        if cat in 'LN' or c in ok:
            rv.append(c)
        if cat == 'Z':  # space
            rv.append(' ')
    new = ''.join(rv).strip()
    if not spaces:
        new = re.sub('[-\s]+', '-', new)
    return new.lower() if lower else new

