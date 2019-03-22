import json, datalist, enum, requests, time

# datalist.py is a linked list data class structure I use to build my cache.

def time_func(func, *args, **kwargs):
    start = time.time()
    result = func(*args, **kwargs)
    duration = time.time() - start
    return result, duration

class DictionaryEntry:
    def __init__(self, word, part_of_speech, definition, example=None):
        self.word = word
        self.part_of_speech = part_of_speech
        self.definition = definition
        self.example = example

    def __str__(self):
        return "\n".join([
            "Word              :{0}",
            "Part of Speech    :{1}",
            "Definition        :{2}",
            "Example           :{3}"
        ]).format(self.word, self.part_of_speech, self.definition, self.example)

class LocalDictionary:
    def __init__(self, dictionary_json_name="dictionary.json"):
        self.dict_list = []
        with open(dictionary_json_name) as file:
            pure_json = json.load(file)
            for entry in pure_json["entries"]:
                self.dict_list.append(
                    DictionaryEntry(entry["word"], entry["partOfSpeech"], entry["definition"], entry.get("example", None)))

    def search(self, word):
        for entry in self.dict_list:
            if entry.word == word:
                return entry
        raise KeyError("Word not found in local dictionary.")

class OxfordDictionary:
    # TODO Enter your APP_ID and APP_KEY from Oxford Dictionary Developer Account here: https://developer.oxforddictionaries.com/
    APP_ID = ""
    APP_KEY = ""
    SOURCE_LANG = "en"

    def search(self, word):
        word_id = word.lower()

        url = f'https://od-api.oxforddictionaries.com:443/api/v1/entries/{OxfordDictionary.SOURCE_LANG}/{word_id}'

        try:
            r = requests.get(url, headers={'app_id': self.APP_ID, 'app_key': self.APP_KEY})
            r.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise KeyError(e.__str__())
        except requests.exceptions.Timeout as e:
            raise KeyError(e.__str__())
        except requests.exceptions.TooManyRedirects as e:
            raise KeyError(e.__str__())
        except requests.exceptions.RequestException as e:
            raise KeyError(e.__str__())

        response = r.json()
        definition = \
        response["results"][0]["lexicalEntries"][0]["entries"][0]["senses"][0][
            "definitions"][0]
        part_of_speech = response["results"][0]["lexicalEntries"][0][
            "lexicalCategory"]
        example = \
        response["results"][0]["lexicalEntries"][0]["entries"][0]["senses"][0][
            "examples"][0]["text"] if "examples" in ["senses"] else None

        return DictionaryEntry(word, part_of_speech, definition, example)

class DictionaryEntryCache(datalist.DataList):
    def __init__(self, capacity=10):
        super().__init__()
        if capacity < 1:
            raise ValueError("Capacity must be at least 1!")
        self.capacity = capacity
        self.counter = 0

    def add(self, entry):
        if not isinstance(entry, DictionaryEntry):
            raise TypeError("Entry is not of type DictionaryEntry!")
        cur = self.head
        while cur.next:
            cur = cur.next
        cur.next = datalist.DataNode(entry)
        self.counter += 1
        if self.counter > self.capacity:
            new_head = self.head
            self.head = new_head.next
            self.counter = self.capacity

    def search(self, word):
        cur = self.head
        while cur.next:
            if cur.next.data.word == word:
                return cur.next.data
            cur = cur.next
        raise KeyError("Key not found in DictionaryEntryCache!")


class DictionarySource(enum.Enum):
    LOCAL = 1
    CACHE = 2
    OXFORD_ONLINE = 3

    def __str__(self):
        return self.name


class Dictionary:
    """
    source parameter in initializer specifies where we
    should look up the word definitions. The default is OXFORD_ONLINE, but it
    can also be LOCAL, and raise a ValueError if it's neither.
    You should instantiate either a LocalDictionary object or OxfordDictionary
    object depending on source.
    """
    def __init__(self, source=DictionarySource.OXFORD_ONLINE):
        self.source = source
        if source == DictionarySource.LOCAL:
            self.localdict = LocalDictionary()
        elif source == DictionarySource.OXFORD_ONLINE:
            self.localdict = OxfordDictionary()
        else:
            raise ValueError("Source must be either LOCAL or OXFORD_ONLINE")
        self.cache = DictionaryEntryCache()

    def search(self, word):
        try:
            start = time.time()
            definition = self.cache.search(word)
            duration = time.time() - start
            return definition, DictionarySource.CACHE, duration
        except:
            definition, duration = time_func(self.localdict.search, word)
            self.cache.add(definition)
            return definition, self.source, duration

if __name__== "__main__":

    dict_inst = Dictionary()

    while True:
        try:
            query = input("Please enter a word to lookup: ")
            response = dict_inst.search(query)
            print("{}\n(Found in {} in {} seconds)".format(response[0], response[1], response[2]))
        except KeyError as error_message:
            print(error_message)
