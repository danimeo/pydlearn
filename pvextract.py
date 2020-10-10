import jieba
import hanlp

lang = 'zh'  # 'zh', 'en'


class Parser:

    def __init__(self, lang='zh'):
        self.lang = lang
        self.tokenizer, self.tagger, self.syntactic_parser, self.semantic_parser = None, None, None, None
        self.customized_postags = {}

    def load(self):
        print('正在加载谓语动词识别模块……')

        self.tokenizer = hanlp.load('CTB6_CONVSEG')

        if self.lang == 'zh':
            self.tagger = hanlp.load(hanlp.pretrained.pos.CTB5_POS_RNN_FASTTEXT_ZH)
            self.syntactic_parser = hanlp.load(hanlp.pretrained.dep.CTB7_BIAFFINE_DEP_ZH)
            self.semantic_parser = hanlp.load(hanlp.pretrained.sdp.SEMEVAL16_TEXT_BIAFFINE_ZH)
        else:
            self.tagger = hanlp.load(hanlp.pretrained.pos.PTB_POS_RNN_FASTTEXT_EN)
            self.syntactic_parser = hanlp.load(hanlp.pretrained.dep.PTB_BIAFFINE_DEP_EN)
            self.semantic_parser = hanlp.load(hanlp.pretrained.sdp.SEMEVAL15_PSD_BIAFFINE_EN)

        return self

    def edit_words(self, words: list):
        def edit_word(word: str):
            if len(word) > 1:
                if word.startswith('-'):
                    jieba.del_word(word[1:])
                elif '/' in word:
                    jieba.del_word(word.replace('/', ''))
                    splits = word.split('/')
                    for spl in splits:
                        jieba.add_word(spl)
                elif word.startswith('+'):
                    jieba.add_word(word)
                else:
                    jieba.add_word(word)

        def edit_postag(word: str, postag: str):
            self.customized_postags[word] = postag

        for word in words:
            if isinstance(word, str):
                edit_word(word)
            elif isinstance(word, tuple):
                edit_word(word[0])
                edit_postag(word[0], word[1])

    def apply_customized_postags(self, tokens_n_tags):
        new_tokens_n_tags = list(tokens_n_tags)
        for index, token_n_tag in enumerate(tokens_n_tags):
            for word in self.customized_postags:
                postag = self.customized_postags[word]
                if token_n_tag[0] == word and token_n_tag[1] != postag:
                    new_tokens_n_tags[index] = (token_n_tag[0], postag)
        return new_tokens_n_tags

    def s_parse(self, text: str):
        sentences = hanlp.utils.rules.split_sentence(text)
        output = ''
        output_pvs = []
        for sentence in sentences:
            if lang == 'zh':
                tokens = jieba.lcut(sentence)
            else:
                tokens = self.tokenizer(sentence)
            tags = self.tagger(tokens)
            tokens_n_tags = self.apply_customized_postags(((token, tag) for token, tag in zip(tokens, tags)))
            print('分词及词性标注结果：' + str(tokens_n_tags))
            syn_parser = self.syntactic_parser(tokens_n_tags)
            sem_parser = self.semantic_parser(tokens_n_tags)

            words_syn = [''] * (len(syn_parser) + 1)
            words = [''] * (len(sem_parser) + 1)

            for w_syn in syn_parser:
                words_syn[w_syn['id']] = w_syn
            for w in sem_parser:
                words[w['id']] = w

            preds_counts = {}

            def plus_1_in_preds_counts(id):
                if id in preds_counts:
                    preds_counts[id] += 1
                else:
                    preds_counts[id] = 1

            for id, word in enumerate(words):
                if not word:
                    continue
                heads = word['head']
                deps = word['deprel']
                for head, dep in zip(heads, deps):
                    if dep.startswith('r'):
                        dp = dep[1:]
                    elif dep[0].isupper():
                        dp = dep
                    else:
                        dp = ''
                    if dp in ('Agt', 'Exp', 'Aft', 'Poss', 'Pat', 'Cont', 'Prod', 'Orig', 'Datv'
                              , 'Belg', 'Clas', 'Accd', 'Reas', 'Int', 'Cons', 'Mann', 'Tool'
                              , 'Malt', 'Time', 'Loc', 'Proc', 'Dir', 'Sco', 'Quan', 'Freq'
                              , 'Seq', 'Desc', 'Feat'):
                        if dep[0] == 'r':
                            plus_1_in_preds_counts(id)
                        else:
                            plus_1_in_preds_counts(head)

            pv_id_list = [d[1] for d in sorted(zip(preds_counts.values(), preds_counts.keys()), reverse=True)]

            p = pv_id_list[0]
            for pv in pv_id_list:
                dep = words_syn[pv]['deprel']
                cpos = words_syn[pv]['cpos']
                if dep == 'root' and cpos.startswith('V'):
                    p = pv
                    break
                if dep in ('cop', 'conj', 'dep', 'root'):
                    p = pv
            pv_set = {p}
            for pv in pv_id_list:
                heads = words[pv]['head']
                deps = words[pv]['deprel']
                if pv == p:
                    for head, dep in zip(heads, deps):
                        if dep.startswith('r'):
                            pv_set.add(head)
                else:
                    for head, dep in zip(heads, deps):
                        if head == pv_id_list[0] and not dep.startswith('r'):
                            pv_set.add(pv)

            verb_in_pv_set = False
            for pv in pv_set:
                if words[pv]['cpos'].startswith('V'):
                    verb_in_pv_set = True
                    break
            if verb_in_pv_set:
                new_set = set()
                for pv in pv_set:
                    if words[pv]['cpos'].startswith('V'):
                        new_set.add(pv)
                pv_set = new_set
            output += sentence + '\n[识别到谓语动词或句子中心词：' + str(
                [str(pv) + ': ' + words[pv]['form'] + ' <' + str(preds_counts[pv]) + '次>' for pv in pv_set]) + ']\n'
            output_pvs += [words[pv]['form'] for pv in pv_set]
        # return output
        return output_pvs



'''edit_words(['平面汇交力系', '-内任', '-之矩', '代数和', ('等于', 'VV')])
result1 = s_parse('平面汇交力系的合力对于平面内任一点之矩等于所有各分力对于该点之矩的代数和。')
result2 = s_parse('他死了，这对我们来说是个不幸的消息，也是个巨大的悲剧。')
result3 = s_parse('材料力学是研究材料在各种外力作用下产生的应变、应力、强度、刚度、稳定和导致各种材料破坏的极限的一门学科。')
edit_words(['折出', '-一条'])
result4 = s_parse('直接用轮廓线、轴线或对称中心线作为尺寸界线时，如果不好在界线之间标注尺寸，则应沿尺寸线方向向外引出线，然后折出一条水平线段，在其上水平地标注尺寸数字及符号。')
print(result1, result2, result3, result4, sep='\n')'''

if __name__ == '__main__':
    parser = Parser().load()

    while True:
        print('请输入要分析的句子：')
        s = input()

        if s.startswith('+') or s.startswith('-'):
            parser.edit_words(s)
            print('已编辑词：' + s)
        else:
            result = parser.s_parse(s)
            print(result)

        print()
