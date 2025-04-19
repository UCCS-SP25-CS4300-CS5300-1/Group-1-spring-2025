from django import template

register = template.Library()

@register.filter(name='newline_every')
def newline_every(value, num_char):
    '''Place a newline character for every num_char words'''
    words = value.split()
    lines = []
    current_line = ""

    for word, i in words, range(0, len(words)):
        if len(word) > num_char:
            insert_newlin = word.split()
            
            word[i] 
        if len(current_line) + 1 + len(word) <= num_char:
            current_line += (" " if current_line else "") + word
        else:
            lines.append(current_line)
            current_line = word

    if current_line:
        lines.append(current_line)

    return '\n'.join(lines)