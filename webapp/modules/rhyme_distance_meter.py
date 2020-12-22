
import os, sys
from logging import getLogger

from bert_score import BERTScorer
from fugashi import GenericTagger

from .utils import romanize, romanize_sentence, vowelize

logger = getLogger(__name__)

tagger = GenericTagger()

class RhymeDistanceMeter:
    def __init__(self, chara_word):
        self.c = chara_word
        self.baseline_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/bert-base-multilingual-cased.tsv')
        self.scorer = BERTScorer(model_type='cl-tohoku/bert-base-japanese-whole-word-masking', num_layers=11, lang='ja', rescale_with_baseline=True, baseline_path=self.baseline_file_path)
        self.min_rhyme = 2

    def throw(self, s1, s2):
        rhyme_count = self.count_rhyme(s1, s2)
        sim_s, sim_c = self.score_similarity(s1, s2)
        len_rate = self.len_rate(s1, s2)
        dist = self.calc_dist(rhyme_count, sim_s, sim_c, len_rate)
        return dist

    def len_rate(self, s1, s2):
        return min(len(s1), len(s2)) / max(len(s1), len(s2))

    def count_rhyme(self, s1, s2):
        romaji1 = romanize_sentence(s1)
        romaji2 = romanize_sentence(s2)
        
        vowel1 = vowelize(romaji1)
        vowel2 = vowelize(romaji2)
        logger.debug(f'{vowel1=}')
        logger.debug(f'{vowel2=}')

        len1 = len(vowel1)
        len2 = len(vowel2)

        if len1 > len2:
            shorter = vowel2
            longer = vowel1
        else:
            shorter = vowel1
            longer = vowel2
        
        min_len = len(shorter)
        if min_len < self.min_rhyme:
            return 0
        
        n = min_len - self.min_rhyme
        for i in range(n):
            if shorter[i:] in longer:
                return min_len - i

        for i in range(1, n):
            if shorter[:-i] in longer:
                return min_len - i

        return 0

    def score_similarity(self, s1, s2):
        refs = [s1]
        hyps = [s2]

        s1_meishi = [w.surface for w in tagger(s1) if w.feature[0] == '名詞']
        s2_meishi = [w.surface for w in tagger(s2) if w.feature[0] == '名詞']
        logger.debug(f'{s1_meishi=}')
        logger.debug(f'{s2_meishi=}')

        for s in s1_meishi:
            refs.append(self.c)
            hyps.append(s)

        for s in s2_meishi:
            refs.append(self.c)
            hyps.append(s)

        logger.debug(f'{refs=}')
        logger.debug(f'{hyps=}')
        P, R, F1 = self.scorer.score(refs, hyps)
        dist_s = F1[0]

        logger.debug(f'{F1[1:]=}')
        dist_c = max(F1[1:])

        return dist_s, dist_c

    def calc_dist(self, count, sim_s, sim_c, len_rate):
        logger.debug(f'{count=}')
        logger.debug(f'{sim_s=}')
        logger.debug(f'{sim_c=}')
        logger.debug(f'{len_rate=}')
        return int(count ** ((1 - sim_s) * (sim_c * 10) * (1 + len_rate)))

    def most_rhyming(self, killer_phrase, candidates, topn=3):
        res = {}
        for c in candidates:
            res[c] = self.count_rhyme(killer_phrase, c)
        logger.debug(f'{res=}')
        sorted_res = sorted(res.items(), key=lambda item: item[1], reverse=True)

        return [w[0] for w in sorted_res[:topn]]


if __name__ == '__main__':
    meter = RhymeDistanceMeter('野球')
    if len(sys.argv) != 3:
        sys.stderr.write(f"ERROR: invalid args.\n  USAGE: {sys.argv[0]} s1 s2\n")
        sys.exit(1)
    s1, s2 = sys.argv[1], sys.argv[2]
    distance = meter.throw(s1, s2)
    logger.debug(f"rhyme distance is {distance} m.")

