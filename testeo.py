def word_generator(path):
    word_list = []
    with open(path, "r", encoding="utf-8") as file:
        content = file.read()
    words = content.split()
    for word in words:
        word_list.append(word)
    return word_list



lista = word_generator("assets/spanish_words.txt")
print(lista)