import codecs
import pvextract

from github_codes.keyword_extraction_master import keyextract_tfidf

parser = pvextract.Parser().load()

data = {'id': ['1', '2'], 'title': ['尺寸标注经验', '力矩'],
        'abstract': ['直接用轮廓线、轴线或对称中心线作为尺寸界线时，如果不好在界线之间标注尺寸，则应沿尺寸线方向向外引出线，然后折出一条水平线段，在其上水平地标注尺寸数字及符号。',
                     '''力矩的定义：在力矩作用面内，力对点的矩是一个代数量，它的绝对值等于力的大小与力臂的乘积；力使物体绕矩心逆时针转向时力矩为正，顺时针则力矩为负。
公式：M0=±F·h
当力为零或力臂为零（力的作用线通过矩心）时，力对点的矩为零。

合力矩定理：一力系的合力对一点的矩应等于各分力对此点力矩的代数和''']}
parser.edit_words(['力系', '-矩应'])


def kwpv(texts: list):
    print(len(texts))
    data = {'id': [str(num) for num in range(0, len(texts))], 'title': [''] * len(texts), 'abstract': texts}
    print('data:', data)

    result = keyextract_tfidf.getKeywords_tfidf(data, [w.strip() for w in codecs.open('data/stopWord.txt', 'r',
                                                                                      encoding='utf-8').readlines()], 1)
    keywords = [str(key, encoding='utf-8') for key in result['key']]
    pvs = [item for sublist in (parser.s_parse(abstract) for abstract in data['abstract']) for item in sublist]

    # print(keywords, pvs, sep='\n')
    return len(keywords) * len(pvs)


if __name__ == '__main__':
    qoi = kwpv(['对初学者而言，数学教育最忌讳的是“莫名其妙”的给出定义、结论，当然这么做并不是在数学逻辑上有什么错误，而是对学生缺乏最基本的人性上的关怀。将这个极限强行定义为e并没有任何在数学逻辑上值得指摘的地方，无中生有般地生硬地说'])
    print('kw*pv信息量：' + '%.1f' % qoi)
