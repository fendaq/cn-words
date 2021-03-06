#!/usr/bin/python
# -*- coding: UTF-8 -*-

import pickle
import time
import argparse
import re
import os
import urllib
import numpy as np

parser = argparse.ArgumentParser(description='Inference the similar words')
parser.add_argument('--path', type=str, default='./vec_saved.p', help='the path of trained embeddings')
parser.add_argument('--word', type=str, default='机器学习', help='find similar word')
parser.add_argument('--add_word', type=str, default=None, help='add a new word')
parser.add_argument('--add_vocabulary', type=bool, default=False, help='add a new word')
parser.add_argument('--top_k', type=int, default=18, help='numbers of the most similar words')
args = parser.parse_args()


def get_file(path):
    if not os.path.exists(path):
        print('Downloading(~300MB)...')
        filepath, _ = urllib.urlretrieve('https://horatio-jsy-1258160473.cos.ap-beijing.myqcloud.com/vec_saved.p', filename=path)
        print('Downloded')
    with open(path, 'rb') as f:
        embed, w_dict = pickle.load(f)
    return embed, w_dict
embed, w_dict = get_file(args.path)
reverse_w_dict = dict(zip(w_dict.values(), w_dict.keys()))
assert embed.shape[0] == len(w_dict)


class Inference:
    def __init__(self, word, top_k=18):
        self.word = word
        self.top_k = top_k

    def get_similar_words(self):
        close_word = []
        index = w_dict[self.word]
        word_embed = np.reshape(embed[index, :], [1, 300])
        similarity = np.matmul(embed, np.transpose(word_embed))
        assert np.shape(similarity) == (len(w_dict), 1)
        nearst = (-similarity).argsort(axis=0)[1:self.top_k + 1]
        for k in range(self.top_k):
            close_word.append(reverse_w_dict[nearst[k, 0]])
        print('%s is close to: %s' % (self.word, '、'.join(close_word)))

    def get_similarity(self, second_word):
        index = (w_dict[self.word], w_dict[second_word])
        word_embd = np.reshape(embed[[index[0], index[1]], :], [2, 300])
        similarity = np.matmul(word_embd[1, :], np.transpose(word_embd[0, :]))/\
                     np.matmul(word_embd[0, :], np.transpose(word_embd[0, :]))
        print('Similarity is: ', float(similarity))

    def get_trends(self, second_word, method):
        close_word = []
        index = (w_dict[self.word], w_dict[second_word])

        if method == '-':
            word_embed = (np.reshape(embed[index[0], :] - embed[index[1], :], [1, 300]))/2
        else:
            word_embed = (np.reshape(embed[index[0], :] + embed[index[1], :], [1, 300]))/2

        similarity = np.matmul(embed, np.transpose(word_embed))
        assert np.shape(similarity) == (len(w_dict), 1)
        nearst = (-similarity).argsort(axis=0)[0:self.top_k ]
        for k in range(self.top_k):
            close_word.append(reverse_w_dict[nearst[k, 0]])
        print('%s %s %s is close to: %s' % (self.word, method, second_word, '、'.join(close_word)))


def add_word(expression, add_vocabulary):
    w_list = []
    num_list = []
    exp_list = re.split(r'[=*-+]', expression)
    global embed, w_dict, reverse_w_dict
    assert len(exp_list) % 2 != 0

    for i in exp_list[1:]:
        if w_dict.__contains__(i):
            index_d = w_dict[i]
            exist_word_embed = np.reshape(embed[index_d, :], [1, 300])
            w_list.append(exist_word_embed)
        elif re.search(r'\d', i):
            num_list.append(i)
        else:
            print('——————————————————————————————————————————')
            print('one or more words are not in vocabulary!')
            print('——————————————————————————————————————————')
            break
    num_list = np.array(num_list).astype(np.float32)
    assert len(w_list) == len(num_list)

    new_embed = 0
    for i in range(len(num_list)):
        new_embed += num_list[i] * w_list[i]
    w_dict[exp_list[0]] = len(w_dict)
    embed = np.vstack((embed, new_embed))
    reverse_w_dict = dict(zip(w_dict.values(), w_dict.keys()))
    Inference(exp_list[0]).get_similar_words()

    if add_vocabulary:
        with open(args.path, 'wb') as f:
            pickle.dump((embed, w_dict), f)
        print('Successfully update vocabulary: %s' % exp_list[0])


def main():
    if args.add_word:
        add_word(args.add_word, args.add_vocabulary)
    else:
        word_list = re.split(r'\-|\/|\+', args.word.rstrip())
        search_obj = re.search(r'\-|\/|\+', args.word)
        start = time.time()
        if search_obj is None:
            if w_dict.__contains__(args.word):
                Inference(args.word, args.top_k).get_similar_words()
            else: print('%s is not in vocabulary!' % args.word)
        elif w_dict.__contains__(word_list[0]) and w_dict.__contains__(word_list[-1]):
            if search_obj.group() == '/':
                Inference(word_list[0], args.top_k).get_similarity(word_list[-1])
            else:
                Inference(word_list[0], args.top_k).get_trends(word_list[-1], search_obj.group())
        else:
            print('%s or %s is not in vocabulary!'%(word_list[0], word_list[-1]))
        print('Inference time:', time.time() - start)


if __name__ == "__main__":
    main()