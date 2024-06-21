import os
import tqdm
import re
from PIL import Image
from torchvision import transforms
import pandas as pd
from joblib import Parallel, delayed
import numpy as np
import traceback


def text_filter_chinese(text):
    try:
        text = text.decode('utf-8').lower()
    except:
        text = text.encode('utf-8').decode('utf-8').lower()
    text = re.sub(u"\u2019|\u2018", "\'", text)
    text = re.sub(u"\u201c|\u201d", "\"", text)
    text = re.sub(r"http[s]?:[^\ ]+", " ", text)
    text = re.sub(r"&gt;", " ", text)
    text = re.sub(r"&lt;", " ", text)
    text = re.sub(r"&quot;", " ", text)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"\"", " ", text)
    text = re.sub(r"#\ ", "#", text)
    text = re.sub(r"\\n", " ", text)
    text = re.sub(r"\\", " ", text)
    text = re.sub(r"[\(\)\[\]\{\}]", r" ", text)
    text = re.sub(r"#", " #", text)
    text = re.sub(r"\@", " \@", text)
    text = re.sub(r"[\!\?\.\,\+\-\$\%\^\>\<\=\:\;\*\(\)\{\}\[\]\/\~\&\'\|]", " ", text)

    return text


def text_filter_english(text):
    try:
        text = text.decode('utf-8').lower()
    except:
        text = text.encode('utf-8').decode('utf-8').lower()
    text = re.sub(u"\u2019|\u2018", "\'", text)
    text = re.sub(u"\u201c|\u201d", "\"", text)
    text = re.sub(u"[\u2000-\u206F]", " ", text)
    text = re.sub(u"[\u20A0-\u20CF]", " ", text)
    text = re.sub(u"[\u2100-\u214F]", " ", text)
    text = re.sub(r"http:\ ", "http:", text)
    text = re.sub(r"http[s]?:[^\ ]+", " ", text)
    text = re.sub(r"&gt;", " ", text)
    text = re.sub(r"&lt;", " ", text)
    text = re.sub(r"&quot;", " ", text)
    text = re.sub(r"\"", " ", text)
    text = re.sub(r"#\ ", "#", text)
    text = re.sub(r"\\n", " ", text)
    text = re.sub(r"\\", " ", text)
    text = re.sub(r"[\(\)\[\]\{\}]", r" ", text)
    text = re.sub(u'['
                  u'\U0001F300-\U0001F64F'
                  u'\U0001F680-\U0001F6FF'
                  u'\u2600-\u26FF\u2700-\u27BF]+',
                  r" ", text)
    text = re.sub(r"\'s", " is ", text)
    text = re.sub(r"\'ve", " have ", text)
    text = re.sub(r"\'re", " are ", text)
    text = re.sub(r"\'d", " had ", text)
    text = re.sub(r"\'ll", " will ", text)
    text = re.sub(r"\'m", " am", text)
    text = re.sub(r"n\'t", " not", text)
    text = re.sub(r"#", " #", text)
    text = re.sub(r"\@", " \@", text)
    text = re.sub(r"[\!\?\.\,\+\-\$\%\^\>\<\=\:\;\*\(\)\{\}\[\]\/\~\&\'\|]", " ", text)

    return text


def picture_filter(im_path):
    im = Image.open(im_path, 'r').convert('RGB')
    trans = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    im = trans(im)  # type is tensor

    return im


def get_weibo_matrix(data_type):
    if data_type not in ['train', 'test']:
        raise ValueError('ERROR! data type must be train or test.')
    # corpus_dir = '/media/hibird/data/code_for_github/weibo_dataset'
    #################################################################
    corpus_dir = '../weibo_dataset'
    rumor_content = open('{}/tweets/{}_rumor.txt'.format(corpus_dir, data_type), 'r').readlines()
    nonrumor_content = open('{}/tweets/{}_nonrumor.txt'.format(corpus_dir, data_type), 'r').readlines()
    rumor_images = os.listdir('{}/rumor_images/'.format(corpus_dir))
    nonrumor_images = os.listdir('{}/nonrumor_images/'.format(corpus_dir))

    text_lists = []  # [train_number]
    image_lists = []  # [train_num]
    labels = []  # [train_num, 2]
    text_image_ids = []  # tweet_id|img_id

    n_lines = len(rumor_content)
    for idx in tqdm.tqdm(range(2, n_lines, 3)):
        tweet_id = rumor_content[idx-2].split('|')[0]
        one_rumor = rumor_content[idx].strip()
        one_rumor = text_filter_chinese(one_rumor)
        if one_rumor:
            images = rumor_content[idx-1].split('|')
            for image in images:
                img = image.split('/')[-1]
                if img in rumor_images:
                    image_lists.append(picture_filter('{}/rumor_images/{}'.format(corpus_dir, img)))
                    labels.append([0, 1])
                    text_lists.append(one_rumor)
                    text_image_ids.append('{}|{}'.format(tweet_id, img.split('.')[0])) 
                    break

    n_lines = len(nonrumor_content)
    for idx in tqdm.tqdm(range(2, n_lines, 3)):
        tweet_id = nonrumor_content[idx-2].split('|')[0]
        one_nonrumor = nonrumor_content[idx].strip()
        one_nonrumor = text_filter_chinese(one_nonrumor)
        if one_nonrumor:
            images = nonrumor_content[idx-1].split('|')
            for image in images:
                img = image.split('/')[-1]
                if img in nonrumor_images:
                    image_lists.append(picture_filter('{}/nonrumor_images/{}'.format(corpus_dir, img)))
                    labels.append([1, 0])
                    text_lists.append(one_nonrumor)
                    text_image_ids.append('{}|{}'.format(tweet_id, img.split('.')[0]))
                    break
    assert len(text_lists) == len(image_lists) == len(labels) == len(text_image_ids)
    # print('   {} samples in {} set.'.format(len(labels), data_type))
    # print('  type of text list {}, image lists {}, labels {}, text image ids {}'.format(
    #     type(text_lists), type(image_lists), type(labels), type(text_image_ids),
    # ))
    return text_lists, image_lists, labels, text_image_ids


