# -*- coding: utf-8 -*-

"""
マルコフ連鎖を用いて適当な文章を自動生成するファイル
"""

import os.path
import sqlite3
import random
import sys

from logging import basicConfig, getLogger, DEBUG, ERROR

from gensim.models import KeyedVectors

from PrepareChain import PrepareChain
from modules.rhyme_distance_meter import RhymeDistanceMeter

# これはメインのファイルにのみ書く
# basicConfig(level=ERROR)
basicConfig(level=DEBUG)

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
        self.w2v_file_path = './data/jawiki.word_vectors.200d.bin'
        self.w2v_vectors = KeyedVectors.load_word2vec_format(self.w2v_file_path, binary=True)
        self.chara_word = '野球'
        self.rdm = RhymeDistanceMeter(self.chara_word)
        self.topn = 3
        self.killer_phrases = [
            '味噌と米ありゃ理想と言える',
            '仲間がいるよ！！！',
            'とうさん。やったんだんぜ。おれは！',
            'ばかやろう。親子の間でそんな遠慮いるかい… おまえをこのままうずもらせてたまるか… そのためには片目が… 両目だって惜しくはないわい。',
            '角膜移植か…不知火はお父さんの片目をもらって復活してきたのか。再起をかけた一打だからこそあれだけ喜んだのか。',
            '打てなくともその倍守る。あの山田まさしく20年に一人の捕手だぜ。',
            'やった太郎。よくこわがらずにやったぞ。 これだ。この勇気がサチ子を助けたんじゃ。',
            '悔しいてわいは涙するんやないで。わいがいながら負けたことがなさけのうてほえとるんじゃい。',
            '山田、おれたちはまだ人生18年だ。苦しいとか辛いなんていう柄じゃないんだな。',
            'おじさんはハゲや。そやさかいハゲも髪型のひとつなんや！気にせんと頑張らな。',
            '血は・・・血はグラウンドで流すもの',
            'これは俺達の血と汗が混じった高知の土だ',
            '泣くな武蔵、胸を張れ',
            '俺達の思い出に残る大会にしようぜ',
            'お兄ちゃん、また勝てなかったよ',
            'うぇへへ・・・おまたせしやした、山田君',
            '天才か・・・思えばそう言われたこともあったづらな・・・',
            'こめ・・・米が・・・もらえない',
            '勝たなあかんねん',
            '俺達は１０００円作るのに苦労したんだ・・・こいつを倒すまで俺は野球をやめねぇ',
            'あーばよぉー、まーたなぁー',
            'まだ裏があらーね',
            'オヤジ・・・今分かったぜ。球汚れなく道険し・・・道、けわし・・・',
            'こんなものしてるからいかんのだ！',
            '俺達はガキの頃から野球やってきたんだ。あんなニワカな奴らに負けたら全国の球児に申し訳が立たんってもんだ！',
            '俺は本当に後悔しているぜ。こんな奴だとは知らずに３年間努力したことを・・・。。。かなうはずないよな。。。',
        ]

    def __max_score(self, text_list, killer_phrase):
        max_score = -1
        max_text = None
        logger.debug(f'{killer_phrase=}')
        for text in text_list:
            score = self.rdm.throw(text, killer_phrase)
            logger.debug(f'{score=}, {text=}')
            if score > max_score:
                max_score = score
                max_text = text

        return max_text

    def generate(self, r_text=None, reverse=False):
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

        if reverse:
            killer_phrase = random.choice(self.killer_phrases)
            text_list = self._generate_sentences_reverse(con, r_text, killer_phrase)
            text = self.__max_score(text_list, killer_phrase)
            text += f"\n{killer_phrase}"
        else:
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

    def _generate_sentences_reverse(self, con, r_text, killer_phrase):
        """
        ランダムに一文を生成する
        @param con DBコネクション
        @return 生成された1つの文章
        """
        results = []
        word_candidates = self._get_word_candidates(r_text)
        exmapded_words = []
        for word in word_candidates:
            exmapded_words.append(word)
            if word in self.w2v_vectors.vocab:
                __sim_words = self.w2v_vectors.most_similar(positive=[word, self.chara_word], topn=20)
                sim_words = self.rdm.most_rhyming(killer_phrase, [sim_word[0] for sim_word in __sim_words], topn=self.topn)
                exmapded_words += sim_words

        logger.debug(f'{word_candidates=}')
        logger.debug(f'{exmapded_words=}')
        for word in exmapded_words:
            logger.debug(f'{word=}')
            # 生成文章のリスト
            morphemes = []

            # はじまりを取得
            first_triplet = self._get_first_triplet_reverse(con, word)
            if first_triplet[2] != PrepareChain.END:
                morphemes.insert(0, first_triplet[2])
            morphemes.insert(0, first_triplet[1])
            morphemes.insert(0, first_triplet[0])

            # 文章を紡いでいく
            while morphemes[0] != PrepareChain.BEGIN:
                suffix1 = morphemes[1]
                suffix2 = morphemes[0]
                triplet = self._get_triplet_reverse(con, suffix1, suffix2)
                morphemes.insert(0, triplet[0])

            # 連結
            result = "".join(morphemes[1:])
            logger.debug(f'{result=}')
            results.append(result)

        logger.debug(f'{results=}')
        return results


    def _get_chain_from_DB(self, con, prefixes):
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

    def _get_chain_from_DB_reverse(self, con, suffixes):
        """
        チェーンの情報をDBから取得する
        @param con DBコネクション
        @param suffixes チェーンを取得するsuffix の条件 tupleかlist
        @return チェーンの情報の配列
        """
        # ベースとなるSQL
        sql = "select prefix1, prefix2, suffix, freq from chain_freqs where suffix = ?"

        if len(suffixes) == 2:
            sql += " and prefix2 = ?"

        # 結果
        result = []

        # DBから取得
        cursor = con.execute(sql, suffixes)
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

    def _get_first_triplet_reverse(self, con, word):
        """
        文章のはじまりの3つ組をr_text を元に取得する
        @param con DBコネクション
        @return 文章のはじまりの3つ組のタプル
        """

        suffixes = (word,)
        chains = self._get_chain_from_DB_reverse(con, suffixes)
        if len(chains) == 0:
            suffixes = (PrepareChain.END,)
            chains = self._get_chain_from_DB_reverse(con, suffixes)

        triplet = self._get_probable_triplet(chains)

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

    def _get_triplet_reverse(self, con, suffix1, suffix2):
        """
        suffix1 とsuffix2 からprefix をランダムに取得する
        @param con DBコネクション
        @param suffix1 後ろから1つ目のsuffix
        @param suffix2 後ろから2つ目のsuffix
        @return 3つ組のタプル
        """
        # BEGINをprefix1としてチェーンを取得
        suffixes = (suffix1, suffix2)

        # チェーン情報を取得
        chains = self._get_chain_from_DB_reverse(con, suffixes)

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

    def _get_word_candidates(self, r_text):
        import unicodedata
        import MeCab

        mt = MeCab.Tagger("-Ochasen")
        mt.parse("") # NOTE: to avoid unicode error see detail at: https://qiita.com/kasajei/items/0805b433f363f1dba785
        word_candidates = []
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
                    word_candidates.append(word)
                except:
                    import pdb; pdb.set_trace()
            node = node.next
        word_candidates = list(filter(None, word_candidates))

        logger.debug('word_candidates: ')
        logger.debug(word_candidates)

        if 'ん' in word_candidates: word_candidates.remove('ん')
        random.shuffle(word_candidates)

        return word_candidates

    def _get_intensive_triplet(self, chains, r_text):
        word_candidates = self._get_word_candidates(r_text)

        for word in word_candidates:
            logger.debug('trynig word: {}...'.format(word))
            logger.debug(f'{chains=}')

            for c in chains:
                try:
                    if word in c['prefix2'] or word in c['suffix']:
                        self.req_word = word
                        logger.debug('{}: {}'.format(word, c))
                        return c
                except:
                    import pdb; pdb.set_trace()

        for word in word_candidates:
            logger.debug('trynig similar word: {}...'.format(word))
            try:
                sim_words = self.w2v_vectors.most_similar(positive=word, topn=20)
            except Exception as err:
                logger.warn(f'    {err=}')
                continue

            logger.debug(f'    {sim_words=}')
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
    gen_txt = generator.generate(param[1], reverse=True)
    print((gen_txt))
