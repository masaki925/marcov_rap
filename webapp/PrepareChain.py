# -*- coding: utf-8 -*-

"""
与えられた文書からマルコフ連鎖のためのチェーン（連鎖）を作成して、DBに保存するファイル
"""

import unittest

import re
import MeCab
import sqlite3
from collections import defaultdict

import sys

class PrepareChain(object):
    """
    チェーンを作成してDBに保存するクラス
    """

    BEGIN = "__BEGIN_SENTENCE__"
    END = "__END_SENTENCE__"

    DB_PATH = "chain.db"
    DB_SCHEMA_PATH = "schema.sql"

    def __init__(self, text):
        """
        初期化メソッド
        @param text チェーンを生成するための文章
        """
        if isinstance(text, str):
            text = text
        self.text = text

        # 形態素解析用タガー
        self.tagger = MeCab.Tagger('-Ochasen')

    def make_triplet_freqs(self):
        """
        形態素解析から3つ組の出現回数まで
        @return 3つ組とその出現回数の辞書 key: 3つ組（タプル） val: 出現回数
        """
        # 長い文章をセンテンス毎に分割
        sentences = self._divide(self.text)

        # 3つ組の出現回数
        triplet_freqs = defaultdict(int)

        # センテンス毎に3つ組にする
        for sentence in sentences:
            # 形態素解析
            morphemes = self._morphological_analysis(sentence)
            # 3つ組をつくる
            triplets = self._make_triplet(morphemes)
            # 出現回数を加算
            for (triplet, n) in list(triplets.items()):
                triplet_freqs[triplet] += n

        return triplet_freqs

    def _divide(self, text):
        """
        「。」や改行などで区切られた長い文章を一文ずつに分ける
        @param text 分割前の文章
        @return 一文ずつの配列
        """
        # 改行文字以外の分割文字（正規表現表記）
        delimiter = "。|．|\."

        # 全ての分割文字を改行文字に置換（splitしたときに「。」などの情報を無くさないため）
        text = re.sub(r"({0})".format(delimiter), r"\1\n", text)

        # 改行文字で分割
        sentences = text.splitlines()

        # 前後の空白文字を削除
        sentences = [sentence.strip() for sentence in sentences]

        return sentences

    def _morphological_analysis(self, sentence):
        """
        一文を形態素解析する
        @param sentence 一文
        @return 形態素で分割された配列
        """
        morphemes = []
        node = self.tagger.parseToNode(sentence)
        while node:
            if node.posid != 0:
                morpheme = node.surface
                morphemes.append(morpheme)
            node = node.next
        return morphemes

    def _make_triplet(self, morphemes):
        """
        形態素解析で分割された配列を、形態素毎に3つ組にしてその出現回数を数える
        @param morphemes 形態素配列
        @return 3つ組とその出現回数の辞書 key: 3つ組（タプル） val: 出現回数
        """
        # 3つ組をつくれない場合は終える
        if len(morphemes) < 3:
            return {}

        # 出現回数の辞書
        triplet_freqs = defaultdict(int)

        # 繰り返し
        for i in range(len(morphemes)-2):
            triplet = tuple(morphemes[i:i+3])
            triplet_freqs[triplet] += 1

        # beginを追加
        triplet = (PrepareChain.BEGIN, morphemes[0], morphemes[1])
        triplet_freqs[triplet] = 1

        # endを追加
        triplet = (morphemes[-2], morphemes[-1], PrepareChain.END)
        triplet_freqs[triplet] = 1

        return triplet_freqs

    def save(self, triplet_freqs, init=False):
        """
        3つ組毎に出現回数をDBに保存
        @param triplet_freqs 3つ組とその出現回数の辞書 key: 3つ組（タプル） val: 出現回数
        """
        # DBオープン
        con = sqlite3.connect(PrepareChain.DB_PATH)

        # 初期化から始める場合
        if init:
            # DBの初期化
            with open(PrepareChain.DB_SCHEMA_PATH, "r") as f:
                schema = f.read()
                con.executescript(schema)

            # データ整形
            datas = [(triplet[0], triplet[1], triplet[2], freq) for (triplet, freq) in list(triplet_freqs.items())]

            # データ挿入
            p_statement = "insert into chain_freqs (prefix1, prefix2, suffix, freq) values (?, ?, ?, ?)"
            con.executemany(p_statement, datas)

        # コミットしてクローズ
        con.commit()
        con.close()

    def show(self, triplet_freqs):
        """
        3つ組毎の出現回数を出力する
        @param triplet_freqs 3つ組とその出現回数の辞書 key: 3つ組（タプル） val: 出現回数
        """
        for triplet in triplet_freqs:
            print("|".join(triplet), "\t", triplet_freqs[triplet])


