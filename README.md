# Trabalho 1 — Diagnóstico de Processos em Linux

**Disciplina:** Sistemas Operacionais — Análise e Desenvolvimento de Sistemas
**Faculdade:** Serra Dourada | **Professor:** Guibson Krause
**Aluno:** Railan Alves Souza

---

## 1. Aplicação escolhida e justificativa

Foi usado um script Python próprio (`aplicacao/app.py`) com **duas threads**:

- **Thread principal:** imprime uma linha `vivo, PID=...` por segundo e dorme em `sleep(1)`.
- **Thread secundária:** executa um loop infinito de cálculo (`consome_cpu`), mantendo um núcleo ocupado.

Justificativa: é seguro (não usa processos do sistema), pode ser iniciado e encerrado à vontade, e permite observar ao mesmo tempo estados diferentes (`S` e `R`), consumo constante de CPU, multithread, preempção e o efeito dos sinais (as linhas "vivo" param e voltam).

## 2. Ambiente

- Windows com **WSL2**, distribuição **Ubuntu 26.04.1 LTS** (resolute)
- Kernel `6.18.54.1-microsoft-standard-WSL2`
- Editor: VS Code conectado ao WSL (dois terminais bash: um para a aplicação, outro para os diagnósticos)
- Evidência: `evidencias/01-pid-ppid/ambiente.txt`

## 3. Como executar

```bash
cd ~/trabalho-linux-processos
python3 aplicacao/app.py        # terminal 1 (primeiro plano)
PID=$(pgrep -f aplicacao/app.py) # terminal 2
```

Os comandos usados, na ordem do experimento, estão em `comandos/comandos-utilizados.md`.

**Nota sobre o PID:** foi feito um ensaio anterior (PID 4003). Entre as sessões o WSL foi reiniciado e o experimento oficial foi refeito do zero, em uma única execução, com o **PID 1719**. Todas as evidências deste repositório são do PID 1719.

---

## 4. Evidências e interpretação

### Item 1 — PID e PPID
Evidência: `evidencias/01-pid-ppid/ps.txt`

- **PID 1719:** identificador único do `python3 aplicacao/app.py`, atribuído pelo kernel.
- **PPID 924:** o `/bin/bash` do terminal integrado do VS Code, que criou o processo (`fork` + `exec`). O PPID do bash (924) é 781, o `ptyHost` do VS Code Server.
- STAT `Sl+`: `S` dormindo (thread principal em `sleep`), `l` multithread, `+` primeiro plano.

### Item 2 — Árvore de processos
Evidência: `evidencias/02-arvore-processos/pstree.txt`

```
systemd(1) → init-systemd(2) → SessionLeader(629) → Relay(631) → sh → ... → MainThread(781)
→ bash(924) → python3(1719) → {python3}(1720)
```

A parte inicial vem do WSL2. O trecho final mostra a hierarquia criada por `fork`: VS Code Server → bash → python3, com a thread entre chaves. O `ps -ef --forest` confirma que o pai (bash, 19:17) foi criado antes do filho (python3, 19:19).

### Item 3 — Estado
Evidências: `ps.txt`, `momento1.txt`, `momento2.txt`, `threads.txt`

O processo aparece como `S` porque `ps` e `top` mostram a **thread líder**, que passa quase todo o tempo em `sleep(1)`. Com `ps -L` vê-se que a thread 1720 está em `R` (executando/pronta). O estado de um processo multithread depende de qual thread se observa.

### Item 4 — CPU e memória
Evidências: `evidencias/03-estado-recursos/momento1.txt` e `momento2.txt`

| Campo | Momento 1 (19:24:32) | Momento 2 (19:26:04) |
|---|---|---|
| %CPU | 100,0 | 100,0 |
| TIME+ | 4:40.50 | 6:12.98 |
| RES | 10284 KB | 10284 KB |
| VIRT | 89980 KB | 89980 KB |

O TIME+ aumentou 1:32,48 em 1:32 de relógio: cerca de 100% de um núcleo, coerente com o loop infinito. A memória ficou estável (sem vazamento), coerente com um código que só soma inteiros e imprime texto. O sistema ficou ~87–91% ocioso porque um núcleo é pouco no total.

### Item 5 — Prioridade e nice
Evidências: `antes-renice.txt`, `apos-renice.txt`, `renice-thread1720.txt`, `sinais.txt`

| | Antes | Depois |
|---|---|---|
| NI (thread 1719) | 0 | 10 |
| PRI (ps) | 19 | 9 |
| STAT | `Sl+` | `SNl+` |

Aumentar o nice **reduz** a prioridade (o PRI do `ps` caiu). O `N` no STAT indica nice positivo. Observou-se que `renice 10 -p 1719` alterou **apenas a thread 1719**: a 1720 continuou com NI 0 (visto em `sinais.txt`). Depois, `renice 10 -p 1720` igualou as duas (`RNl`). No Linux o nice é atributo **por thread**.

