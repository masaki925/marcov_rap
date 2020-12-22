import MeCab
tagger = MeCab.Tagger()

romanize_table = {
    "キャ" : "kya",
    "キュ" : "kyu",
    "キョ" : "kyo",
    "シャ" : "sya",
    "シュ" : "syu",
    "ショ" : "syo",
    "チャ" : "tya",
    "チュ" : "tyu",
    "チョ" : "tyo",
    "ニャ" : "nya",
    "ニュ" : "nyu",
    "ニョ" : "nyo",
    "ヒャ" : "hya",
    "ヒュ" : "hyu",
    "ヒョ" : "hyo",
    "ミャ" : "mya",
    "ミュ" : "myu",
    "ミョ" : "myo",
    "リャ" : "rya",
    "リュ" : "ryu",
    "リョ" : "ryo",
    "ギャ" : "gya",
    "ギュ" : "gyu",
    "ギョ" : "gyo",
    "ジャ" : "jya",
    "ジュ" : "jyu",
    "ジョ" : "jyo",
    "ビャ" : "bya",
    "ビュ" : "byu",
    "ビョ" : "byo",
    "ピャ" : "pya",
    "ピュ" : "pyu",
    "ピョ" : "pyo",
    "カ" : "ka",
    "キ" : "ki",
    "ク" : "ku",
    "ケ" : "ke",
    "コ" : "ko",
    "サ" : "sa",
    "シ" : "si",
    "ス" : "su",
    "セ" : "se",
    "ソ" : "so",
    "タ" : "ta",
    "チ" : "ti",
    "ツ" : "tu",
    "テ" : "te",
    "ト" : "to",
    "ナ" : "na",
    "ニ" : "ni",
    "ヌ" : "nu",
    "ネ" : "ne",
    "ノ" : "no",
    "ハ" : "ha",
    "ヒ" : "hi",
    "フ" : "ha",
    "ヘ" : "he",
    "ホ" : "ho",
    "マ" : "ma",
    "ミ" : "mi",
    "ム" : "mu",
    "メ" : "me",
    "モ" : "mo",
    "ヤ" : "ya",
    "ユ" : "yu",
    "ヨ" : "yo",
    "ラ" : "ra",
    "リ" : "ri",
    "ル" : "ru",
    "レ" : "re",
    "ロ" : "ro",
    "ワ" : "wa",
    "ヲ" : "wo",
    "ガ" : "ga",
    "ギ" : "gi",
    "グ" : "gu",
    "ゲ" : "ge",
    "ゴ" : "go",
    "ザ" : "za",
    "ジ" : "zi",
    "ズ" : "zu",
    "ゼ" : "ze",
    "ゾ" : "zo",
    "ダ" : "da",
    "ヂ" : "di",
    "ヅ" : "du",
    "デ" : "de",
    "ド" : "do",
    "バ" : "ba",
    "ビ" : "bi",
    "ブ" : "bu",
    "ベ" : "be",
    "ボ" : "bo",
    "パ" : "pa",
    "ピ" : "pi",
    "プ" : "pu",
    "ペ" : "pe",
    "ポ" : "po",
    "ア" : "a",
    "イ" : "i",
    "ウ" : "u",
    "エ" : "e",
    "オ" : "o",
    "ン" : "#",
    "ッ" : "*",
}

def romanize(term):
    for k,v in romanize_table.items():
        term = term.replace(k,v)
    return term

def romanize_sentence(sentence):
    parsed = tagger.parse(sentence) # 'PC\t名詞,固有名詞,一般,*,*,*,PC,ピーシー,ピーシー\nEOS\n'
    tokens = parsed.splitlines()    # ['PC\t名詞,固有名詞,一般,*,*,*,PC,ピーシー,ピーシー', 'EOS']
    tokens.remove('EOS')
    romaji = ""
    for x in tokens:
        katakana  = x.split('\t')[1].split(',')[-2]
        romaji += romanize(katakana)
    return romaji

def vowelize(term):
    res = ""
    for x in term:
        if x in ['a', 'i', 'u', 'e', 'o']:
            res += x 
    return res

