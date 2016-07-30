

# avg. # words per qn

from nltk.tokenize import WordPunctTokenizer
import codecs
import operator



def listtostring(alist):
    newline = ""
    for word in alist:
        newline+=word+" "
    newline = newline.strip()
    return newline


def compute_stat(fname):

    file = open(fname,"r")

    num_d = 0
    num_q = 0
    avg_words = 0
    ac = 0

    for line in file:
        line = line.strip()
        x = line.split()
        if len(x)>1:
            if line != "N / A":
                avg_words+=len(x)
                ac+=1
        if line=="":
            num_d+=1
        else:
            num_q+=1
    file.close()
    num_d+=1
    print "number of dialogues: ",num_d

    num_q/=2

    print "number of questions: ",num_q
    print "average qns per dialogue: ", num_q*1.0/num_d
    print "average words per question: ",avg_words*1.0/ac


def tokenize(fname, tfname):

    file = open(fname, "r")
    ofile = open(tfname, "w")

    wpt = WordPunctTokenizer()

    for line in file:
        line = line.strip()
        line = wpt.tokenize(line)
        ofile.write(listtostring(line)+"\n")

    file.close()
    ofile.close()


def get_vocabulary(src, vfile):

    vocab = {}

    file = open(src,"r")
    for line in file:
        line = line.strip().split()
        for word in line:
            word = word.lower()
            if word in vocab:
                vocab[word] = vocab[word] + 1
            else:
                vocab[word] = 1
    file.close()
    sorted_vocab = sorted(vocab.items(),key=operator.itemgetter(1),reverse=True)

    file = open(vfile,"w")

    for word in sorted_vocab:
        file.write(word[0]+"\t"+str(word[1])+"\n")
    file.close()


tokenize("questions.txt","t_questions.txt")
get_vocabulary("t_questions.txt", "vocab.txt")
compute_stat("t_questions.txt")