O %CPU não mudou (≈99–100%) porque a máquina estava ociosa: o nice só altera a divisão de CPU quando há **disputa** entre processos. O `ps` também mostra %CPU como média desde o início. Diminuir o nice (aumentar prioridade) exigiria root.

### Item 6 — Threads
Evidência: `evidencias/04-threads/threads.txt`

| LWP | STAT | %CPU | Papel |
|---|---|---|---|
| 1719 | `Sl+` | 0,0 | Thread principal (imprime e dorme) |
| 1720 | `Rl+` | 99,9 | Thread de cálculo |

`/proc/1719/task` lista 1719 e 1720 e `Threads: 2` confirma. **Processo x thread:** o processo é a unidade de alocação de recursos (espaço de endereçamento, descritores, PID); as threads são fluxos de execução dentro dele, que compartilham memória e arquivos abertos, mas têm identificador (LWP), pilha, registradores e estado de escalonamento próprios. O kernel escalona cada thread individualmente, por isso uma está em `S` e outra em `R`.

### Item 7 — /proc/PID
Evidências: `evidencias/05-proc/`

| Fonte | Observação |
|---|---|
| `status` | `State: S`, `PPid: 924`, `Threads: 2`, `VmRSS: 10284 kB`, `TracerPid: 0` (sem depurador). Thread principal: 1820 trocas de contexto voluntárias e 1 involuntária. |
| `cmdline` | `python3 aplicacao/app.py`: como o processo foi iniciado. |
| `limits` | Pilha 8 MB, core file 0 (sem dump), máx. 30421 processos, CPU/memória ilimitados. |
| `fd` | 0, 1 e 2 apontam para `/dev/pts/6` (stdin/stdout/stderr no pseudo-terminal). O descritor 28 aponta para um log do VS Code Server, herdado do shell que iniciou o app (comportamento do ambiente). |
| `task` | Uma entrada por thread: 1719 e 1720. |
| `ctxt-thread1720` | Thread de cálculo: 2022 voluntárias e **1506 involuntárias**. A principal cede a CPU sozinha no `sleep`; a de cálculo sofre **preempção** do escalonador ao fim do quantum. |

Também foram salvos `stat.txt` (estatísticas brutas do processo, usadas por `ps` e `top`) e `maps.txt` (regiões de memória mapeadas) como fontes complementares.

### Item 8 — Sinais
Evidência: `evidencias/06-sinais/sinais.txt`

| Momento | Thread 1719 | Thread 1720 | TIME da 1720 |
|---|---|---|---|
| Antes (19:31:18) | `SNl+` | `Rl+` | 11:26 |
| Após SIGSTOP (19:31:23) | `TNl` | `Tl` | 11:26 |
| Após SIGCONT (19:31:28) | `SNl` | `Rl` | 11:31 |

- **SIGSTOP:** todas as threads foram para `T` e o TIME não aumentou. O processo continua em memória e na tabela de processos, mas sem CPU. Não pode ser capturado nem ignorado. No terminal da aplicação as linhas "vivo" pararam entre 19:31:18 e 19:31:23 e o bash exibiu `[1]+ Stopped`.
- **SIGCONT:** o processo voltou a ser escalonável (`S` e `R`) e o TIME retomou (+5 s). O `+` sumiu do STAT porque o bash passou a tratar o job como parado/em segundo plano (controle de jobs); o app continuou escrevendo no mesmo terminal.
- **SIGTERM (19:35:36):** `ps -p 1719` não retornou o processo e `ls /proc/1719` deu `No such file or directory`. O kernel liberou memória e descritores e removeu o PID. O SIGTERM pode ser tratado pela aplicação (limpeza antes de sair); o SIGSTOP não.
- **Pausar x terminar:** pausar preserva PID, memória e descritores e permite retomar; terminar encerra o processo definitivamente.

---

## 5. Conclusão do diagnóstico

O processo 1719 foi criado pelo bash do VS Code Server e tem duas threads com papéis opostos: uma dorme quase todo o tempo e outra consome ~100% de um núcleo, com memória estável (~10 MB). O `top`/`ps` mostram só o estado da thread líder (`S`), enquanto `ps -L` e `/proc` revelam a thread em `R`. As trocas de contexto involuntárias da thread de cálculo evidenciam a preempção pelo escalonador. O nice é por thread e só produz efeito perceptível sob competição por CPU, o que não ocorreu em máquina ociosa. SIGSTOP/SIGCONT mostraram pausa e retomada sem perda de estado, e o SIGTERM encerrou o processo e removeu `/proc/1719`.

**Limitações:** WSL2 acrescenta processos próprios à árvore; o nice não foi testado sob disputa de CPU; os valores de `ps` são médias desde o início do processo.