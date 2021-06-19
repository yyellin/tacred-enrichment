to_fix = open(r'C:\Users\JYellin\re_1\tacred\results\general\test-ucca_paths_v0.0.5.csv', encoding='utf-8')
fixed = open(r'C:\Users\JYellin\re_1\tacred\results\general\fixed.csv','w', encoding='utf-8', newline='', buffering=1)


in_word_to_remove = False
in_brackets = False

for line in to_fix:

    replace_line = ""
    skip = False

    for letter in line:
        if skip:
            skip = False
            continue

        if not in_brackets and letter == "'":
            continue

        if not in_brackets and letter == '[':
            replace_line += letter
            in_brackets = True
            continue

        if not in_brackets and letter == ",":
            replace_line += letter
            skip = True
            continue

        if not in_brackets and letter != "":
            replace_line += letter
            continue

        if in_brackets and letter != "]":
            replace_line += letter
            continue

        if in_brackets and letter == "]":
            replace_line += letter
            in_brackets = False
            continue

    #print(replace_line)
    fixed.write(replace_line)
   # print(replace_line)

