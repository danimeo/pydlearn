import jieba.posseg as pseg
from pyltp import SentenceSplitter, Segmentor, Postagger, Parser, SementicRoleLabeller

model_dir = '../pyltp_models'

segmentor = Segmentor()  # 分词
segmentor.load(model_dir + '/cws.model')
postagger = Postagger()  # 词性标注
postagger.load(model_dir + '/pos.model')
parser = Parser()  # 依存句法分析
parser.load(model_dir + '/parser.model')


def analyze(content):
    # 分句
    texts = SentenceSplitter.split(content)
    print('\n'.join(texts))

    for text in texts:
        # 分词
        words = segmentor.segment(text)
        words_str = '\t'.join(words)
        print("[分词]")
        print(words_str)

        # 词性标注
        postags = postagger.postag(words)
        postags_str = '\t'.join(postags)
        print("[词性标注]")
        print(postags_str)

        words = []
        postags = []
        for posseg in pseg.cut(text):
            words.append(posseg.word)
            postags.append(posseg.flag)

        # 依存句法分析
        arcs = parser.parse(words, postags)
        print(list((word, postag) for word, postag in zip(words, postags)))
        print(list(arc.relation for arc in arcs))
        arcs_str = "\t".join("%s%s" % (arc.relation, '(' + words[arc.head] + '->' + word + ')') for arc, word in zip(arcs, words))
        print("[依存句法分析]")
        print(arcs_str)

        verbs = set()
        for arc in arcs:
            if arc.relation in ('SBV', 'VOB', 'IOB', 'FOB', 'DBL', 'CMP'):
            # if arc.relation == 'HED':
                print(arc.head, words[arc.head])
                verbs.add(words[arc.head])
        print('动词：' + str(verbs))


def release_model():
    # 释放模型
    segmentor.release()
    postagger.release()
    parser.release()


if __name__ == '__main__':
    text = '平面汇交力系的合力对于平面内任一点之矩等于所有各分力对于该点之矩的代数和。'

    # 开始分析
    analyze(text)
    release_model()
