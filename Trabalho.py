entrada = "GLUD.txt"
saida = "AFN.txt"

afn = {
    "Q": set(),
    "Sigma": set(),
    "delta": {},  
    "q0": "",
    "F": set()
}

with open(entrada, "r") as arquivo:
    linhas = [linha.strip() for linha in arquivo if "->" in linha]

for linha in linhas:
    esquerda, direita = linha.split("->")
    origem = esquerda.strip()
    producoes = direita.strip()

    if afn["q0"] == "":
        afn["q0"] = origem

    afn["Q"].add(origem)

    if producoes == 'e':
        estado_final = "qF"
        afn["Q"].add(estado_final)
        afn["F"].add(estado_final)
        afn["delta"].setdefault((origem, 'e'), set()).add(estado_final)
    elif len(producoes) == 2:
        simbolo = producoes[0]
        destino = producoes[1]
        afn["Sigma"].add(simbolo)
        afn["Q"].add(destino)
        afn["delta"].setdefault((origem, simbolo), set()).add(destino)
    elif len(producoes) == 1:
        simbolo = producoes
        estado_final = "qF"
        afn["Q"].add(estado_final)
        afn["F"].add(estado_final)
        afn["Sigma"].add(simbolo)
        afn["delta"].setdefault((origem, simbolo), set()).add(estado_final)

with open(saida, "w") as f:
    f.write("#AFN Original\n")
    f.write("Q: " + ", ".join(sorted(afn["Q"])) + "\n")
    f.write("Sigma: " + ", ".join(sorted(afn["Sigma"])) + "\n")
    f.write("q0: " + afn["q0"] + "\n")
    f.write("delta:\n")
    for (estado, simbolo), destinos in afn["delta"].items():
        for destino in destinos:
            f.write(f"  ({estado}, {simbolo}) -> {destino}\n")
    f.write("F: " + ", ".join(sorted(afn["F"])) + "\n")       