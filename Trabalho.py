from collections import defaultdict

entrada = "GLUD.txt"
saida = "AFN.txt"

# Mapeia os estados (símbolos não-terminais) para q0, q1, ..., qF
estado_original_para_q = {}
contador_estado = 0

linhas_relevantes = []

# Primeiro passo: ler o arquivo e registrar os estados (apenas símbolos à esquerda)
with open(entrada, "r") as arquivo:
    for linha in arquivo:
        if "->" in linha:
            linhas_relevantes.append(linha.strip())
            esquerda, direita = linha.split("->")
            origem = esquerda.strip()
            if origem not in estado_original_para_q:
                estado_original_para_q[origem] = f"q{contador_estado}"
                contador_estado += 1

# Inicializa o AFN
afn = {
    "Q": set(),
    "Sigma": set(),
    "delta": defaultdict(set),
    "q0": "",
    "F": set()
}

# Estado final único
estado_final = "qF"
afn["Q"].add(estado_final)
afn["F"].add(estado_final)

# Segundo passo: construir o AFN com base nas produções (agora com múltiplas alternativas)
for linha in linhas_relevantes:
    esquerda, direita = linha.split("->")
    origem = esquerda.strip()
    producoes = direita.strip()

    # Define o estado inicial na primeira produção
    if afn["q0"] == "":
        afn["q0"] = estado_original_para_q[origem]

    estado_origem = estado_original_para_q[origem]
    afn["Q"].add(estado_origem)

    # Se a produção tem múltiplas alternativas (separadas por '|')
    alternativas = [alt.strip() for alt in producoes.split('|')]

    for prod in alternativas:
        if prod == 'e':  # produção vazia: transição epsilon para o estado final
            afn["delta"][(estado_origem, 'e')].add(estado_final)
        elif len(prod) == 1:  # ex: 'a'
            simbolo = prod
            afn["Sigma"].add(simbolo)
            afn["delta"][(estado_origem, simbolo)].add(estado_final)
        elif len(prod) == 2:  # ex: 'aA'
            simbolo = prod[0]
            destino = prod[1]
            # mapeia o estado destino se ainda não mapeado
            if destino not in estado_original_para_q:
                estado_original_para_q[destino] = f"q{contador_estado}"
                contador_estado += 1
            estado_destino = estado_original_para_q[destino]
            afn["Sigma"].add(simbolo)
            afn["Q"].add(estado_destino)
            afn["delta"][(estado_origem, simbolo)].add(estado_destino)
        else:
            raise ValueError(f"Produção inválida: {prod}")

# Terceiro passo: salvar o AFN em arquivo
with open(saida, "w") as f:
    f.write("#AFN Original\n")
    f.write("Q: " + ", ".join(sorted(afn["Q"])) + "\n")
    f.write("Sigma: " + ", ".join(sorted(afn["Sigma"])) + "\n")
    f.write("q0: " + afn["q0"] + "\n")
    f.write("delta:\n")
    for (estado, simbolo), destinos in sorted(afn["delta"].items()):
        for destino in sorted(destinos):
            f.write(f"  ({estado}, {simbolo}) -> {destino}\n")
    f.write("F: " + ", ".join(sorted(afn["F"])) + "\n")

from collections import defaultdict, deque

# 2. Função para calcular o fecho-ε (epsilon-closure)
def fechamento_epsilon(estado, delta):
    visitados = set()
    pilha = [estado]
    while pilha:
        atual = pilha.pop()
        if atual not in visitados:
            visitados.add(atual)
            for dest in delta.get((atual, 'e'), []):
                pilha.append(dest)
    return visitados

# 3. Converte AFN → AFD usando subconjuntos
def afn_para_afd(afn):
    estado_nome = {}
    nome_estado = {}

    def nomear_estado(conjunto_estados):
        if not conjunto_estados:
            return "Dead"
        chave = frozenset(sorted(conjunto_estados))  # garante unicidade e ordenação
        if chave not in estado_nome:
            novo_nome = f"q{len(estado_nome)}"
            estado_nome[chave] = novo_nome
            nome_estado[novo_nome] = chave
        return estado_nome[chave]

    # Fecho-epsilon do estado inicial
    estado_inicial = frozenset(fechamento_epsilon(afn['q0'], afn['delta']))
    nome_inicial = nomear_estado(estado_inicial)

    from collections import deque
    fila = deque([estado_inicial])
    visitados = set()
    afd_delta = {}
    estados_afd = set()
    finais_afd = set()

    while fila:
        atual = fila.popleft()
        nome_atual = nomear_estado(atual)
        estados_afd.add(nome_atual)
        visitados.add(frozenset(atual))

        # Se algum dos estados do AFN em "atual" é final, o estado do AFD também é final
        if any(s in afn["F"] for s in atual):
            finais_afd.add(nome_atual)

        for simbolo in afn["Sigma"]:
            destino = set()
            for estado in atual:
                destinos_estado = afn["delta"].get((estado, simbolo), set())
                destino.update(destinos_estado)

            # Fecho epsilon após a transição
            def fechamento_epsilon_conjunto(estados, delta):
                resultado = set()
                for estado in estados:
                    resultado |= fechamento_epsilon(estado, delta)
                return resultado
            fecho = fechamento_epsilon_conjunto(destino, afn["delta"])
            nome_destino = nomear_estado(fecho)

            afd_delta[(nome_atual, simbolo)] = nome_destino

            if frozenset(fecho) not in visitados and nome_destino != "Dead":
                fila.append(fecho)
    if any(dest == "Dead" for dest in afd_delta.values()):
        estados_afd.add("Dead")
        for simbolo in afn["Sigma"]:
            afd_delta[("Dead", simbolo)] = "Dead"

    return {
        "Q": estados_afd,
        "Sigma": afn["Sigma"],
        "q0": nome_inicial,
        "F": finais_afd,
        "delta": afd_delta
    }

# 4. Função para salvar o AFD em um arquivo
def salvar_afd_em_arquivo(afd, caminho):
    with open(caminho, "w") as f:
        f.write("#AFD Gerado a partir de AFN com e-transições\n")
        f.write("Q: " + ", ".join(sorted(afd["Q"])) + "\n")
        f.write("Sigma: " + ", ".join(sorted(afd["Sigma"])) + "\n")
        f.write("q0: " + afd["q0"] + "\n")
        f.write("delta:\n")
        for (estado, simbolo), destino in afd["delta"].items():
            f.write(f"  ({estado}, {simbolo}) -> {destino}\n")
        f.write("F: " + ", ".join(sorted(afd["F"])) + "\n")

# 5. Executar tudo
afd = afn_para_afd(afn)
salvar_afd_em_arquivo(afd, "AFD.txt")     