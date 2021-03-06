import os
from subprocess import Popen, PIPE
import sys
import nltk
import env

env.assert_valid_env()


def _penn_treebank_tokenize(lang_short_code, text):
    runner_path = os.path.join(
        os.environ['JOSHUA'],
        'scripts',
        'training',
        'penn-treebank-tokenizer.perl'
    )
    options = ['-l', lang_short_code]
    p = Popen(
        [runner_path] + options,
        stdin=PIPE,
        stderr=PIPE,
        stdout=PIPE,
        env=os.environ
    )
    out, err = p.communicate(text.encode('utf8'))
    sys.stderr.write(err.encode('utf8') + '\n')
    return unicode(out.strip(), encoding='utf8').split('\n')


def _penn_treebank_detokenize(lang_short_code, text):
    runner_path = os.path.join(
        os.environ['JOSHUA'],
        'scripts',
        'training',
        'penn-treebank-detokenizer.perl'
    )
    options = ['-l', lang_short_code]
    p = Popen(
        [runner_path] + options,
        stdin=PIPE,
        stderr=PIPE,
        stdout=PIPE,
        env=os.environ
    )
    out, err = p.communicate(text.encode('utf8'))
    sys.stderr.write(err.encode('utf8') + '\n')
    return unicode(out.strip(), encoding='utf8')


def tokenize(lang_short_code, sentences):
    """
    Returns a string with tokenized parts separated by a space character
    """
    if lang_short_code not in ['en', 'es']:
        lang_short_code = 'en'

    text = '\n'.join(sentences)

    return _penn_treebank_tokenize(lang_short_code, text)


def detokenize(sentence):
    """
    Returns a string with tokenized parts separated by a space character
    """
    pass


class PreProcessor(object):
    """
    Prepares raw text for input to a Joshua Decoder:
    1. Sentence-splitting
    2. tokenization
    3. lowercasing
    4. joining sentences with '\n'
    """
    def __init__(self, lang_aliases):
        self._lang = lang_aliases
        assert lang_aliases.long_english_name != 'es'
        self._sentence_splitter = nltk.data.load(
            'tokenizers/punkt/%s.pickle' % lang_aliases.long_english_name
        ).tokenize

    def prepare(self, text):
        paragraphs = text.split('\n')
        results = []
        for paragraph in paragraphs:
            if not paragraph:
                results.append('')
                continue
            sentences = self._sentence_splitter(paragraph)
            tokenized_sentences = tokenize(self._lang.short_name, sentences)
            lc_tokenized_sentences = [
                sent.lower() for sent in tokenized_sentences
            ]
            results.extend(lc_tokenized_sentences)
        return '\n'.join(results)


def merge_lines(translation):
    """
    Join text in one sentence per line format into paragraph format.
    """
    lines = translation.split('\n')
    prev_line = ''
    result = ''

    # The connector after each line depends on the next line.
    while lines:
        next_line = lines.pop(0)
        if prev_line == '':
            if next_line == '':
                result += u'\n\n'
            else:
                result += next_line
        else:
            if next_line == '':
                result += u'\n\n'
            else:
                result = u'{0} {1}'.format(result, next_line)

        prev_line = next_line

    return result


class PostProcessor(object):
    """
    Prepares text returned by the Joshua decoder for response to client
    """
    def __init__(self, lang_aliases):
        self._lang = lang_aliases

    def prepare(self, text):
        """
        Expected format of text is one sentence per line
        """
        text = _penn_treebank_detokenize(self._lang.short_name, text)
        lines = text.split('\n')
        lines = [line.capitalize() for line in lines]
        return merge_lines('\n'.join(lines))