def get_twitter_matrix(data_type):
    text_lists = []  # [train_number]
    image_lists = []  # [train_num]
    labels = []  # [train_num, 2]
    label_dict = {'fake': [0, 1], 'real': [1, 0]}
    text_image_ids = []

    # corpus_dir = '/home/hibird/plw/corpus/image-verification-corpus-master_original/mediaeval2016'
    #########################################
    corpus_dir = '../twitter_dataset'
    if data_type == 'train':
        tweets = open('{}/devset/posts.txt'.format(corpus_dir), 'r').readlines()[1:]
        image_index = 3 # 这是找到图像索引的位置 在第4个
        image_dirs = '{}/devset/images/'.format(corpus_dir)
        image_files = list(filter(lambda x: not x.endswith('.txt'), os.listdir(image_dirs))) # 这里过滤原始数据中以txt结尾的图片
        image_name = [image_file.split('.')[0] for image_file in image_files] # 加载到数组中。
    elif data_type == 'test': 
        tweets = open('{}/testset/posts_groundtruth.txt'.format(corpus_dir), 'r').readlines()[1:]
        image_index = 4 # 找到图片的位置，第5个 从0开始计数。
        image_dirs = '{}/testset/images/'.format(corpus_dir)
        image_files = list(filter(lambda x: not x.endswith('.txt'), os.listdir(image_dirs)))
        image_name = [image_file.split('.')[0] for image_file in image_files]
    else:
        raise ValueError('data type must be train or test!')

    for lines in tqdm.tqdm(tweets):
        args = lines.strip().split('\t')
        tweet_id = args[0] # 找到 tweet_id 
        for img in args[image_index].split(','): # 取图片
            if img in image_name: # 以图片为准，对过滤后的图片数据进行处理，从而得到数据集。
                image_lists.append(picture_filter('{}/{}'.format(image_dirs, image_files[image_name.index(img)])))
                labels.append(label_dict[args[-1]]) # 加入label列表
                tweet_text = args[1]
                tweet_text = text_filter_english(tweet_text) # 过滤英文
                text_lists.append(tweet_text) # 加入文本列表中。
                text_image_ids.append('{}|{}'.format(tweet_id, img)) # 只是将两个ID拼在一起的作用是？
                break

    assert len(text_lists) == len(image_lists) == len(labels) == len(text_image_ids)
    # print('   {} samples in {} set.'.format(len(labels), data_type))
    # print('  type of text list {}, image lists {}, labels {}, event labels {}, text image ids {}'.format(
    #     type(text_lists), type(image_lists), type(labels), type(event_labels), type(text_image_ids),
    # ))
    # 输出文本列表 图像列表，标签，和文本对应的图像id
    return text_lists, image_lists, labels, text_image_ids


def get_gossipcop_matrix(data_type, is_generated):
    text_lists = []  # [train_number]
    image_lists = []  # [train_num]
    labels = []  # [train_num, 2]
    label_dict = {'fake': [0, 1], 'real': [1, 0]}
    text_image_ids = []
    img_dir = "top_img"
    corpus_dir = '../gossipcop_dataset'
    if data_type == "train":
        df = pd.read_json('{}/gossipcop_v3-1_style_based_fake_{}.json'.format(corpus_dir, data_type))
    elif data_type == 'test': 
        df = pd.read_json('{}/gossipcop_v3-1_style_based_fake_{}.json'.format(corpus_dir, data_type))
    else:
        raise ValueError('data type must be train or test!') 
    if is_generated:
        text_lists = df["generated_text"].map(lambda x: text_filter_english(x)).to_list()
    else:
        text_lists = df["origin_text"].map(lambda x: text_filter_english(x)).to_list()
    # 生成带有绝对路径的图像ID    
    image_lists_pth = df["origin_id"].map(lambda x: corpus_dir+"/" + img_dir+"/" + str(x)+"_top_img.png").tolist()
    labels  = df["generated_label"].map(lambda x: label_dict[x]).tolist()
    text_image_ids = df["origin_id"].tolist()    
    for img in tqdm.tqdm(image_lists_pth):
        image_lists.append(picture_filter(img))
    assert len(text_lists) == len(image_lists) == len(labels) == len(text_image_ids)
    
    return text_lists, image_lists, labels, text_image_ids

def dataset_filter(dataset_name, data_type):

    if dataset_name == 'weibo':
        text_lists, image_lists, labels, text_image_ids = get_weibo_matrix(data_type)

    elif dataset_name == 'twitter':
        text_lists, image_lists, labels, text_image_ids = get_twitter_matrix(data_type)

    elif dataset_name == 'gossipcop_origin':
        text_lists,image_lists,labels,text_image_ids = get_gossipcop_matrix(data_type,False)
    elif dataset_name == 'gossipcop_glm':
        text_lists,image_lists,labels,text_image_ids = get_gossipcop_matrix(data_type,True)
    else:
        raise ValueError('ERROR! Dataset must be weibo or twitter!')

    return text_lists, image_lists, labels, text_image_ids



