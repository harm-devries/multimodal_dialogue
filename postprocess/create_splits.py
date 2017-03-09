import json
import random

dialogues_file = '/Users/harmdevries/Documents/multimodal_dialogue/data/guesswhat_postprocessed.jsonl'

train_file = '/Users/harmdevries/Documents/multimodal_dialogue/data/guesswhat.train.jsonl'
valid_file = '/Users/harmdevries/Documents/multimodal_dialogue/data/guesswhat.valid.jsonl'
test_file = '/Users/harmdevries/Documents/multimodal_dialogue/data/guesswhat.test.jsonl'

picture_id_to_set = {}
with open(dialogues_file) as f, \
        open(train_file, 'wb') as f_train, \
        open(valid_file, 'wb') as f_val, \
        open(test_file, 'wb') as f_test:
    for line in f:
        set = ''
        game = json.loads(line)
        if game['picture_id'] in picture_id_to_set:
            set = picture_id_to_set[game['picture_id']]
        else:
            r = random.random()
            if r < 0.7:
                set = 'train'
            elif r < 0.85:
                set = 'valid'
            else:   
                set = 'test'
            picture_id_to_set[game['picture_id']] = set

        if set == 'train':
            f_train.write(line)
        if set == 'valid':
            f_val.write(line)
        if set == 'test':
            f_test.write(line)