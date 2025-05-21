with open("GLUD.txt", "r") as glud:
    texto = glud.readlines()
    for i in range(len(texto)):
        texto[i] = texto[i].replace("\n", ' ').replace(" ", '')
        print(texto[i])
    texto.remove("")
    print(texto)


   