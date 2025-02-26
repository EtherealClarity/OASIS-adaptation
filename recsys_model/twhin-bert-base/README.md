---
language: 
  - en
  - ja
  - pt
  - es
  - ko
  - ar
  - tr
  - th
  - fr
  - id
  - ru
  - de
  - fa
  - it
  - zh
  - pl
  - hi
  - ur
  - nl
  - el
  - ms
  - ca
  - sr
  - sv
  - uk
  - he
  - fi
  - cs
  - ta
  - ne
  - vi
  - hu
  - eo
  - bn
  - mr
  - ml
  - hr
  - no
  - sw
  - sl
  - te
  - az
  - da
  - ro
  - gl
  - gu
  - ps
  - mk
  - kn
  - bg
  - lv
  - eu
  - pa
  - et
  - mn
  - sq
  - si
  - sd
  - la
  - is
  - jv
  - lt
  - ku
  - am
  - bs
  - hy
  - or
  - sk
  - uz
  - cy
  - my
  - su
  - br
  - as
  - af
  - be
  - fy
  - kk
  - ga
  - lo
  - ka
  - km
  - sa
  - mg
  - so
  - ug
  - ky
  - gd
  - yi
tags:
  - Twitter
  - Multilingual
license: "apache-2.0"
mask_token: "<mask>"
---

# TwHIN-BERT: A Socially-Enriched Pre-trained Language Model for Multilingual Tweet Representations
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-green.svg?style=flat-square)](http://makeapullrequest.com)
[![arXiv](https://img.shields.io/badge/arXiv-2203.15827-b31b1b.svg)](https://arxiv.org/abs/2209.07562)


This repo contains models, code and pointers to datasets from our paper: [TwHIN-BERT: A Socially-Enriched Pre-trained Language Model for Multilingual Tweet Representations](https://arxiv.org/abs/2209.07562).
[[PDF]](https://arxiv.org/pdf/2209.07562.pdf)
[[HuggingFace Models]](https://huggingface.co/Twitter)

### Overview
TwHIN-BERT is a new multi-lingual Tweet language model that is trained on 7 billion Tweets from over 100 distinct languages. TwHIN-BERT differs from prior pre-trained language models as it is trained with not only text-based self-supervision (e.g., MLM), but also with a social objective based on the rich social engagements within a Twitter Heterogeneous Information Network (TwHIN).

TwHIN-BERT can be used as a drop-in replacement for BERT in a variety of NLP and recommendation tasks. It not only outperforms similar models semantic understanding tasks such text classification), but also **social recommendation** tasks such as predicting user to Tweet engagement.

## 1. Pretrained Models

We initially release two pretrained TwHIN-BERT models (base and large) that are compatible wit the [HuggingFace BERT models](https://github.com/huggingface/transformers).


| Model | Size | Download Link (🤗 HuggingFace) |
| ------------- | ------------- | --------- |
| TwHIN-BERT-base   | 280M parameters | [Twitter/TwHIN-BERT-base](https://huggingface.co/Twitter/twhin-bert-base) |
| TwHIN-BERT-large  | 550M parameters | [Twitter/TwHIN-BERT-large](https://huggingface.co/Twitter/twhin-bert-large) |


To use these models in 🤗 Transformers:
```python
from transformers import AutoTokenizer, AutoModel
tokenizer = AutoTokenizer.from_pretrained('Twitter/twhin-bert-base')
model = AutoModel.from_pretrained('Twitter/twhin-bert-base')
inputs = tokenizer("I'm using TwHIN-BERT! #TwHIN-BERT #NLP", return_tensors="pt")
outputs = model(**inputs)
```



<!-- ## 2. Set up environment and data
### Environment
TBD


## 3. Fine-tune TwHIN-BERT

TBD -->


## Citation
If you use TwHIN-BERT or out datasets in your work, please cite the following:
```bib
@article{zhang2022twhin,
  title={TwHIN-BERT: A Socially-Enriched Pre-trained Language Model for Multilingual Tweet Representations},
  author={Zhang, Xinyang and Malkov, Yury and Florez, Omar and Park, Serim and McWilliams, Brian and Han, Jiawei and El-Kishky, Ahmed},
  journal={arXiv preprint arXiv:2209.07562},
  year={2022}
}
```