class TestFunctions(unittest.TestCase):
    """
    テスト用クラス
    """

    def setUp(self):
        """
        テストが実行される前に実行される
        """
        self.text = "こんにちは。　今日は、楽しい運動会です。hello world.我輩は猫である\n  名前はまだない。我輩は犬である\r\n名前は決まってるよ"
        self.chain = PrepareChain(self.text)

    def test_make_triplet_freqs(self):
        """
        全体のテスト
        """
        triplet_freqs = self.chain.make_triplet_freqs()
        answer = {("__BEGIN_SENTENCE__", "今日", "は"): 1, ("今日", "は", "、"): 1, ("は", "、", "楽しい"): 1, ("、", "楽しい", "運動会"): 1, ("楽しい", "運動会", "です"): 1, ("運動会", "です", "。"): 1, ("です", "。", "__END_SENTENCE__"): 1, ("__BEGIN_SENTENCE__", "hello", "world"): 1, ("hello", "world", "."): 1, ("world", ".", "__END_SENTENCE__"): 1, ("__BEGIN_SENTENCE__", "我輩", "は"): 2, ("我輩", "は", "猫"): 1, ("は", "猫", "で"): 1, ("猫", "で", "ある"): 1, ("で", "ある", "__END_SENTENCE__"): 2, ("__BEGIN_SENTENCE__", "名前", "は"): 2, ("名前", "は", "まだ"): 1, ("は", "まだ", "ない"): 1, ("まだ", "ない", "。"): 1, ("ない", "。", "__END_SENTENCE__"): 1, ("我輩", "は", "犬"): 1, ("は", "犬", "で"): 1, ("犬", "で", "ある"): 1, ("名前", "は", "決まっ"): 1, ("は", "決まっ", "てる"): 1, ("決まっ", "てる", "よ"): 1, ("てる", "よ", "__END_SENTENCE__"): 1}
        self.assertEqual(triplet_freqs, answer)

    def test_divide(self):
        """
        一文ずつに分割するテスト
        """
        sentences = self.chain._divide(self.text)
        answer = ["こんにちは。", "今日は、楽しい運動会です。", "hello world.", "我輩は猫である", "名前はまだない。", "我輩は犬である", "名前は決まってるよ"]
        self.assertEqual(sentences.sort(), answer.sort())

    def test_morphological_analysis(self):
        """
        形態素解析用のテスト
        """
        sentence = "今日は、楽しい運動会です。"
        morphemes = self.chain._morphological_analysis(sentence)
        answer = ["今日", "は", "、", "楽しい", "運動会", "です", "。"]
        self.assertEqual(morphemes.sort(), answer.sort())

    def test_make_triplet(self):
        """
        形態素毎に3つ組にしてその出現回数を数えるテスト
        """
        morphemes = ["今日", "は", "、", "楽しい", "運動会", "です", "。"]
        triplet_freqs = self.chain._make_triplet(morphemes)
        answer = {("__BEGIN_SENTENCE__", "今日", "は"): 1, ("今日", "は", "、"): 1, ("は", "、", "楽しい"): 1, ("、", "楽しい", "運動会"): 1, ("楽しい", "運動会", "です"): 1, ("運動会", "です", "。"): 1, ("です", "。", "__END_SENTENCE__"): 1}
        self.assertEqual(triplet_freqs, answer)

    def test_make_triplet_too_short(self):
        """
        形態素毎に3つ組にしてその出現回数を数えるテスト
        ただし、形態素が少なすぎる場合
        """
        morphemes = ["こんにちは", "。"]
        triplet_freqs = self.chain._make_triplet(morphemes)
        answer = {}
        self.assertEqual(triplet_freqs, answer)

    def test_make_triplet_3morphemes(self):
        """
        形態素毎に3つ組にしてその出現回数を数えるテスト
        ただし、形態素がちょうど3つの場合
        """
        morphemes = ["hello", "world", "."]
        triplet_freqs = self.chain._make_triplet(morphemes)
        answer = {("__BEGIN_SENTENCE__", "hello", "world"): 1, ("hello", "world", "."): 1, ("world", ".", "__END_SENTENCE__"): 1}
        self.assertEqual(triplet_freqs, answer)

    def tearDown(self):
        """
        テストが実行された後に実行される
        """
        pass


if __name__ == '__main__':
    # unittest.main()

    param = sys.argv
    if (len(param) != 2):
        print(("Usage: $ python " + param[0] + " sample.txt"))
        quit()


    f = open(param[1])
    text = f.read()
    f.close()

    # print (text)

    chain = PrepareChain(text)
    triplet_freqs = chain.make_triplet_freqs()
    chain.save(triplet_freqs, True)
