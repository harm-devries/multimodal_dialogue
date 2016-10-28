import random
dialogues_file = '/Users/harmdevries/Documents/multimodal_dialogue/database/guesswhat_postprocessed.jsonl'

train_file = '/Users/harmdevries/Documents/multimodal_dialogue/guesswhat.train.jsonl'
valid_file = '/Users/harmdevries/Documents/multimodal_dialogue/guesswhat.valid.jsonl'
test_file = '/Users/harmdevries/Documents/multimodal_dialogue/guesswhat.test.jsonl'

yes = 0
no = 0
na = 0
with open(dialogues_file) as f, \
		open(train_file, 'wb') as f_train, \
		open(valid_file, 'wb') as f_val, \
		open(test_file, 'wb') as f_test:
	for line in f:
		r = random.random()
		if r < 0.7:
			f_train.write(line)
		elif r < 0.85:
			f_val.write(line)
		else:
			f_test.write(line)