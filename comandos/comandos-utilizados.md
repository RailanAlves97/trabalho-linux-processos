# Comandos utilizados (PID 1719, em ordem)

## 0. Preparação
```bash
pgrep -f aplicacao/app.py || echo "nenhum app rodando"
python3 aplicacao/app.py                 # terminal 1
PID=$(pgrep -f aplicacao/app.py); echo $PID   # terminal 2
```

## 1–2. Ambiente, PID/PPID e árvore
```bash
cat /etc/os-release | tee evidencias/01-pid-ppid/ambiente.txt
uname -a | tee -a evidencias/01-pid-ppid/ambiente.txt
ps -o pid,ppid,stat,pri,ni,%cpu,%mem,cmd -p $PID | tee evidencias/01-pid-ppid/ps.txt
ps -o pid,ppid,cmd -p $(ps -o ppid= -p $PID) | tee -a evidencias/01-pid-ppid/ps.txt
pstree -p -s -l $PID | tee evidencias/02-arvore-processos/pstree.txt
ps -ef --forest | grep -B3 "[a]plicacao/app.py" | tee -a evidencias/02-arvore-processos/pstree.txt
```

## 3–4. Estado, CPU e memória (dois momentos)
```bash
ps -o pid,ppid,stat,pri,ni,%cpu,%mem,rss,cmd -p $PID > evidencias/03-estado-recursos/momento1.txt
top -b -n 1 -p $PID >> evidencias/03-estado-recursos/momento1.txt
# ~1 min depois
ps -o pid,ppid,stat,pri,ni,%cpu,%mem,rss,cmd -p $PID > evidencias/03-estado-recursos/momento2.txt
top -b -n 1 -p $PID >> evidencias/03-estado-recursos/momento2.txt
```

## 6. Threads
```bash
ps -L -o pid,lwp,stat,pri,ni,%cpu,cmd -p $PID | tee evidencias/04-threads/threads.txt
ls /proc/$PID/task | tee -a evidencias/04-threads/threads.txt
grep Threads /proc/$PID/status | tee -a evidencias/04-threads/threads.txt
```

## 7. /proc/PID
```bash
cat /proc/$PID/status > evidencias/05-proc/status.txt
cat /proc/$PID/stat > evidencias/05-proc/stat.txt
tr '\0' ' ' < /proc/$PID/cmdline > evidencias/05-proc/cmdline.txt
cat /proc/$PID/limits > evidencias/05-proc/limits.txt
ls -l /proc/$PID/fd > evidencias/05-proc/fd.txt
head -20 /proc/$PID/maps > evidencias/05-proc/maps.txt
ls /proc/$PID/task >> evidencias/05-proc/task.txt
grep ctxt /proc/$PID/task/1720/status | tee evidencias/05-proc/ctxt-thread1720.txt
```

## 5. Prioridade / nice
```bash
ps -o pid,pri,ni,%cpu,stat -p $PID | tee evidencias/03-estado-recursos/antes-renice.txt
renice 10 -p $PID
ps -o pid,pri,ni,%cpu,stat -p $PID | tee evidencias/03-estado-recursos/apos-renice.txt
# depois dos sinais:
renice 10 -p 1720
ps -L -o pid,lwp,stat,ni,%cpu -p 1719 | tee evidencias/03-estado-recursos/renice-thread1720.txt
```

## 8. Sinais
```bash
S=evidencias/06-sinais/sinais.txt
{ echo "== ANTES ($(date +%T))"; ps -L -o pid,lwp,stat,ni,time,cmd -p $PID; } | tee $S
kill -STOP $PID; sleep 5
{ echo "== APOS SIGSTOP ($(date +%T))"; ps -L -o pid,lwp,stat,ni,time,cmd -p $PID; } | tee -a $S
kill -CONT $PID; sleep 5
{ echo "== APOS SIGCONT ($(date +%T))"; ps -L -o pid,lwp,stat,ni,time,cmd -p $PID; } | tee -a $S
{ echo "== ESTADO ATUAL ($(date +%T))"; ps -L -o pid,lwp,stat,ni,time,cmd -p $PID; } | tee -a $S
kill -TERM $PID; sleep 1
{ echo "== APOS SIGTERM ($(date +%T))"; ps -p $PID || echo "processo $PID encerrado"; ls /proc/$PID 2>&1 | head -1; } | tee -a $S
```

## Git
```bash
git init
git config --global user.name "Railan Alves Souza"
git branch -m main
git add . && git commit -m "Trabalho 1 - Diagnóstico de processos em Linux"
```