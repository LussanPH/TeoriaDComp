from collections import defaultdict, deque

entrada = "GLUD.txt"
saida = "AFN.txt"

# Mapeia os símbolos não-terminais (estados da gramática) para estados do tipo q0, q1, ..., qF
estado_original_para_q = {}
contador_estado = 0

linhas_relevantes = []

# 1. Leitura do arquivo e identificação dos estados não-terminais à esquerda das produções
with open(entrada, "r") as arquivo:
    for linha in arquivo:
        if "->" in linha:
            linhas_relevantes.append(linha.strip())
            esquerda, direita = linha.split("->")
            origem = esquerda.strip()
            if origem not in estado_original_para_q:
                estado_original_para_q[origem] = f"q{contador_estado}"
                contador_estado += 1

# Inicialização da estrutura do AFN
afn = {
    "Q": set(),                       # Conjunto de estados
    "Sigma": set(),                   # Alfabeto (símbolos terminais)
    "delta": defaultdict(set),        # Função de transição (estado, símbolo) -> conjunto de estados
    "q0": "",                         # Estado inicial
    "F": set()                        # Conjunto de estados finais
}

# Adiciona um estado final único
estado_final = "qF"
afn["Q"].add(estado_final)
afn["F"].add(estado_final)

# 2. Construção do AFN com base nas produções da gramática
for linha in linhas_relevantes:
    esquerda, direita = linha.split("->")
    origem = esquerda.strip()
    producoes = direita.strip()

    if afn["q0"] == "":  # Define o estado inicial na primeira produção
        afn["q0"] = estado_original_para_q[origem]

    estado_origem = estado_original_para_q[origem]
    afn["Q"].add(estado_origem)

    # Trata múltiplas alternativas separadas por '|'
    alternativas = [alt.strip() for alt in producoes.split('|')]

    for prod in alternativas:
        if prod == 'e':  # Transição epsilon
            afn["delta"][(estado_origem, 'e')].add(estado_final)
        elif len(prod) == 1:  # Produção do tipo 'a' (vai direto pro final)
            simbolo = prod
            afn["Sigma"].add(simbolo)
            afn["delta"][(estado_origem, simbolo)].add(estado_final)
        elif len(prod) == 2:  # Produção do tipo 'aA' (símbolo terminal + não-terminal)
            simbolo = prod[0]
            destino = prod[1]
            if destino not in estado_original_para_q:
                estado_original_para_q[destino] = f"q{contador_estado}"
                contador_estado += 1
            estado_destino = estado_original_para_q[destino]
            afn["Sigma"].add(simbolo)
            afn["Q"].add(estado_destino)
            afn["delta"][(estado_origem, simbolo)].add(estado_destino)
        else:
            raise ValueError(f"Produção inválida: {prod}")

# 3. Salva o AFN em arquivo
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

# Função para calcular o fechamento epsilon de um único estado
def fechamento_epsilon(estado, delta):
    visitados = set()
    pilha = [estado]
    while pilha:
        atual = pilha.pop()
        if atual not in visitados:
            visitados.add(atual)
            # Adiciona os destinos epsilon não visitados à pilha
            for dest in delta.get((atual, 'e'), []):
                pilha.append(dest)
    return visitados

# Converte um AFN com epsilon em um AFD (algoritmo de subconjuntos)
def afn_para_afd(afn):
    estado_nome = {}   # Mapeia conjuntos de estados AFN para nomes únicos no AFD
    nome_estado = {}   # Inverso: nome do estado -> conjunto de estados

    # Gera um nome único para o conjunto de estados
    def nomear_estado(conjunto_estados):
        if not conjunto_estados:
            return "Dead"
        chave = frozenset(sorted(conjunto_estados)) # Cria uma chave única para o conjunto de estados usando frozenset (conjunto imutável) e sorted (ordenação) Isso garante que conjuntos com os mesmos elementos, mas em ordens diferentes (ex: {'q1', 'q2'} vs {'q2', 'q1'}),sejam considerados iguais ao nomear os estados do AFD. Evita gerar estados repetidos ou ambíguos.
        if chave not in estado_nome:
            novo_nome = f"q{len(estado_nome)}"
            estado_nome[chave] = novo_nome
            nome_estado[novo_nome] = chave
        return estado_nome[chave]

    # Fecho-epsilon do estado inicial do AFN
    estado_inicial = frozenset(fechamento_epsilon(afn['q0'], afn['delta']))
    nome_inicial = nomear_estado(estado_inicial)

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

        # Marca como final se qualquer estado do conjunto é final no AFN
        if any(s in afn["F"] for s in atual):
            finais_afd.add(nome_atual)

        for simbolo in afn["Sigma"]:
            destino = set()
            # Aplica a transição pelo símbolo em cada estado do conjunto atual
            for estado in atual:
                destinos_estado = afn["delta"].get((estado, simbolo), set())
                destino.update(destinos_estado)

            # Fecho-epsilon do conjunto destino
            def fechamento_epsilon_conjunto(estados, delta):
                resultado = set()
                for estado in estados:
                    resultado |= fechamento_epsilon(estado, delta)
                return resultado

            fecho = fechamento_epsilon_conjunto(destino, afn["delta"])
            nome_destino = nomear_estado(fecho)

            afd_delta[(nome_atual, simbolo)] = nome_destino

            # Só visita novos estados não processados ainda
            if frozenset(fecho) not in visitados and nome_destino != "Dead":
                fila.append(fecho)

    # Cria o estado Dead (morto) se necessário
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

