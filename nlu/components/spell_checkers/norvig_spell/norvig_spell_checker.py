from sparknlp.annotator import *

class NorvigSpellChecker:
    @staticmethod
    def get_default_model():
        return NorvigSweetingModel.pretrained() \
                   .setInputCols(["token"]) \
                   .setOutputCol("checked")

    @staticmethod
    def get_pretrained_model(name, language, bucket=None):
        return NorvigSweetingModel.pretrained(name,language,bucket) \
            .setInputCols(["token"]) \
            .setOutputCol("checked")

    @staticmethod
    def get_default_trainable_model():
        return NorvigSweetingApproach() \
            .setInputCols(["token"]) \
            .setOutputCol("checked") \
            .setDictionary("coca2017.txt", "[a-zA-Z]+")
