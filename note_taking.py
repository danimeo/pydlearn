import re
import pyltp


notes_filename = 'notes/notes_cllx_2020.txt'

count = 1

with open(notes_filename, 'rt', encoding='utf-8') as file_input:
    while True:
        line = file_input.readline()
        if not line:
            break
        l = re.findall(r'^[0-9]+\. ', line[:-1])
        if l and l[0] :
            number_n_content = l[0].split('. ')
            count = int(number_n_content[0]) + 1
            # content = number_n_content[1]

while True:
    note = input('请输入第' + str(count) + '条笔记：')

    with open(notes_filename, 'at', encoding='utf-8') as file_output:
        file_output.write(str(count) + '. ' + note + '\n')
    count += 1
