import os
import logging
import sentencepiece

# Some paths and parameters
text_filepath = "path/to/corpus.txt"
model_filepath = "path/to/model/"
vocab_size = 25000
control_symbols = ["[CLS]", "[SEP]", "[MASK]"]

if __name__ == "__main__":
    # Add argument parser to provide script as cli tool
    if not os.path.isfile(text_filepath):
        raise BaseException(f"Could not train sp tokenizer, due to missing text file at {text_filepath}")

    train_command = f"--input={text_filepath} " \
                    f"--model_prefix={model_filepath} " \
                    f"--vocab_size={vocab_size - len(control_symbols)} " \
                    f"--pad_id=0 --unk_id=1 --eos_id=-1 --bos_id=-1 " \
                    f"--user_defined_symbols=(,),”,-,.,–,£,€ " \
                    f"--control_symbols={','.join(control_symbols)} " \
                    f"--shuffle_input_sentence=true --input_sentence_size=10000000 " \
                    f"--character_coverage=0.99995 --model_type=unigram "

    logging.info(f"Learning SentencePiece tokenizer with following train command: {train_command}")
    sentencepiece.SentencePieceTrainer.Train(train_command)
    # Check if model was written to disc.
    assert (os.path.isfile(f"{model_filepath}.model"))