# Salva o AFD resultante em arquivo
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

# Verifica se uma cadeia é aceita pelo AFD
def verifica_afd(afd, entrada):
    estado_atual = afd["q0"]

    for simbolo in entrada:
        if simbolo not in afd["Sigma"]:
            print(f"Símbolo inválido na entrada: '{simbolo}' não está no alfabeto.")
            return False
        chave = (estado_atual, simbolo)
        if chave not in afd["delta"]:
            print(f"Transição indefinida para ({estado_atual}, {simbolo}).")
            return False
        estado_atual = afd["delta"][chave]

    if estado_atual in afd["F"]:
        print(f"A entrada '{entrada}' foi aceita. Estado final: {estado_atual}")
        return True
    else:
        print(f"A entrada '{entrada}' foi rejeitada. Estado final: {estado_atual}")
        return False

# Gera o reverso de um AFD (linguagem reversa)
def reverso_afd(afd):
    novo_afn = {
        "Q": set(afd["Q"]),
        "Sigma": set(afd["Sigma"]),
        "delta": defaultdict(set),
        "q0": "qR",            # Novo estado inicial
        "F": {afd["q0"]}       # Novo estado final será o inicial antigo
    }

    novo_afn["Q"].add("qR")

    # Inverte todas as transições
    for (origem, simbolo), destino in afd["delta"].items():
        novo_afn["delta"][(destino, simbolo)].add(origem)

    # Conecta o novo estado inicial com todos os antigos finais via epsilon
    for estado_final_antigo in afd["F"]:
        novo_afn["delta"][("qR", 'e')].add(estado_final_antigo)

    return novo_afn

# Salva um AFN (como o reverso) em arquivo
def salvar_afn_em_arquivo(afn, caminho):
    with open(caminho, "w") as f:
        f.write("#AFN Reverso (linguagem reversa do AFD original)\n")
        f.write("Q: " + ", ".join(sorted(afn["Q"])) + "\n")
        f.write("Sigma: " + ", ".join(sorted(afn["Sigma"])) + "\n")
        f.write("q0: " + afn["q0"] + "\n")
        f.write("delta:\n")
        for (estado, simbolo), destinos in sorted(afn["delta"].items()):
            for destino in sorted(destinos):
                f.write(f"  ({estado}, {simbolo}) -> {destino}\n")
        f.write("F: " + ", ".join(sorted(afn["F"])) + "\n")

# Gera o complemento de um AFD
def gerar_complemento_afd(afd):
    estados = afd["Q"]
    alfabeto = afd["Sigma"]
    delta = dict(afd["delta"])

    # Completa com transições para o estado Dead, se faltar alguma
    for estado in estados:
        for simbolo in alfabeto:
            if (estado, simbolo) not in delta:
                delta[(estado, simbolo)] = "Dead"

    # Completa transições do estado Dead
    if any(dest == "Dead" for dest in delta.values()):
        estados.add("Dead")
        for simbolo in alfabeto:
            delta[("Dead", simbolo)] = "Dead"

    # O complemento inverte os estados finais
    novos_finais = estados - afd["F"]

    return {
        "Q": estados,
        "Sigma": alfabeto,
        "q0": afd["q0"],
        "F": novos_finais,
        "delta": delta
    }

# Salva o AFD complementar em arquivo
def salvar_complemento_em_arquivo(afd_comp, caminho="COMP.txt"):
    with open(caminho, "w") as f:
        f.write("#AFD Complementar\n")
        f.write("Q: " + ", ".join(sorted(afd_comp["Q"])) + "\n")
        f.write("Sigma: " + ", ".join(sorted(afd_comp["Sigma"])) + "\n")
        f.write("q0: " + afd_comp["q0"] + "\n")
        f.write("delta:\n")
        for (estado, simbolo), destino in afd_comp["delta"].items():
            f.write(f"  ({estado}, {simbolo}) -> {destino}\n")
        f.write("F: " + ", ".join(sorted(afd_comp["F"])) + "\n")

# Execução final de todas as etapas
#obs: a construção do afn não está dentro de uma função  
afd = afn_para_afd(afn)
salvar_afd_em_arquivo(afd, "AFD.txt")
reverso = reverso_afd(afd)
salvar_afn_em_arquivo(reverso, "REV.txt")
afd_complementar = gerar_complemento_afd(afd)
salvar_complemento_em_arquivo(afd_complementar, "COMP.txt")

# Verificação de cadeia
entrada_usuario = input("Digite a cadeia de entrada: ").strip()
verifica_afd(afd, entrada_usuario)
