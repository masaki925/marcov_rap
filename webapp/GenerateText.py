# -*- coding: utf-8 -*-

"""
マルコフ連鎖を用いて適当な文章を自動生成するファイル
"""

import os.path
import sqlite3
import random
import sys

from logging import basicConfig, getLogger, DEBUG, ERROR

from PrepareChain import PrepareChain

# これはメインのファイルにのみ書く
basicConfig(level=ERROR)

# これはすべてのファイルに書く
logger = getLogger(__name__)

class GenerateText(object):
    """
    文章生成用クラス
    """

    def __init__(self):
        """
        初期化メソッド
        @param n いくつの文章を生成するか
        """
        self.req_word = ''
        self.first_prefix = ''

    def generate(self, r_text=None):
        """
        実際に生成する
        @return 生成された文章
        """
        # DBが存在しないときは例外をあげる
        if not os.path.exists(PrepareChain.DB_PATH):
            raise IOError("DBファイルが存在しません")

        # DBオープン
        con = sqlite3.connect(PrepareChain.DB_PATH)
        con.row_factory = sqlite3.Row

        # 最終的にできる文章
        generated_text = ""

        text = self._generate_sentence(con, r_text)
        generated_text += text #.replace(self.first_prefix, self.req_word)

        # DBクローズ
        con.close()

        return generated_text

    def _generate_sentence(self, con, r_text):
        """
        ランダムに一文を生成する
        @param con DBコネクション
        @return 生成された1つの文章
        """
        # 生成文章のリスト
        morphemes = []

        # はじまりを取得
        first_triplet = self._get_first_triplet(con, r_text)
        morphemes.append(first_triplet[1])
        morphemes.append(first_triplet[2])

        # 文章を紡いでいく
        while morphemes[-1] != PrepareChain.END:
            prefix1 = morphemes[-2]
            prefix2 = morphemes[-1]
            triplet = self._get_triplet(con, prefix1, prefix2)
            morphemes.append(triplet[2])

        # 連結
        result = "".join(morphemes[:-1])

        return result

    def _get_chain_from_DB(self, con, prefixes):
    # def _get_chain_from_DB(con, prefixes):
        """
        チェーンの情報をDBから取得する
        @param con DBコネクション
        @param prefixes チェーンを取得するprefixの条件 tupleかlist
        @return チェーンの情報の配列
        """
        # ベースとなるSQL
        sql = "select prefix1, prefix2, suffix, freq from chain_freqs where prefix1 = ?"

        # prefixが2つなら条件に加える
        if len(prefixes) == 2:
            sql += " and prefix2 = ?"

        # 結果
        result = []

        # DBから取得
        cursor = con.execute(sql, prefixes)
        for row in cursor:
            result.append(dict(row))

        return result

    def _get_first_triplet(self, con, r_text):
        """
        文章のはじまりの3つ組をランダムに取得する
        @param con DBコネクション
        @return 文章のはじまりの3つ組のタプル
        """
        # BEGINをprefix1としてチェーンを取得
        prefixes = (PrepareChain.BEGIN,)

        # チェーン情報を取得
        chains = self._get_chain_from_DB(con, prefixes)
        # chains = _get_chain_from_DB(con, prefixes)

        # 取得したチェーンから、確率的に1つ選ぶ
        # triplet = self._get_probable_triplet(chains)

        # 取得したチェーンから、リクエスト文を元に、関連の強い単語を含むtriplet を1つ選ぶ
        triplet = self._get_intensive_triplet(chains, r_text)
        self.first_prefix = triplet['prefix2']

        return (triplet["prefix1"], triplet["prefix2"], triplet["suffix"])

    def _get_triplet(self, con, prefix1, prefix2):
        """
        prefix1とprefix2からsuffixをランダムに取得する
        @param con DBコネクション
        @param prefix1 1つ目のprefix
        @param prefix2 2つ目のprefix
        @return 3つ組のタプル
        """
        # BEGINをprefix1としてチェーンを取得
        prefixes = (prefix1, prefix2)

        # チェーン情報を取得
        chains = self._get_chain_from_DB(con, prefixes)

        # 取得したチェーンから、確率的に1つ選ぶ
        triplet = self._get_probable_triplet(chains)

        return (triplet["prefix1"], triplet["prefix2"], triplet["suffix"])

    def _get_probable_triplet(self, chains):
        """
        チェーンの配列の中から確率的に1つを返す
        @param chains チェーンの配列
        @return 確率的に選んだ3つ組
        """
        # 確率配列
        probability = []

        # 確率に合うように、インデックスを入れる
        for (index, chain) in enumerate(chains):
            for j in range(chain["freq"]):
                probability.append(index)

        # ランダムに1つを選ぶ
        chain_index = random.choice(probability)

        return chains[chain_index]

    def _get_intensive_triplet(self, chains, r_text):
        from gensim.models import Word2Vec
        import unicodedata
        import MeCab

        model = Word2Vec.load('./data/rap_w2v.model')

        mt = MeCab.Tagger("-Ochasen")
        mt.parse("") # NOTE: to avoid unicode error see detail at: https://qiita.com/kasajei/items/0805b433f363f1dba785
        tmp_list = []
        text = unicodedata.normalize('NFKC',str(r_text))
        node = mt.parseToNode(text)
        while node:
            logger.debug('node: ')
            logger.debug(node.feature)
            logger.debug('surface: ')
            logger.debug(node.surface)
            if node.feature.startswith('名詞') or node.feature.startswith('形容詞'):
                try:
                    word = node.feature.split(',')[6]
                    if '俺' in word:
                        word = word.replace('俺', 'おまえ')
                    elif 'おまえ' in word:
                        word = word.replace('おまえ', '俺')
                    tmp_list.append(word)
                except:
                    import pdb; pdb.set_trace()
            node = node.next
        tmp_list = list(filter(None, tmp_list))

        logger.debug('tmp_list: ')
        logger.debug(tmp_list)

        if 'ん' in tmp_list: tmp_list.remove('ん')
        random.shuffle(tmp_list)

        for word in tmp_list:
            logger.debug('trynig word: {}...'.format(word))
            for c in chains:
                try:
                    if word in c['prefix2'] or word in c['suffix']:
                        self.req_word = word
                        logger.debug('{}: {}'.format(word, c))
                        return c
                except:
                    import pdb; pdb.set_trace()

        for word in tmp_list:
            logger.debug('trynig similar word: {}...'.format(word))
            try:
                sim_words = model.most_similar(positive=word, topn=20)
            except:
                continue

            for s_word in sim_words:
                logger.debug('    trynig s_word: {}...'.format(s_word))
                for c in chains:
                    try:
                        if s_word[0] in c['prefix2'] or s_word[0] in c['suffix']:
                            self.req_word = word
                            logger.debug('{}: {}: {}'.format(word, s_word, c))
                            return c
                    except:
                        import pdb; pdb.set_trace()

        logger.debug('///////////////////////////////')
        logger.debug('WARN: select first chain randomly')
        logger.debug('///////////////////////////////')
        return self._get_probable_triplet(chains)

if __name__ == '__main__':
    param = sys.argv
    if (len(param) != 2):
        print(("Usage: $ python " + param[0] + " (request text)"))
        quit()  

    logger.setLevel(DEBUG)
    generator = GenerateText()
    gen_txt = generator.generate(param[1])
    print((gen_txt)) 
